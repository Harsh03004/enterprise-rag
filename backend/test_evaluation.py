"""Tests for the evaluation dataset, scoring metrics and summaries."""

import contextlib
import io
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from app.evaluation import evaluator
from app.evaluation.dataset import EvaluationCase, load_dataset
from app.evaluation.metrics import (
    chunk_relevance,
    citation_scores,
    contains_phrase,
    forbidden_hits,
    matched_facts,
    retrieval_scores,
)
from app.evaluation.regression import compare_summaries
from app.services.rag import RagOutcome

EVALUATION_DIR = Path(__file__).resolve().parent / "evaluation"


class DatasetIntegrityTests(unittest.TestCase):
    """Labels must stay valid against the committed corpus and real chunking."""

    @classmethod
    def setUpClass(cls):
        from app.services.chunking import chunk_text_with_metadata
        from app.services.rag_settings import DEFAULTS
        from app.services.text_extraction import extract_text_blocks

        cls.dataset = load_dataset(EVALUATION_DIR / "dataset.json")
        cls.chunks = {}
        for name in cls.dataset.corpus:
            # DOCX image OCR prints when Tesseract is unavailable; text still extracts.
            with contextlib.redirect_stdout(io.StringIO()):
                blocks = extract_text_blocks((EVALUATION_DIR / "corpus" / name).resolve())
            cls.chunks[name] = [
                chunk.content
                for text, page_number in blocks
                for chunk in chunk_text_with_metadata(
                    text,
                    chunk_size=int(DEFAULTS["chunk_size"]),
                    chunk_overlap=int(DEFAULTS["chunk_overlap"]),
                    page_number=page_number,
                )
            ]

    def test_dataset_covers_answerable_and_unanswerable_cases(self):
        categories = {case.category for case in self.dataset.cases}
        self.assertGreaterEqual(len(self.dataset.cases), 40)
        self.assertIn("Unanswerable", categories)
        self.assertTrue(any(case.should_fallback for case in self.dataset.cases))

    def test_every_labelled_passage_is_inside_a_real_chunk(self):
        missing = [
            (case.id, passage.quote)
            for case in self.dataset.cases
            for passage in case.relevant_passages
            if not any(passage.quote and _contains(passage.quote, chunk) for chunk in self.chunks[passage.document])
        ]
        self.assertEqual(missing, [], "Quotes must appear verbatim (ignoring case/punctuation) in one chunk.")


def _contains(quote, chunk):
    from app.evaluation.metrics import passage_in_text

    return passage_in_text(quote, chunk)


class DatasetValidationTests(unittest.TestCase):
    def test_answerable_case_requires_facts_and_passages(self):
        with self.assertRaises(ValueError):
            EvaluationCase.from_dict({"id": "x", "category": "c", "question": "q?"})
        with self.assertRaises(ValueError):
            EvaluationCase.from_dict(
                {"id": "x", "category": "c", "question": "q?", "required_facts": [["a"]]}
            )

    def test_bare_string_fact_is_one_phrasing(self):
        case = EvaluationCase.from_dict({
            "id": "x", "category": "c", "question": "q?",
            "required_facts": ["24 days"],
            "relevant_passages": [{"document": "d.md", "quote": "24 days"}],
        })
        self.assertEqual(case.required_facts, [["24 days"]])

    def test_unanswerable_case_needs_no_labels(self):
        case = EvaluationCase.from_dict({"id": "x", "category": "c", "question": "q?", "should_fallback": True})
        self.assertTrue(case.should_fallback)


class MetricTests(unittest.TestCase):
    def test_phrase_match_respects_token_boundaries(self):
        self.assertTrue(contains_phrase("You get 24 days.", "24 days"))
        self.assertFalse(contains_phrase("You get 124 days.", "24 days"))
        self.assertTrue(contains_phrase("Accuracy is +/- 0.2 C", "0.2"))
        self.assertTrue(contains_phrase("Core hours are 10:00 to 15:00", "10:00"))

    def test_citation_numbers_never_satisfy_facts(self):
        self.assertEqual(matched_facts("Plus supports more homes [Source 3].", [["3"]]), [False])
        self.assertEqual(matched_facts("Up to 3 homes [Source 1].", [["3"]]), [True])
        self.assertEqual(forbidden_hits("Answer [Source 6].", ["6"]), [])

    def test_retrieval_scores(self):
        relevance = chunk_relevance(
            [("a.md", "noise"), ("a.md", "the key fact is here"), ("b.md", "the key fact is here")],
            [("a.md", "key fact")],
        )
        self.assertEqual(relevance, [set(), {0}, set()])
        scores = retrieval_scores(relevance, passage_count=1)
        self.assertEqual(scores["passage_recall"], 1.0)
        self.assertEqual(scores["mrr"], 0.5)
        self.assertAlmostEqual(scores["precision"], 1 / 3)

    def test_citation_scores_are_undefined_without_data(self):
        self.assertEqual(citation_scores([], [1]), {"precision": None, "recall": 0.0})
        self.assertEqual(citation_scores([1, 2], [2]), {"precision": 0.5, "recall": 1.0})


class RegressionTests(unittest.TestCase):
    def test_lower_is_better_metric_regresses_when_it_rises(self):
        failures = compare_summaries(
            current={"false_refusal_rate": 0.30},
            baseline={"false_refusal_rate": 0.10},
            max_regression=0.05,
        )
        self.assertEqual(len(failures), 1)

    def test_lower_is_better_metric_may_improve(self):
        self.assertEqual(
            compare_summaries(
                current={"false_refusal_rate": 0.0},
                baseline={"false_refusal_rate": 0.2},
            ),
            [],
        )


def _ranked(filename, content, score=3.0):
    chunk = SimpleNamespace(content=content, chunk_index=0, page_number=None)
    return ((chunk, SimpleNamespace(filename=filename), 0.1), score)


class EvaluateCaseTests(unittest.TestCase):
    CASE = EvaluationCase.from_dict({
        "id": "leave", "category": "Specific", "question": "How much leave?",
        "required_facts": [["24 days"]],
        "forbidden": ["10 days"],
        "relevant_passages": [{"document": "h.md", "quote": "24 days of paid annual leave"}],
    })

    def _run(self, outcome, case=None):
        with patch.object(evaluator, "run_rag_pipeline", return_value=outcome):
            return evaluator.evaluate_case(db=None, case=case or self.CASE, user_id=1, collection_id=2)

    def test_correct_cited_answer_passes(self):
        result = self._run(RagOutcome(
            status="answered",
            answer="Employees get 24 days [Source 1].",
            search_query="q",
            ranked_results=[_ranked("h.md", "staff receive 24 days of paid annual leave")],
            context_sources=[{"id": 1, "filename": "h.md", "_content": "staff receive 24 days of paid annual leave"}],
        ))
        self.assertTrue(result.passed, result.failure_reasons)
        self.assertEqual(result.citation_precision, 1.0)
        self.assertEqual(result.mrr, 1.0)

    def test_forbidden_phrase_fails_case(self):
        result = self._run(RagOutcome(
            status="answered", answer="24 days, or 10 days [Source 1].", search_query="q",
            ranked_results=[_ranked("h.md", "24 days of paid annual leave")],
            context_sources=[{"id": 1, "filename": "h.md", "_content": "24 days of paid annual leave"}],
        ))
        self.assertFalse(result.passed)
        self.assertIn("contains_forbidden_phrase", result.failure_reasons)

    def test_refusal_of_answerable_question_fails_with_status_reason(self):
        result = self._run(RagOutcome(status="grounding_failed", answer="fallback", search_query="q"))
        self.assertFalse(result.passed)
        self.assertIn("unexpected_grounding_failed", result.failure_reasons)
        self.assertEqual(result.fact_recall, 0.0)

    def test_unanswerable_question_passes_when_refused(self):
        case = EvaluationCase.from_dict({"id": "u", "category": "Unanswerable", "question": "q?", "should_fallback": True})
        refused = self._run(RagOutcome(status="no_context", answer="none", search_query="q"), case)
        answered = self._run(RagOutcome(status="answered", answer="Tokyo [Source 1].", search_query="q"), case)
        self.assertTrue(refused.passed)
        self.assertFalse(answered.passed)

    def test_cited_refusal_is_scored_as_refusal_and_flagged(self):
        case = EvaluationCase.from_dict({"id": "u", "category": "Unanswerable", "question": "q?", "should_fallback": True})
        outcome = RagOutcome(
            status="answered",
            answer="I could not find the answer in the uploaded documents. [Source 5]",
            search_query="q",
        )
        unanswerable = self._run(outcome, case)
        answerable = self._run(outcome)
        self.assertTrue(unanswerable.passed)
        self.assertTrue(unanswerable.refused)
        self.assertIn("citation_attached_to_refusal", unanswerable.failure_reasons)
        self.assertFalse(answerable.passed)
        self.assertIn("unexpected_model_declined", answerable.failure_reasons)

    def test_summary_separates_answer_and_refusal_metrics(self):
        results = [
            evaluator.EvaluationResult("a", "Specific", "q", False, "answered", "x", "x", True, fact_recall=1.0),
            evaluator.EvaluationResult("b", "Specific", "q", False, "no_context", "x", "", False, refused=True, fact_recall=0.0),
            evaluator.EvaluationResult("c", "Unanswerable", "q", True, "no_context", "x", "", True, refused=True),
        ]
        summary = evaluator.summarize_results(results)
        self.assertEqual(summary["answer_accuracy"], 0.5)
        self.assertEqual(summary["false_refusal_rate"], 0.5)
        self.assertEqual(summary["refusal_accuracy"], 1.0)
        self.assertEqual(summary["categories"]["Specific"], {"total": 2, "passed": 1, "pass_rate": 0.5})


if __name__ == "__main__":
    unittest.main()


class ResumeTests(unittest.TestCase):
    META = {"dataset": "d.json", "provider": "ollama", "model": "m", "config": {"k": 1}, "corpus_fingerprint": "f"}

    def _write(self, directory, **overrides):
        import json

        path = Path(directory) / "run.json"
        result = evaluator.EvaluationResult("a", "Specific", "q", False, "answered", "x", "x", True).to_dict()
        path.write_text(json.dumps({**self.META, **overrides, "results": [result]}), encoding="utf-8")
        return path

    def test_resume_reuses_results_with_matching_settings(self):
        import tempfile

        from app.evaluation.runner import _load_resumable

        with tempfile.TemporaryDirectory() as directory:
            results = _load_resumable(self._write(directory), self.META)
        self.assertEqual([item.case_id for item in results], ["a"])
        self.assertTrue(results[0].passed)

    def test_resume_refuses_results_from_other_settings(self):
        import tempfile

        from app.evaluation.runner import _load_resumable

        with tempfile.TemporaryDirectory() as directory:
            path = self._write(directory, model="other")
            with self.assertRaises(SystemExit):
                _load_resumable(path, self.META)


class LlmCacheTests(unittest.TestCase):
    CONFIG = {"provider": "gemini", "gemini_model": "gemini-2.5-flash", "temperature": 0.1, "max_output_tokens": 800}

    def test_identical_request_is_sent_once_and_survives_restart(self):
        import tempfile

        from app.evaluation import llm_cache

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "cache.json"
            with patch.object(llm_cache, "generate_response", return_value="Answer [Source 1].") as generate:
                cache = llm_cache.LlmCache(path)
                cache.generate("prompt", self.CONFIG, "system")
                cache.generate("prompt", self.CONFIG, "system")
                llm_cache.LlmCache(path).generate("prompt", self.CONFIG, "system")
                llm_cache.LlmCache(path).generate("other prompt", self.CONFIG, "system")
            self.assertEqual(generate.call_count, 2)
            self.assertEqual((cache.misses, cache.hits), (1, 1))

    def test_empty_drafts_are_not_cached(self):
        from app.evaluation import llm_cache

        with patch.object(llm_cache, "generate_response", return_value="") as generate:
            cache = llm_cache.LlmCache(None)
            cache.generate("prompt", self.CONFIG)
            cache.generate("prompt", self.CONFIG)
        self.assertEqual(generate.call_count, 2)


class GeminiOptionsTests(unittest.TestCase):
    def test_thinking_disabled_only_where_supported(self):
        from app.services.llm import _request_options

        self.assertEqual(_request_options("gemini", "gemini-2.5-flash"), {"reasoning_effort": "none"})
        self.assertEqual(_request_options("gemini", "gemini-2.5-pro"), {})
        self.assertEqual(_request_options("gemini", "gemini-3.8-flash"), {"reasoning_effort": "low"})
        self.assertEqual(_request_options("ollama", "qwen3:8b"), {})
