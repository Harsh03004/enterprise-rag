from __future__ import annotations

from collections.abc import Mapping

DEFAULT_METRICS = (
    "pass_rate",
    "answer_accuracy",
    "fact_recall",
    "refusal_accuracy",
    "false_refusal_rate",
    "retrieval_hit_rate",
    "passage_recall",
    "mrr",
    "citation_precision",
    "citation_recall",
)

# Metrics where a higher value is worse.
LOWER_IS_BETTER = frozenset({"false_refusal_rate"})


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
        if metric in LOWER_IS_BETTER:
            regression = -regression

        if regression > max_regression:
            failures.append(
                f"{metric} regressed from {float(baseline_value):.4f} "
                f"to {float(current_value):.4f} "
                f"(allowed regression: {max_regression:.4f})"
            )

    return failures
