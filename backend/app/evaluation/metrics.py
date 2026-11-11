"""Deterministic scoring functions for RAG evaluation."""

from __future__ import annotations

import re
from collections.abc import Iterable, Sequence


def normalize_text(text: str) -> str:
    """Lowercase, replace punctuation with spaces and collapse whitespace."""
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9\s]", " ", (text or "").lower())).strip()


def contains_phrase(text: str, phrase: str) -> bool:
    """Whole-token phrase match after normalisation ("24 days" ≠ "124 days")."""
    normalized_phrase = normalize_text(phrase)
    if not normalized_phrase:
        return False
    return f" {normalized_phrase} " in f" {normalize_text(text)} "


CITATION_PATTERN = re.compile(r"\[(?:Source\s+)?\d+\]", re.IGNORECASE)


def strip_citations(text: str) -> str:
    """Remove [Source N] labels so their numbers never satisfy a fact check."""
    return CITATION_PATTERN.sub(" ", text or "")


def matched_facts(answer: str, required_facts: Sequence[Sequence[str]]) -> list[bool]:
    """For each required fact, whether any accepted phrasing appears in the answer."""
    text = strip_citations(answer)
    return [any(contains_phrase(text, phrasing) for phrasing in fact) for fact in required_facts]


def forbidden_hits(answer: str, forbidden: Iterable[str]) -> list[str]:
    text = strip_citations(answer)
    return [phrase for phrase in forbidden if contains_phrase(text, phrase)]


def passage_in_text(quote: str, text: str) -> bool:
    """Whether a labelled evidence quote appears in a chunk (whitespace/case-insensitive)."""
    normalized_quote = normalize_text(quote)
    return bool(normalized_quote) and normalized_quote in normalize_text(text)


def chunk_relevance(
    chunks: Sequence[tuple[str, str]],
    passages: Sequence[tuple[str, str]],
) -> list[set[int]]:
    """Map each (filename, content) chunk to the indexes of passages it contains."""
    return [
        {
            index
            for index, (document, quote) in enumerate(passages)
            if filename == document and passage_in_text(quote, content)
        }
        for filename, content in chunks
    ]


def retrieval_scores(relevance: Sequence[set[int]], passage_count: int) -> dict[str, float]:
    """Retrieval quality for one ranked list, given per-chunk relevance sets.

    passage_recall: share of labelled passages found in any retrieved chunk.
    hit:            1 if at least one labelled passage was retrieved.
    mrr:            reciprocal rank of the first chunk holding a labelled passage.
    precision:      share of retrieved chunks that hold any labelled passage.
    """
    found = set().union(*relevance) if relevance else set()
    first_rank = next((rank for rank, hits in enumerate(relevance, start=1) if hits), None)
    return {
        "passage_recall": len(found) / passage_count if passage_count else 0.0,
        "hit": 1.0 if found else 0.0,
        "mrr": 1.0 / first_rank if first_rank else 0.0,
        "precision": (sum(1 for hits in relevance if hits) / len(relevance)) if relevance else 0.0,
    }


def citation_scores(cited_ids: Iterable[int], relevant_ids: Iterable[int]) -> dict[str, float | None]:
    """Precision/recall of cited [Source N] labels against sources holding evidence.

    Returns None for a score that is undefined (nothing cited / no relevant source
    in the context) so averages are not skewed by cases that cannot be scored.
    """
    cited = set(cited_ids)
    relevant = set(relevant_ids)
    overlap = len(cited & relevant)
    return {
        "precision": overlap / len(cited) if cited else None,
        "recall": overlap / len(relevant) if relevant else None,
    }


def average(values: Iterable[float | None]) -> float | None:
    numbers = [float(value) for value in values if value is not None]
    if not numbers:
        return None
    return sum(numbers) / len(numbers)
