from __future__ import annotations

import re
from collections.abc import Iterable


def normalize_text(text: str) -> str:
    return re.sub(
        r"\s+",
        " ",
        re.sub(
            r"[^a-z0-9\s]",
            " ",
            text.lower(),
        ),
    ).strip()


def token_f1(
    prediction: str,
    reference: str,
) -> float:
    prediction_tokens = normalize_text(prediction).split()
    reference_tokens = normalize_text(reference).split()

    if not prediction_tokens or not reference_tokens:
        return 0.0

    prediction_counts = {}

    for token in prediction_tokens:
        prediction_counts[token] = (
            prediction_counts.get(token, 0) + 1
        )

    reference_counts = {}

    for token in reference_tokens:
        reference_counts[token] = (
            reference_counts.get(token, 0) + 1
        )

    overlap = sum(
        min(
            prediction_counts.get(token, 0),
            reference_counts.get(token, 0),
        )
        for token in prediction_counts
    )

    if overlap == 0:
        return 0.0

    precision = overlap / len(prediction_tokens)
    recall = overlap / len(reference_tokens)

    if precision + recall == 0:
        return 0.0

    return (
        2 * precision * recall
        / (precision + recall)
    )


def keyword_recall(
    answer: str,
    expected_keywords: Iterable[str],
) -> float:
    keywords = list(expected_keywords)

    if not keywords:
        return 0.0

    normalized_answer = normalize_text(answer)

    matched = sum(
        1
        for keyword in keywords
        if normalize_text(keyword) in normalized_answer
    )

    return matched / len(keywords)


def retrieval_recall(
    retrieved_ids: Iterable[int],
    relevant_ids: Iterable[int],
) -> float:
    relevant = set(relevant_ids)

    if not relevant:
        return 0.0

    retrieved = set(retrieved_ids)

    return len(retrieved & relevant) / len(relevant)


def retrieval_precision(
    retrieved_ids: Iterable[int],
    relevant_ids: Iterable[int],
) -> float:
    retrieved = list(retrieved_ids)

    if not retrieved:
        return 0.0

    relevant = set(relevant_ids)

    if not relevant:
        return 0.0

    return len(set(retrieved) & relevant) / len(retrieved)


def citation_recall(
    cited_source_ids: Iterable[int],
    relevant_source_ids: Iterable[int],
) -> float:
    """
    Measures how many expected source IDs were cited.

    Example:
        expected = [1, 2, 3]
        cited    = [1, 3]

        recall = 2 / 3
    """

    expected = set(relevant_source_ids)

    if not expected:
        return 0.0

    cited = set(cited_source_ids)

    return len(cited & expected) / len(expected)


def citation_precision(
    cited_source_ids: Iterable[int],
    relevant_source_ids: Iterable[int],
) -> float:
    """
    Measures how many cited sources were actually expected.
    """

    cited = set(cited_source_ids)

    if not cited:
        return 0.0

    expected = set(relevant_source_ids)

    if not expected:
        return 0.0

    return len(cited & expected) / len(cited)


def fallback_accuracy(
    predicted_fallback: bool,
    expected_fallback: bool,
) -> float:
    return float(
        predicted_fallback == expected_fallback
    )


def average(
    values: Iterable[float],
) -> float:
    values = list(values)

    if not values:
        return 0.0

    return sum(values) / len(values)