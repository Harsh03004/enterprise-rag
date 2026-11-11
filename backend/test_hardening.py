import json
import tempfile
import unittest
from contextlib import nullcontext
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from fastapi import HTTPException
from sqlalchemy.dialects import postgresql
from sqlalchemy.exc import IntegrityError

from app.api.routes.admin import update_admin_user_status, validate_user_status_change
from app.api.routes.auth import login as authenticate
from app.api.routes.auth import register_user
from app.crud.user import get_user_by_email
from app.evaluation.regression import compare_summaries
from app.evaluation.runner import _can_compare_regression, _write_json_atomic
from app.schemas.auth import LoginRequest
from app.schemas.chat import ChatResponse
from app.schemas.user import UserCreate
from app.services.analytics import get_admin_analytics
from app.services.chunking import ENCODING, chunk_text, chunk_text_with_metadata
from app.services.document_processing import process_document
from app.services.document_service import (
    sanitize_filename,
    validate_upload_filename,
)
from app.services.llm import generate_response, stream_response
from app.services.rag import (
    _retrieval_scope_version,
    build_context_and_sources,
    verify_citations,
)
from app.services.rag_settings import DEFAULTS, save_rag_config, validate_config
from app.services.web_extraction import (
    MAX_WEB_PAGE_BYTES,
    _read_bounded_html,
    validate_url,
)
from app.tasks import _record_processing_failure


class ChatContractTests(unittest.TestCase):
    def test_registration_rejects_duplicate_username_with_conflict(self):
        request = UserCreate(email="new@example.com", username="existing", password="password")
        with (
            patch("app.api.routes.auth.get_user_by_email", return_value=None),
            patch("app.api.routes.auth.get_user_by_username", return_value=object()),
            patch("app.api.routes.auth.create_user") as create,
        ):
            with self.assertRaises(HTTPException) as raised:
                register_user(request, MagicMock())

        self.assertEqual(raised.exception.status_code, 409)
        create.assert_not_called()

    def test_registration_rolls_back_concurrent_uniqueness_conflict(self):
        request = UserCreate(email="new@example.com", username="new-user", password="password")
        db = MagicMock()
        with (
            patch("app.api.routes.auth.get_user_by_email", return_value=None),
            patch("app.api.routes.auth.get_user_by_username", return_value=None),
            patch("app.api.routes.auth.create_user", side_effect=IntegrityError("insert", {}, Exception())),
        ):
            with self.assertRaises(HTTPException) as raised:
                register_user(request, db)

        self.assertEqual(raised.exception.status_code, 409)
        db.rollback.assert_called_once()

    def test_email_lookup_normalizes_case(self):
        db = MagicMock()
        get_user_by_email(db, "User@Example.COM")
        compiled = db.scalar.call_args.args[0].compile(dialect=postgresql.dialect())
        self.assertIn("user@example.com", compiled.params.values())

    def test_inactive_account_cannot_obtain_a_login_token(self):
        inactive_user = SimpleNamespace(is_active=False, hashed_password="hashed")
        credentials = LoginRequest(email="user@example.com", password="password")
        with (
            patch("app.api.routes.auth.get_user_by_email", return_value=inactive_user),
            patch("app.api.routes.auth.verify_password") as verify_password,
        ):
            with self.assertRaises(HTTPException) as raised:
                authenticate(credentials, MagicMock())

        self.assertEqual(raised.exception.status_code, 401)
        verify_password.assert_not_called()

    def test_admin_cannot_deactivate_self(self):
        admin = SimpleNamespace(id=1, email="admin@example.com")
        with self.assertRaises(HTTPException) as raised:
            validate_user_status_change(admin, admin, False)
        self.assertEqual(raised.exception.status_code, 403)

    def test_admin_cannot_deactivate_configured_admin(self):
        admin = SimpleNamespace(id=1, email="admin@example.com")
        target = SimpleNamespace(id=2, email="protected@example.com")
        with patch("app.api.routes.admin.is_admin_email", return_value=True):
            with self.assertRaises(HTTPException) as raised:
                validate_user_status_change(admin, target, False)
        self.assertEqual(raised.exception.status_code, 403)

    def test_admin_can_activate_account(self):
        admin = SimpleNamespace(id=1, email="admin@example.com")
        target = SimpleNamespace(id=2, email="user@example.com")
        validate_user_status_change(admin, target, True)

    def test_admin_status_endpoint_persists_account_change(self):
        admin = SimpleNamespace(id=1, email="admin@example.com")
        target = SimpleNamespace(
            id=2, email="user@example.com", username="user", is_active=True,
            created_at=datetime.now(UTC),
        )
        db = MagicMock()
        db.get.return_value = target

        payload = update_admin_user_status(2, False, admin, db)

        self.assertFalse(payload["is_active"])
        self.assertTrue(payload["can_change_status"])
        db.commit.assert_called_once()
        db.refresh.assert_called_once_with(target)

    def test_admin_status_endpoint_returns_not_found_for_unknown_user(self):
        db = MagicMock()
        db.get.return_value = None

        with self.assertRaises(HTTPException) as raised:
            update_admin_user_status(99, False, SimpleNamespace(id=1, email="admin@example.com"), db)

        self.assertEqual(raised.exception.status_code, 404)

    def test_rag_settings_reject_non_string_provider_values(self):
        for key in ("provider", "fallback_provider", "embedding_model"):
            with self.subTest(key=key), self.assertRaises(ValueError):
                validate_config({**DEFAULTS, key: []})

    def test_rag_settings_reject_non_object_update(self):
        with self.assertRaisesRegex(ValueError, "JSON object"):
            save_rag_config(MagicMock(), [])

    def test_retrieval_scope_version_counts_chunks_for_cache_key(self):
        db = MagicMock()
        db.execute.return_value.one.return_value = (3, 27)

        self.assertEqual(_retrieval_scope_version(db, 4, 8, None), (3, 27))
        db.execute.assert_called_once()

    def test_llm_connection_failure_identifies_provider_configuration(self):
        client = MagicMock()
        client.chat.completions.create.side_effect = ConnectionError("Connection error")
        with patch("app.services.llm._get_client", return_value=(client, "qwen3:8b")):
            with self.assertRaisesRegex(RuntimeError, "OLLAMA_BASE_URL"):
                generate_response("question", config={"provider": "ollama"})

    def test_empty_llm_response_uses_configured_fallback(self):
        primary_client = MagicMock()
        primary_client.chat.completions.create.return_value.choices = [
            SimpleNamespace(message=SimpleNamespace(content="  "))
        ]
        fallback_client = MagicMock()
        fallback_client.chat.completions.create.return_value.choices = [
            SimpleNamespace(message=SimpleNamespace(content="Grounded answer."))
        ]
        with patch(
            "app.services.llm._get_client",
            side_effect=[(primary_client, "qwen3:8b"), (fallback_client, "gemini-test")],
        ):
            answer = generate_response(
                "question",
                config={"provider": "ollama", "fallback_provider": "gemini"},
            )

        self.assertEqual(answer, "Grounded answer.")
        fallback_client.chat.completions.create.assert_called_once()

    def test_empty_llm_response_without_fallback_is_an_error(self):
        client = MagicMock()
        client.chat.completions.create.return_value.choices = [
            SimpleNamespace(message=SimpleNamespace(content=""))
        ]
        with patch("app.services.llm._get_client", return_value=(client, "qwen3:8b")):
            with self.assertRaisesRegex(RuntimeError, "empty response"):
                generate_response("question", config={"provider": "ollama"})

    def test_empty_stream_uses_configured_fallback(self):
        primary_client = MagicMock()
        primary_client.chat.completions.create.return_value = iter([])
        fallback_client = MagicMock()
        chunk = SimpleNamespace(
            choices=[SimpleNamespace(delta=SimpleNamespace(content="Grounded answer."))]
        )
        fallback_client.chat.completions.create.return_value = iter([chunk])
        with patch(
            "app.services.llm._get_client",
            side_effect=[(primary_client, "qwen3:8b"), (fallback_client, "gemini-test")],
        ):
            answer = "".join(stream_response(
                "question",
                config={"provider": "ollama", "fallback_provider": "gemini"},
            ))

        self.assertEqual(answer, "Grounded answer.")
        fallback_client.chat.completions.create.assert_called_once()

    def test_empty_stream_without_fallback_is_an_error(self):
        client = MagicMock()
        client.chat.completions.create.return_value = iter([])
        with patch("app.services.llm._get_client", return_value=(client, "qwen3:8b")):
            with self.assertRaisesRegex(RuntimeError, "empty response"):
                list(stream_response("question", config={"provider": "ollama"}))

    def test_analytics_p95_uses_nearest_rank_percentile(self):
        db = MagicMock()
        created_at = datetime.now(UTC)
        summary_result = MagicMock()
        summary_result.one.return_value = (
            100, 5, 2, 3, 10.0, 20.0, 5.0, 50.5, 95, 300, 120, 10000, 4000, 0.75,
        )
        daily_result = MagicMock()
        daily_result.all.return_value = [(created_at.date(), 100, 5, 50.5)]
        provider_result = MagicMock()
        provider_result.all.return_value = [
            ("ollama", "qwen3:8b", 100, 5, 50.5, 10000, 4000, 0.75),
        ]
        db.execute.side_effect = [summary_result, daily_result, provider_result]

        analytics = get_admin_analytics(db, days=30)

        self.assertEqual(analytics["p95_latency_ms"], 95)
        self.assertEqual(analytics["daily"][0]["queries"], 100)
        self.assertEqual(analytics["providers"][0]["model"], "qwen3:8b")
        for call in db.execute.call_args_list:
            call.args[0].compile(dialect=postgresql.dialect())

    def test_evaluation_checkpoint_writes_complete_json_atomically(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "nested" / "results.json"
            _write_json_atomic(output, {"status": "running", "results": [1, 2]})
            self.assertEqual(json.loads(output.read_text(encoding="utf-8")), {
                "status": "running", "results": [1, 2]
            })
            self.assertEqual(list(output.parent.glob("*.tmp")), [])

    def test_evaluation_with_case_errors_is_not_regression_comparable(self):
        self.assertFalse(_can_compare_regression(
            0,
            [{"case_id": "basic-001", "error": "LLM connection failed"}],
        ))
        self.assertFalse(_can_compare_regression(
            3,
            [{"case_id": "basic-004", "error": "LLM connection failed"}],
        ))
        self.assertTrue(_can_compare_regression(16, []))

    def test_chat_response_includes_conversation_id(self):
        response = ChatResponse(
            answer="Answer",
            sources=[],
            conversation_id=42,
        )

        self.assertEqual(response.conversation_id, 42)

    def test_verify_citations_removes_redundant_trailing_sources_footer(self):
        answer = "StuMeet offers custom rooms [Source 1]. (Sources: 1, 2, 3)"
        verified_answer, verified_sources = verify_citations(
            answer,
            [{"id": 1, "filename": "guide.pdf"}, {"id": 2, "filename": "faq.pdf"}],
        )

        self.assertEqual(verified_answer, "StuMeet offers custom rooms [Source 1].")
        self.assertEqual([source["id"] for source in verified_sources], [1])

    def test_verify_citations_removes_bracketed_sources_footer(self):
        verified_answer, verified_sources = verify_citations(
            "StuMeet offers custom rooms [Source 1]. [Sources: 1, 2]",
            [{"id": 1, "filename": "guide.pdf"}],
        )

        self.assertEqual(verified_answer, "StuMeet offers custom rooms [Source 1].")
        self.assertEqual([source["id"] for source in verified_sources], [1])

    def test_context_respects_character_budget_and_keeps_rank_order(self):
        document = SimpleNamespace(id=9, filename="source.txt")
        chunks = [
            SimpleNamespace(
                id=index, chunk_index=index, page_number=None,
                section_heading=None, block_type="text", token_count=20,
                content=("content " + str(index) + " ") * 25,
                embedding=[1.0, 0.0],
            )
            for index in (2, 1, 3)
        ]
        results = [(chunk, document, 0.1) for chunk in chunks]
        context, sources = build_context_and_sources(results, max_context_chars=450)
        self.assertLessEqual(len(context), 450)
        self.assertEqual([source["chunk_id"] for source in sources], [2, 1, 3][:len(sources)])
        self.assertTrue(sources)

    def test_evaluation_regression_detects_metric_drop(self):
        failures = compare_summaries(
            current={"pass_rate": 0.70},
            baseline={"pass_rate": 0.80},
            max_regression=0.05,
        )

        self.assertEqual(len(failures), 1)

    def test_evaluation_regression_allows_small_metric_drop(self):
        failures = compare_summaries(
            current={"pass_rate": 0.76},
            baseline={"pass_rate": 0.80},
            max_regression=0.05,
        )

        self.assertEqual(failures, [])


class IngestionBoundaryTests(unittest.TestCase):
    def test_website_response_body_is_bounded(self):
        response = SimpleNamespace(
            headers={},
            encoding="utf-8",
            iter_bytes=lambda chunk_size: iter([b"<html>", b"safe</html>"]),
        )
        self.assertEqual(_read_bounded_html(response), "<html>safe</html>")

        oversized = SimpleNamespace(
            headers={},
            encoding="utf-8",
            iter_bytes=lambda chunk_size: iter([b"x" * (MAX_WEB_PAGE_BYTES + 1)]),
        )
        with self.assertRaisesRegex(ValueError, "larger than 5 MiB"):
            _read_bounded_html(oversized)

    def test_website_content_length_rejects_large_page_before_reading(self):
        response = SimpleNamespace(
            headers={"content-length": str(MAX_WEB_PAGE_BYTES + 1)},
            encoding="utf-8",
            iter_bytes=MagicMock(),
        )
        with self.assertRaisesRegex(ValueError, "larger than 5 MiB"):
            _read_bounded_html(response)
        response.iter_bytes.assert_not_called()

    def test_processing_task_failure_keeps_document_retryable(self):
        job = SimpleNamespace(attempts=1, status="processing", error=None, completed_at=None)
        document = SimpleNamespace(status="failed", processing_error="temporary error")

        retries_remaining = _record_processing_failure(
            job, document, RuntimeError("temporary error"), now=None
        )

        self.assertEqual(retries_remaining, 3)
        self.assertEqual(job.status, "retrying")
        self.assertEqual(document.status, "processing")
        self.assertIsNone(document.processing_error)

    def test_processing_task_failure_marks_document_failed_after_last_attempt(self):
        job = SimpleNamespace(attempts=4, status="processing", error=None, completed_at=None)
        document = SimpleNamespace(status="processing", processing_error=None)
        failed_at = object()

        retries_remaining = _record_processing_failure(
            job, document, RuntimeError("permanent error"), now=failed_at
        )

        self.assertEqual(retries_remaining, 0)
        self.assertEqual(job.status, "failed")
        self.assertIs(job.completed_at, failed_at)
        self.assertEqual(document.status, "failed")
        self.assertEqual(document.processing_error, "permanent error")

    def test_failed_reindex_preserves_existing_chunks_until_replacement_is_ready(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.order_by.return_value.all.return_value = []
        document = SimpleNamespace(
            id=12,
            status="processed",
            processing_error=None,
            source_url=None,
            file_path="storage/users/1/source.txt",
        )
        chunk = SimpleNamespace(
            content="staged chunk",
            page_number=None,
            section_heading=None,
            block_type="text",
            token_count=2,
        )

        with (
            patch("app.services.document_processing.get_rag_config", return_value={"chunk_size": 400, "chunk_overlap": 50}),
            patch("app.services.document_processing.materialize_uploaded_file", return_value=nullcontext("source.txt")),
            patch("app.services.document_processing.extract_text_blocks", return_value=[("source text", None)]),
            patch("app.services.document_processing.chunk_text_with_metadata", return_value=[chunk]),
            patch("app.services.document_processing.generate_embedding", side_effect=RuntimeError("model unavailable")),
        ):
            with self.assertRaisesRegex(RuntimeError, "model unavailable"):
                process_document(db, document, rebuild_chunks=True)

        db.query.return_value.filter.return_value.delete.assert_not_called()

    def test_chunking_uses_bounded_token_windows(self):
        text = "important project detail " * 250

        chunks = chunk_text(text, chunk_size=40, chunk_overlap=5)

        self.assertGreater(len(chunks), 1)
        self.assertTrue(all(len(ENCODING.encode(chunk)) <= 40 for chunk in chunks))

    def test_chunk_metadata_tracks_markdown_sections(self):
        chunks = chunk_text_with_metadata("# Introduction\n" + ("project detail " * 20))

        self.assertTrue(chunks)
        self.assertEqual(chunks[0].section_heading, "Introduction")
        self.assertEqual(chunks[0].block_type, "section")
        self.assertGreater(chunks[0].token_count or 0, 0)

    def test_chunk_metadata_preserves_page_number(self):
        chunks = chunk_text_with_metadata("page content", page_number=3)

        self.assertEqual(chunks[0].page_number, 3)

    def test_filename_is_reduced_to_a_safe_basename(self):
        self.assertEqual(
            sanitize_filename("../../reports/quarterly.pdf"),
            "quarterly.pdf",
        )

    def test_missing_filename_gets_a_safe_default(self):
        self.assertEqual(sanitize_filename(None), "uploaded-file")

    def test_upload_extension_must_be_supported_by_extractor(self):
        self.assertEqual(validate_upload_filename("report.TXT"), "report.TXT")
        with self.assertRaises(ValueError):
            validate_upload_filename("report.markdown")

    def test_private_urls_are_rejected(self):
        with self.assertRaises(ValueError):
            validate_url("http://127.0.0.1/internal")

    def test_non_http_urls_are_rejected(self):
        with self.assertRaises(ValueError):
            validate_url("file:///etc/passwd")


if __name__ == "__main__":
    unittest.main()
