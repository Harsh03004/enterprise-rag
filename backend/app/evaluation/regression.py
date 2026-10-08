from __future__ import annotations

from collections.abc import Mapping

DEFAULT_METRICS = (
    "pass_rate",
    "retrieval_recall",
    "retrieval_precision",
    "answer_f1",
    "keyword_recall",
    "citation_recall",
    "citation_precision",
    "fallback_accuracy",
)


def compare_summaries(
    current: Mapping[str, object],
    baseline: Mapping[str, object],
    max_regression: float = 0.05,
    metrics: tuple[str, ...] = DEFAULT_METRICS,
) -> list[str]:
    if max_regression < 0:
        raise ValueError("max_regression must be non-negative.")

    failures: list[str] = []

    for metric in metrics:
        current_value = current.get(metric)
        baseline_value = baseline.get(metric)

        if not isinstance(current_value, int | float):
            continue

        if not isinstance(baseline_value, int | float):
            continue

        regression = float(baseline_value) - float(current_value)

        if regression > max_regression:
            failures.append(
                f"{metric} regressed from {float(baseline_value):.4f} "
                f"to {float(current_value):.4f} "
                f"(allowed regression: {max_regression:.4f})"
            )

    return failures
