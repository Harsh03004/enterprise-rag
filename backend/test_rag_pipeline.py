"""Contract tests for the shared RAG pipeline used by chat and evaluation."""

import unittest
from types import SimpleNamespace
from unittest.mock import patch

from app.services import rag
from app.services.grounding import GroundingResult

SOURCE = {"id": 1, "document_id": 7, "chunk_id": 70, "filename": "doc.md", "chunk_index": 0}
CONFIG = {"query_cache_enabled": False, "retrieval_top_k": 3}


def _patch_pipeline(answer: str, grounded: bool, ranked=None):
    """Patch retrieval, generation and grounding around the real orchestration."""
    ranked = [(SimpleNamespace(id=70), 4.0)] if ranked is None else ranked
    return [
        patch.object(rag, "search_similar_chunks", return_value=["candidate"]),
        patch.object(rag, "rerank_chunks", return_value=ranked),
        patch.object(rag, "build_context_and_sources", return_value=("context", [dict(SOURCE)])),
        patch.object(rag, "generate_response", return_value=answer),
        patch.object(rag, "stream_response", side_effect=lambda *a, **k: iter([answer[:5], answer[5:]])),
        patch.object(
            rag,
            "ground_answer",
            side_effect=lambda text, _sources, question=None: GroundingResult(
                answer=text if grounded else "",
                status="verified" if grounded else "unsupported",
                cited_ids=[1] if grounded else [],
            ),
        ),
        patch.object(rag, "rewrite_query", side_effect=lambda question, conversation_history: question),
    ]


class PipelineTestCase(unittest.TestCase):
    def start(self, patches):
        for item in patches:
            item.start()
            self.addCleanup(item.stop)


class RunRagPipelineTests(PipelineTestCase):
    def test_grounded_answer_is_returned_with_verified_sources(self):
        self.start(_patch_pipeline("The answer is 42 [Source 1].", grounded=True))
        outcome = rag.run_rag_pipeline(db=None, user_id=1, question="Q?", config=CONFIG)
        self.assertEqual(outcome.status, "answered")
        self.assertEqual(outcome.answer, "The answer is 42 [Source 1].")
        self.assertEqual([source["id"] for source in outcome.verified_sources], [1])
        self.assertEqual(outcome.search_query, "Q?")
        self.assertIn("context", outcome.prompt)

    def test_low_confidence_returns_no_context_without_generation(self):
        self.start(_patch_pipeline("unused", grounded=True, ranked=[]))
        with patch.object(rag, "generate_response") as generate:
            outcome = rag.run_rag_pipeline(db=None, user_id=1, question="Q?", config=CONFIG)
        self.assertEqual(outcome.status, "no_context")
        self.assertEqual(outcome.answer, rag.NO_CONTEXT_ANSWER)
        generate.assert_not_called()

    def test_model_refusal_is_distinguished_from_grounding_failure(self):
        self.start(_patch_pipeline(rag.MODEL_REFUSAL_ANSWER, grounded=False))
        outcome = rag.run_rag_pipeline(db=None, user_id=1, question="Q?", config=CONFIG)
        self.assertEqual(outcome.status, "model_declined")
        # Refusals are shown as refusals, never with a repaired citation.
        self.assertEqual(outcome.answer, rag.MODEL_REFUSAL_ANSWER)
        self.assertEqual(outcome.verified_sources, [])

    def test_unsupported_answer_is_a_grounding_failure(self):
        self.start(_patch_pipeline("Unsupported claim [Source 1].", grounded=False))
        outcome = rag.run_rag_pipeline(db=None, user_id=1, question="Q?", config=CONFIG)
        self.assertEqual(outcome.status, "grounding_failed")
        self.assertEqual(outcome.draft_answer, "Unsupported claim [Source 1].")

    def test_precomputed_search_query_skips_rewriting(self):
        self.start(_patch_pipeline("A [Source 1].", grounded=True))
        with patch.object(rag, "rewrite_query") as rewrite:
            outcome = rag.run_rag_pipeline(
                db=None, user_id=1, question="Q?", search_query="rewritten", config=CONFIG
            )
        rewrite.assert_not_called()
        self.assertEqual(outcome.search_query, "rewritten")


class ChatEntryPointTests(PipelineTestCase):
    def setUp(self):
        conversation = SimpleNamespace(
            id=5, user_id=1, document_id=None, collection_id=None, title="t",
            created_at=SimpleNamespace(isoformat=lambda: "now"),
            updated_at=SimpleNamespace(isoformat=lambda: "now"),
        )
        self.messages = []
        self.start([
            patch.object(rag, "resolve_conversation", return_value=(conversation, None, None)),
            patch.object(rag, "extract_document_reference", return_value=None),
            patch.object(rag, "build_conversation_context", return_value=""),
            patch.object(rag, "add_message", side_effect=lambda *a, **k: self.messages.append(k)),
        ])

    def test_answer_question_persists_and_returns_verified_answer(self):
        self.start(_patch_pipeline("The answer is 42 [Source 1].", grounded=True))
        response = rag.answer_question(db=None, user_id=1, question="Q?", config=CONFIG)
        self.assertEqual(response["answer"], "The answer is 42 [Source 1].")
        self.assertEqual(response["conversation_id"], 5)
        self.assertEqual([source["id"] for source in response["sources"]], [1])
        self.assertEqual([m["role"] for m in self.messages], ["user", "assistant"])
        self.assertFalse(response["_metrics"]["fallback"])

    def test_answer_question_low_confidence_persists_fallback(self):
        self.start(_patch_pipeline("unused", grounded=True, ranked=[]))
        response = rag.answer_question(db=None, user_id=1, question="Q?", config=CONFIG)
        self.assertEqual(response["answer"], rag.NO_CONTEXT_ANSWER)
        self.assertEqual(response["sources"], [])
        self.assertEqual(self.messages[-1]["content"], rag.NO_CONTEXT_ANSWER)

    def test_stream_answer_emits_tokens_then_verified_final(self):
        self.start(_patch_pipeline("The answer is 42 [Source 1].", grounded=True))
        events = list(rag.stream_answer(db=None, user_id=1, question="Q?", config=CONFIG))
        types = [event["type"] for event in events]
        self.assertEqual(types[0], "conversation")
        self.assertIn("token", types)
        self.assertLess(types.index("verifying"), types.index("final"))
        self.assertEqual(types[-3:], ["sources", "metrics", "complete"])
        final = next(event for event in events if event["type"] == "final")
        self.assertEqual(final["content"], "The answer is 42 [Source 1].")

    def test_stream_answer_replaces_ungrounded_answer(self):
        self.start(_patch_pipeline("Unsupported claim [Source 1].", grounded=False))
        events = list(rag.stream_answer(db=None, user_id=1, question="Q?", config=CONFIG))
        final = next(event for event in events if event["type"] == "final")
        sources = next(event for event in events if event["type"] == "sources")
        self.assertEqual(final["content"], rag.GROUNDING_FALLBACK)
        self.assertEqual(sources["sources"], [])


if __name__ == "__main__":
    unittest.main()


class LlmMessageTests(unittest.TestCase):
    def test_qwen3_requests_skip_hidden_reasoning(self):
        from app.services.llm import _messages

        messages = _messages("Question?", "System.", "qwen3:4b")
        self.assertEqual(messages[0], {"role": "system", "content": "System."})
        self.assertTrue(messages[1]["content"].endswith("/no_think"))
        self.assertEqual(_messages("Question?", None, "google/gemma-4-31b-it:free"), [{"role": "user", "content": "Question?"}])


class ConfidenceGateTests(unittest.TestCase):
    def test_default_gate_refuses_clearly_unrelated_questions(self):
        from app.services.reranking import has_sufficient_confidence

        # Calibration: answerable questions scored >= -1.19, off-topic ones far lower.
        self.assertTrue(has_sufficient_confidence([("chunk", -1.19)]))
        self.assertFalse(has_sufficient_confidence([("chunk", -7.9)]))
        self.assertFalse(has_sufficient_confidence([]))
