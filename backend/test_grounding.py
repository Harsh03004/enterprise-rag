"""Tests for sentence-level grounding (the entailment model is replaced by a stub)."""

import re
import unittest
from unittest.mock import patch

from app.services import grounding, rag
from app.services.grounding import (
    PARTIAL_NOTE,
    evidence_units,
    ground_answer,
    split_sentences,
)

# The stub "entails" a hypothesis when they share a code word.
CODE_WORDS = {"alpha", "beta", "gamma", "delta"}


def fake_entailment(pairs):
    scores = []
    for premise, hypothesis in pairs:
        shared = CODE_WORDS & set(re.findall(r"[a-z]+", premise.lower())) & set(
            re.findall(r"[a-z]+", hypothesis.lower())
        )
        scores.append(0.95 if shared else 0.02)
    return scores


def fake_embeddings(texts):
    return [[1.0, 0.0] for _ in texts]


SOURCES = [
    {"id": 1, "_content": "The alpha plan costs 5 USD. Unrelated filler sentence here."},
    {"id": 2, "_content": "The beta feature ships in March. Gamma is mentioned as well."},
]


class GroundingTestCase(unittest.TestCase):
    def setUp(self):
        for target, replacement in (
            ("entailment_scores", fake_entailment),
            ("generate_embeddings", fake_embeddings),
        ):
            patcher = patch.object(grounding, target, side_effect=replacement)
            patcher.start()
            self.addCleanup(patcher.stop)


class SegmentationTests(unittest.TestCase):
    def test_citation_after_period_stays_with_its_sentence(self):
        sentences = split_sentences("First claim here. [Source 1] Second claim here [Source 2].")
        self.assertEqual([s.citations for s in sentences], [[1], [2]])
        self.assertEqual(sentences[0].claim, "First claim here.")

    def test_decimals_and_list_items(self):
        sentences = split_sentences("Prices:\n- Pro costs 8.99 USD [Source 1].\n- Plus costs 3.99 USD [Source 1].")
        self.assertEqual([s.is_claim for s in sentences], [False, True, True])
        self.assertIn("8.99", sentences[1].claim)

    def test_headings_are_not_claims(self):
        sentences = split_sentences("## Summary of the policy\nMFA is mandatory for accounts [Source 1].")
        self.assertFalse(sentences[0].is_claim)
        self.assertTrue(sentences[1].is_claim)

    def test_table_rows_carry_their_header(self):
        units = evidence_units("| Plan | Price |\n| Pro | 8.99 USD |")
        self.assertIn("Plan Price. Pro 8.99 USD", units)


class LexicalSupportTests(unittest.TestCase):
    SOURCE = "Orion Home Devices released the Orion X2 smart thermostat in March 2026."

    def test_faithful_paraphrase_is_supported(self):
        self.assertTrue(grounding.lexically_supported("The Orion X2 was released in March 2026.", "When was it released?", self.SOURCE))

    def test_claim_restating_question_terms_is_checked_against_source(self):
        table = "Matter support Yes No. Orion X2 (2026) Orion X1 (2023)"
        question = "Does the Orion X1 support Matter?"
        self.assertTrue(grounding.lexically_supported("No, the Orion X1 does not support Matter.", question, table))
        self.assertFalse(grounding.lexically_supported("No, the Orion X1 does not support Matter.", question, "Battery life 18 months"))

    def test_word_forms_match(self):
        source = "Uses Socket.IO to enable real-time messaging, emoji reactions, and notifications."
        self.assertTrue(grounding.lexically_supported(
            "Socket.IO enables real-time messaging, emoji reactions, and notifications.", None, source))

    def test_changed_number_or_new_words_are_not(self):
        self.assertFalse(grounding.lexically_supported("The Orion X2 was released in March 2033.", None, self.SOURCE))
        self.assertFalse(grounding.lexically_supported("The Orion X2 lacks robust security features.", None, self.SOURCE))


class GroundAnswerTests(GroundingTestCase):
    def test_supported_answer_is_unchanged_and_keeps_markdown(self):
        answer = "Key facts:\n- The `alpha` plan costs 5 USD [Source 1].\n- **Beta** ships in March [Source 2]."
        result = ground_answer(answer, SOURCES)
        self.assertEqual(result.status, "verified")
        self.assertEqual(result.answer, answer)
        self.assertEqual(result.cited_ids, [1, 2])

    def test_unsupported_sentence_is_removed_with_note(self):
        answer = "The alpha plan costs 5 USD [Source 1]. The omega tier is unlimited [Source 1]."
        result = ground_answer(answer, SOURCES)
        self.assertEqual(result.status, "partial")
        self.assertEqual(result.answer, f"The alpha plan costs 5 USD [Source 1].\n\n{PARTIAL_NOTE}")
        self.assertEqual(result.removed, 1)

    def test_removed_list_item_leaves_no_empty_bullet(self):
        answer = "- The alpha plan costs 5 USD [Source 1].\n- The omega tier is unlimited [Source 1]."
        result = ground_answer(answer, SOURCES)
        self.assertTrue(result.answer.startswith("- The alpha plan costs 5 USD [Source 1]."))
        self.assertNotIn("\n- \n", result.answer)
        self.assertNotRegex(result.answer, r"(?m)^- *$")

    def test_wrong_citation_is_corrected(self):
        result = ground_answer("The beta feature ships in March [Source 1].", SOURCES)
        self.assertEqual(result.status, "verified")
        self.assertEqual(result.answer, "The beta feature ships in March [Source 2].")
        self.assertEqual(result.corrected, 1)

    def test_uncited_supported_claim_gets_a_citation(self):
        result = ground_answer("The alpha plan costs 5 USD.", SOURCES)
        self.assertEqual(result.answer, "The alpha plan costs 5 USD [Source 1].")
        self.assertEqual(result.cited_ids, [1])

    def test_answer_without_any_supported_claim_is_unsupported(self):
        result = ground_answer("The omega tier is unlimited [Source 1].", SOURCES)
        self.assertEqual(result.status, "unsupported")
        self.assertEqual(result.answer, "")

    def test_connective_lines_need_no_citation(self):
        result = ground_answer("Here is what I found:\nThe alpha plan costs 5 USD [Source 1].", SOURCES)
        self.assertEqual(result.status, "verified")
        self.assertTrue(result.answer.startswith("Here is what I found:"))

    def test_short_fragment_is_judged_with_the_question(self):
        seen = []

        def recording(pairs):
            seen.extend(pairs)
            return fake_entailment(pairs)

        with patch.object(grounding, "entailment_scores", side_effect=recording):
            ground_answer("5 USD [Source 1].", SOURCES, question="What does the alpha plan cost?")
        self.assertTrue(all(hypothesis.startswith("What does the alpha plan cost?") for _p, hypothesis in seen))


class FinalizeAnswerTests(GroundingTestCase):
    def test_model_refusal_returns_plain_refusal_without_sources(self):
        with patch.object(rag, "ground_answer") as ground:
            answer, sources, status, details = rag.finalize_answer(rag.MODEL_REFUSAL_ANSWER, SOURCES)
        ground.assert_not_called()
        self.assertEqual((answer, sources, status, details), (rag.MODEL_REFUSAL_ANSWER, [], "model_declined", None))

    def test_partial_answer_exposes_only_supporting_sources(self):
        answer, sources, status, details = rag.finalize_answer(
            "The beta feature ships in March [Source 2]. The omega tier is unlimited [Source 1].", SOURCES
        )
        self.assertEqual(status, "answered")
        self.assertEqual([source["id"] for source in sources], [2])
        self.assertIn(PARTIAL_NOTE, answer)
        self.assertEqual(details.status, "partial")

    def test_unsupported_answer_becomes_grounding_fallback(self):
        answer, sources, status, _details = rag.finalize_answer("The omega tier is unlimited [Source 1].", SOURCES)
        self.assertEqual((answer, sources, status), (rag.GROUNDING_FALLBACK, [], "grounding_failed"))


if __name__ == "__main__":
    unittest.main()


class CitationFormatTests(GroundingTestCase):
    def test_grouped_citations_are_normalized(self):
        self.assertEqual(rag.normalize_citation_groups("A [Source 1, Source 2]. B [1, 3]. C [Sources 2 and 4]."),
                         "A [Source 1] [Source 2]. B [Source 1] [Source 3]. C [Source 2] [Source 4].")

    def test_claim_combining_two_cited_sources_is_kept_with_both_cards(self):
        sources = [
            {"id": 1, "_content": "The platform is secure and customizable."},
            {"id": 2, "_content": "It is designed for students and educators."},
        ]
        result = ground_answer("The platform is secure, customizable and designed for students [Source 1] [Source 2].", sources)
        self.assertEqual(result.status, "verified")
        self.assertEqual(result.cited_ids, [1, 2])
