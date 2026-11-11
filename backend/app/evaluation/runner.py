"""Run the RAG evaluation suite.

    uv run python -m app.evaluation.runner                       # full suite
    uv run python -m app.evaluation.runner --case handbook-leave-001
    uv run python -m app.evaluation.runner --baseline evaluation/baselines/gemini-3.1-flash-lite.json

The corpus is ingested automatically for a dedicated evaluation user (see
app.evaluation.corpus); no existing documents or IDs are needed.
"""

from __future__ import annotations

import argparse
import json
import os
import tempfile
import time
from dataclasses import fields
from pathlib import Path

from app.core.config import settings
from app.db.session import SessionLocal
from app.evaluation.corpus import corpus_fingerprint, ensure_corpus
from app.evaluation.dataset import load_dataset
from app.evaluation.evaluator import (
    SUMMARY_METRICS,
    EvaluationResult,
    evaluate_case,
    summarize_results,
)
from app.evaluation.llm_cache import LlmCache
from app.evaluation.regression import compare_summaries
from app.models.evaluation_run import EvaluationRun
from app.services.rag_settings import get_rag_config

EVALUATION_DIR = Path(__file__).resolve().parents[2] / "evaluation"
CONFIG_SNAPSHOT_KEYS = (
    "retrieval_top_k",
    "candidate_multiplier",
    "rerank_limit",
    "minimum_reranker_score",
    "max_context_chars",
    "temperature",
    "max_output_tokens",
    "chunk_size",
    "chunk_overlap",
    "embedding_model",
)


def _write_json_atomic(path: Path, payload: dict) -> None:
    """Write a complete checkpoint without leaving a truncated result file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as file:
            temporary_path = Path(file.name)
            json.dump(payload, file, indent=2, ensure_ascii=False)
            file.flush()
            os.fsync(file.fileno())
        # NamedTemporaryFile creates 0600 files; results are meant to be read
        # by the host user even when a container (root) writes them.
        os.chmod(temporary_path, 0o644)
        os.replace(temporary_path, path)
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)


def _can_compare_regression(result_count: int, case_errors: list[dict]) -> bool:
    """Only compare completed case results; operational failures are not scores."""
    return result_count > 0 and not case_errors


MAX_CONSECUTIVE_ERRORS = 3
RESUME_KEYS = ("dataset", "provider", "model", "config", "grounding", "corpus_fingerprint")


def _load_resumable(output_path: Path, metadata: dict) -> list[EvaluationResult]:
    """Completed results from an earlier run with identical settings, if any."""
    if not output_path.is_file():
        return []
    previous = json.loads(output_path.read_text(encoding="utf-8"))
    mismatched = [key for key in RESUME_KEYS if previous.get(key) != metadata.get(key)]
    if mismatched:
        raise SystemExit(
            f"Cannot resume {output_path}: it was produced with different {', '.join(mismatched)}. "
            "Use a new --output file or run without --resume."
        )
    known = {item.name for item in fields(EvaluationResult)}
    return [
        EvaluationResult(**{key: value for key, value in item.items() if key in known})
        for item in previous.get("results", [])
    ]


def _fmt(value: float | None, percent: bool = False) -> str:
    if value is None:
        return "n/a"
    return f"{value:.1%}" if percent else f"{value:.3f}"


def _print_case(result) -> None:
    facts = (
        f"{sum(result.facts_matched)}/{len(result.facts_matched)}"
        if result.facts_matched
        else "n/a"
    )
    print(f"Status:     {result.status}")
    print(f"Facts:      {facts}")
    print(
        f"Retrieval:  hit={_fmt(result.retrieval_hit)} recall={_fmt(result.passage_recall)} "
        f"mrr={_fmt(result.mrr)}"
    )
    print(
        f"Citations:  {result.citation_ids} precision={_fmt(result.citation_precision)} "
        f"recall={_fmt(result.citation_recall)}"
    )
    print(f"Answer:     {result.answer[:300]}")
    verdict = "PASS" if result.passed else "FAIL"
    reasons = f" ({', '.join(result.failure_reasons)})" if result.failure_reasons else ""
    print(f"RESULT:     {verdict}{reasons}")


def _print_summary(summary: dict) -> None:
    print()
    print("=" * 80)
    print("FINAL EVALUATION SUMMARY")
    print("=" * 80)
    print(f"Cases:               {summary['total']} ({summary['answerable_cases']} answerable, "
          f"{summary['unanswerable_cases']} unanswerable)")
    print(f"Passed:              {summary['passed']}  Failed: {summary['failed']}")
    for metric in SUMMARY_METRICS:
        print(f"{metric + ':':<21}{_fmt(summary.get(metric), percent=True)}")
    print(f"Statuses:            {summary['status_counts']}")
    if summary["failure_reasons"]:
        print(f"Failure reasons:     {summary['failure_reasons']}")
    print("By category:")
    for category, stats in summary["categories"].items():
        print(f"  {category:<18} {stats['passed']}/{stats['total']}  ({stats['pass_rate']:.0%})")
    print("=" * 80)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the Enterprise RAG evaluation suite.")
    parser.add_argument("--dataset", default=str(EVALUATION_DIR / "dataset.json"))
    parser.add_argument("--corpus-dir", default=str(EVALUATION_DIR / "corpus"))
    parser.add_argument("--reingest", action="store_true", help="Re-ingest the corpus even if unchanged.")
    parser.add_argument("--case", action="append", default=[], help="Only run these case IDs (repeatable).")
    parser.add_argument("--provider", choices=("gemini", "ollama", "openrouter"), default=None)
    parser.add_argument("--model", default=None)
    parser.add_argument("--output", default="evaluation_results.json")
    parser.add_argument("--baseline", default=None, help="Existing evaluation JSON to compare against.")
    parser.add_argument(
        "--max-regression",
        type=float,
        default=0.05,
        help="Maximum allowed drop for aggregate metrics.",
    )
    parser.add_argument("--no-record", action="store_true", help="Do not store the run for the admin dashboard.")
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Keep completed cases from --output (same dataset, model and settings) and run the rest.",
    )
    parser.add_argument(
        "--no-llm-cache",
        action="store_true",
        help="Always send prompts to the LLM instead of reusing cached drafts of identical requests.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Run at most this many not-yet-completed cases, then stop (use with --resume for batches).",
    )
    parser.add_argument(
        "--pause-seconds",
        type=float,
        default=0.0,
        help="Sleep between cases to keep a laptop responsive during long local runs.",
    )
    args = parser.parse_args()

    dataset = load_dataset(args.dataset)
    cases = dataset.cases
    if args.case:
        wanted = set(args.case)
        unknown = wanted - {case.id for case in cases}
        if unknown:
            raise SystemExit(f"Unknown case IDs: {', '.join(sorted(unknown))}")
        cases = [case for case in cases if case.id in wanted]
    output_path = Path(args.output)

    db = SessionLocal()
    results = []
    case_errors = []

    try:
        rag_config = get_rag_config(db)
        if args.provider:
            rag_config["provider"] = args.provider
        if args.model:
            rag_config[f"{rag_config['provider']}_model"] = args.model
        # Every case must reach the pipeline; a cached answer would skip it.
        rag_config["query_cache_enabled"] = False
        provider = rag_config["provider"]
        model = rag_config[f"{provider}_model"]

        scope = ensure_corpus(db, args.corpus_dir, dataset.corpus, reingest=args.reingest)
        safe_model = "".join(ch if ch.isalnum() or ch in "._-" else "-" for ch in model)
        llm_cache = LlmCache(
            None if args.no_llm_cache else output_path.parent / "llm_cache" / f"{provider}-{safe_model}.json"
        )
        metadata = {
            "dataset": Path(args.dataset).name,
            "provider": provider,
            "model": model,
            "config": {key: rag_config.get(key) for key in CONFIG_SNAPSHOT_KEYS},
            "grounding": {
                "model": settings.grounding_model,
                "min_entailment": settings.grounding_min_entailment,
            },
            "corpus_fingerprint": corpus_fingerprint(Path(args.corpus_dir), dataset.corpus, rag_config),
            "partial": bool(args.case),
            "scope": {"user_id": scope.user_id, "collection_id": scope.collection_id},
        }

        if args.resume:
            results = [item for item in _load_resumable(output_path, metadata) if item.case_id in {c.id for c in cases}]
            done = {item.case_id for item in results}
            cases_to_run = [case for case in cases if case.id not in done]
        else:
            cases_to_run = cases
        if args.limit is not None:
            cases_to_run = cases_to_run[: max(args.limit, 0)]
        batch_only = len(results) + len(cases_to_run) < len(cases)

        print("=" * 80)
        print("ENTERPRISE RAG EVALUATION")
        print("=" * 80)
        print(f"Dataset:    {args.dataset} ({len(cases)} of {len(dataset.cases)} cases)")
        print(f"Provider:   {provider} / {model}")
        print(f"Collection: {scope.collection_id} ({len(scope.document_ids)} documents)")
        if args.resume:
            print(f"Resuming:   {len(results)} completed, {len(cases_to_run)} remaining")
        print("=" * 80)

        offset = len(results)
        consecutive_errors = 0
        for number, case in enumerate(cases_to_run, start=offset + 1):
            if args.pause_seconds and number > offset + 1:
                time.sleep(args.pause_seconds)
            print()
            print(f"--- CASE {number}/{len(cases)}  {case.id}  [{case.category}]")
            print(f"Question:   {case.question}")
            try:
                result = evaluate_case(
                    db=db,
                    case=case,
                    user_id=scope.user_id,
                    collection_id=scope.collection_id,
                    config=rag_config,
                    generate=llm_cache.generate,
                )
                results.append(result)
                _print_case(result)
            except Exception as exc:  # noqa: BLE001 - any case failure is recorded, not fatal
                # A failed SQL statement leaves the session unusable until rollback.
                db.rollback()
                print(f"ERROR: {exc}")
                print("RESULT:     FAIL (error)")
                case_errors.append(
                    {"case_id": case.id, "category": case.category, "question": case.question, "error": str(exc)}
                )
                # Failures in a row (wrong model, bad key, quota) only waste
                # requests: stop and let --resume continue after a fix.
                consecutive_errors += 1
                if consecutive_errors >= MAX_CONSECUTIVE_ERRORS:
                    print(f"STOPPING: {MAX_CONSECUTIVE_ERRORS} cases failed in a row; fix the error above and rerun.")
                    break
            else:
                consecutive_errors = 0

            # Keep a durable artifact after every case so an interrupted run
            # still leaves its completed results available.
            _write_json_atomic(
                output_path,
                {
                    "status": "running",
                    **metadata,
                    "summary": summarize_results(results),
                    "results": [item.to_dict() for item in results],
                    "case_errors": case_errors,
                },
            )

        summary = summarize_results(results)
        comparable = _can_compare_regression(len(results), case_errors)
        regression_failures: list[str] = []
        payload = {
            "status": "completed" if comparable else "incomplete",
            **metadata,
            "summary": summary,
            "results": [item.to_dict() for item in results],
            "case_errors": case_errors,
        }

        if args.baseline and comparable and not args.case and not batch_only:
            baseline_payload = json.loads(Path(args.baseline).read_text(encoding="utf-8"))
            regression_failures = compare_summaries(
                current=summary,
                baseline=baseline_payload["summary"],
                max_regression=args.max_regression,
            )
            payload["regression_failures"] = regression_failures
            payload["baseline"] = Path(args.baseline).name
        elif args.baseline:
            payload["regression_skipped_reason"] = (
                "Only a subset of cases was run."
                if args.case or batch_only
                else "Evaluation cases had operational errors."
                if case_errors
                else "The dataset contained no cases."
            )

        _write_json_atomic(output_path, payload)
        _print_summary(summary)
        print(f"LLM requests:        {llm_cache.misses} sent, {llm_cache.hits} reused from cache")
        print(f"Results written to: {output_path}")
        if batch_only:
            remaining = len(cases) - len(results) - len(case_errors)
            print(f"BATCH DONE: {remaining} cases remain; rerun the same command to continue.")
            return

        if not comparable:
            print("REGRESSION CHECK: SKIPPED (evaluation incomplete; inspect case errors)")
            for failure in case_errors:
                print(f"- Case {failure['case_id']} failed: {failure['error']}")
            raise SystemExit(1)

        if not args.no_record and not args.case and not batch_only:
            db.add(
                EvaluationRun(
                    dataset_name=metadata["dataset"],
                    user_id=scope.user_id,
                    document_id=None,
                    collection_id=scope.collection_id,
                    provider=provider,
                    model=model,
                    summary=summary,
                    results=payload["results"],
                    case_errors=case_errors,
                    regression_failures=regression_failures,
                    max_regression=args.max_regression if args.baseline else None,
                )
            )
            db.commit()

        if regression_failures:
            print("REGRESSION CHECK: FAIL")
            for failure in regression_failures:
                print(f"- {failure}")
            raise SystemExit(1)
        if args.baseline and "regression_failures" in payload:
            print("REGRESSION CHECK: PASS")

    finally:
        db.close()


if __name__ == "__main__":
    main()
