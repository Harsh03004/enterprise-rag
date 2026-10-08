import unittest
from types import SimpleNamespace
from unittest.mock import patch

from app.evaluation.regression import compare_summaries
from app.schemas.chat import ChatResponse
from app.services.chunking import ENCODING, chunk_text, chunk_text_with_metadata
from app.services.rag import build_context_and_sources
from app.services.citation_verifier import (
    repair_missing_citations,
    verify_answer_grounding,
)
from app.services.document_service import (
    sanitize_filename,
    validate_upload_filename,
)
from app.services.web_extraction import validate_url


class ChatContractTests(unittest.TestCase):
    def test_chat_response_includes_conversation_id(self):
        response = ChatResponse(
            answer="Answer",
            sources=[],
            conversation_id=42,
        )

        self.assertEqual(response.conversation_id, 42)

    def test_uncited_answer_without_sources_is_unchanged(self):
        answer = "StuMeet uses MongoDB."

        self.assertEqual(repair_missing_citations(answer, []), answer)

    def test_repair_adds_citation_to_uncited_claims_in_mixed_answer(self):
        sources = [{"id": 1, "_embedding": [1.0, 0.0]}]
        answer = "First factual claim [Source 1]. Second factual claim."
        with patch("app.services.citation_verifier.generate_embeddings", return_value=[[1.0, 0.0], [1.0, 0.0]]):
            repaired = repair_missing_citations(answer, sources)
        self.assertIn("Second factual claim. [Source 1]", repaired)

    def test_punctuation_before_citation_keeps_citation_with_its_claim(self):
        sources = [{"id": 1, "_embedding": [1.0, 0.0]}]
        answer = "Supported statement. [Source 1] Another statement. [Source 1]"
        with patch("app.services.citation_verifier.generate_embeddings", return_value=[[1.0, 0.0], [1.0, 0.0]]):
            self.assertTrue(verify_answer_grounding(answer, sources))

    def test_grounding_rejects_uncited_claim_even_if_another_claim_is_cited(self):
        sources = [{"id": 1, "_embedding": [1.0, 0.0]}]
        answer = "Supported statement [Source 1]. Uncited factual statement."
        with patch("app.services.citation_verifier.generate_embeddings", return_value=[[1.0, 0.0]]):
            self.assertFalse(verify_answer_grounding(answer, sources))


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
