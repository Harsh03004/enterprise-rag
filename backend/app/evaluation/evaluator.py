"""Score evaluation cases against the production RAG pipeline."""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, field

from app.evaluation.dataset import EvaluationCase
from app.evaluation.metrics import (
    average,
    chunk_relevance,
    citation_scores,
    forbidden_hits,
    matched_facts,
    retrieval_scores,
)
from app.services.rag import (
    begin_rag_request,
    extract_citation_ids,
    is_model_refusal,
    run_rag_pipeline,
)

ANSWERED = "answered"


@dataclass
class EvaluationResult:
    case_id: str
    category: str
    question: str
    should_fallback: bool

    status: str
    answer: str
    draft_answer: str
    passed: bool
    refused: bool = False
    failure_reasons: list[str] = field(default_factory=list)

    # Answer quality (answerable cases)
    facts_matched: list[bool] = field(default_factory=list)
    fact_recall: float | None = None
    forbidden_found: list[str] = field(default_factory=list)

    # Retrieval quality (cases with labelled passages)
    retrieved: list[dict] = field(default_factory=list)
    passage_recall: float | None = None
    retrieval_hit: float | None = None
    mrr: float | None = None
    retrieval_precision: float | None = None

    # Grounding: what sentence-level verification changed
    statements_removed: int = 0
    citations_corrected: int = 0
    grounding_verdicts: list[dict] = field(default_factory=list)

    # Citations (answered cases)
    citation_ids: list[int] = field(default_factory=list)
    citation_precision: float | None = None
    citation_recall: float | None = None

    def to_dict(self) -> dict:
        return asdict(self)


def evaluate_case(
    db,
    case: EvaluationCase,
    user_id: int,
    collection_id: int | None = None,
    document_id: int | None = None,
    config: dict | None = None,
    generate=None,
) -> EvaluationResult:
    """Run one case through the same pipeline chat uses, without persistence."""
    begin_rag_request()
    outcome = run_rag_pipeline(
        db=db,
        user_id=user_id,
        question=case.question,
        document_id=document_id,
        collection_id=collection_id,
        config=config or {},
        generate=generate,
    )

    passages = [(passage.document, passage.quote) for passage in case.relevant_passages]
    result = EvaluationResult(
        case_id=case.id,
        category=case.category,
        question=case.question,
        should_fallback=case.should_fallback,
        status=outcome.status,
        answer=outcome.answer,
        draft_answer=outcome.draft_answer,
        passed=False,
    )

    # ---- Retrieval: which reranked chunks hold labelled evidence -------------
    ranked = [(document.filename, chunk.content) for (chunk, document, _distance), _score in outcome.ranked_results]
    relevance = chunk_relevance(ranked, passages)
    result.retrieved = [
        {
            "rank": rank,
            "filename": document.filename,
            "chunk_index": chunk.chunk_index,
            "page_number": chunk.page_number,
            "reranker_score": round(float(score), 4),
            "relevant": bool(hits),
        }
        for rank, (((chunk, document, _distance), score), hits) in enumerate(
            zip(outcome.ranked_results, relevance, strict=True), start=1
        )
    ]
    if passages:
        scores = retrieval_scores(relevance, len(passages))
        result.passage_recall = scores["passage_recall"]
        result.retrieval_hit = scores["hit"]
        result.mrr = scores["mrr"]
        result.retrieval_precision = scores["precision"]

    if outcome.grounding is not None:
        result.statements_removed = outcome.grounding.removed
        result.citations_corrected = outcome.grounding.corrected
        result.grounding_verdicts = [asdict(verdict) for verdict in outcome.grounding.verdicts]

    # A refusal sentence can pass verification once citation repair attaches a
    # [Source N] to it. Score it as the refusal the user actually sees, and flag
    # the spurious citation separately.
    cited_refusal = outcome.status == ANSWERED and is_model_refusal(outcome.answer)
    answered = outcome.status == ANSWERED and not cited_refusal
    result.refused = not answered

    # ---- Answer and citations -------------------------------------------------
    if answered:
        result.citation_ids = sorted(extract_citation_ids(outcome.answer))
        result.forbidden_found = forbidden_hits(outcome.answer, case.forbidden)
        if passages:
            source_relevance = chunk_relevance(
                [(source["filename"], source.get("_content", "")) for source in outcome.context_sources],
                passages,
            )
            relevant_ids = [
                int(source["id"])
                for source, hits in zip(outcome.context_sources, source_relevance, strict=True)
                if hits
            ]
            citations = citation_scores(result.citation_ids, relevant_ids)
            result.citation_precision = citations["precision"]
            result.citation_recall = citations["recall"]

    if case.required_facts:
        result.facts_matched = matched_facts(outcome.answer if answered else "", case.required_facts)
        result.fact_recall = sum(result.facts_matched) / len(result.facts_matched)

    # ---- Pass / fail ------------------------------------------------------------
    reasons: list[str] = []
    if cited_refusal:
        reasons.append("citation_attached_to_refusal")
    if case.should_fallback:
        if answered:
            reasons.append("answered_unanswerable_question")
    else:
        if not answered:
            reasons.append("unexpected_model_declined" if cited_refusal else f"unexpected_{outcome.status}")
        elif not all(result.facts_matched):
            reasons.append("missing_required_facts")
        if result.retrieval_hit == 0.0:
            reasons.append("evidence_not_retrieved")
    if result.forbidden_found:
        reasons.append("contains_forbidden_phrase")

    # Diagnostics are reported but do not decide the case: a case passes on the
    # outcome the user sees (a correct answer, or a refusal when expected).
    diagnostics = {"evidence_not_retrieved", "citation_attached_to_refusal"}
    blocking = [reason for reason in reasons if reason not in diagnostics]
    result.passed = not blocking
    result.failure_reasons = reasons
    return result


SUMMARY_METRICS = (
    "pass_rate",
    "answer_accuracy",
    "fact_recall",
    "refusal_accuracy",
    "false_refusal_rate",
    "retrieval_hit_rate",
    "passage_recall",
    "mrr",
    "retrieval_precision",
    "citation_precision",
    "citation_recall",
    "partial_answer_rate",
)


def summarize_results(results: list[EvaluationResult]) -> dict:
    """Aggregate scores; each metric averages only the cases it applies to."""
    answerable = [result for result in results if not result.should_fallback]
    unanswerable = [result for result in results if result.should_fallback]
    passed = sum(1 for result in results if result.passed)

    summary: dict = {
        "total": len(results),
        "passed": passed,
        "failed": len(results) - passed,
        "pass_rate": passed / len(results) if results else None,
        "answerable_cases": len(answerable),
        "unanswerable_cases": len(unanswerable),
        # Answerable questions answered with every required fact and no forbidden phrase.
        "answer_accuracy": average(1.0 if result.passed else 0.0 for result in answerable),
        "fact_recall": average(result.fact_recall for result in answerable),
        # Unanswerable questions correctly refused.
        "refusal_accuracy": average(1.0 if result.passed else 0.0 for result in unanswerable),
        # Answerable questions the system refused (lower is better).
        "false_refusal_rate": average(1.0 if result.refused else 0.0 for result in answerable),
        "retrieval_hit_rate": average(result.retrieval_hit for result in answerable),
        "passage_recall": average(result.passage_recall for result in answerable),
        "mrr": average(result.mrr for result in answerable),
        "retrieval_precision": average(result.retrieval_precision for result in answerable),
        "citation_precision": average(result.citation_precision for result in results),
        "citation_recall": average(result.citation_recall for result in results),
        # Answered cases where grounding removed at least one sentence.
        "partial_answer_rate": average(
            (1.0 if result.statements_removed else 0.0) for result in results if not result.refused
        ),
        "statements_removed": sum(result.statements_removed for result in results),
        "citations_corrected": sum(result.citations_corrected for result in results),
        "status_counts": dict(Counter(result.status for result in results)),
        "failure_reasons": dict(
            Counter(reason for result in results for reason in result.failure_reasons)
        ),
    }

    by_category: dict[str, list[EvaluationResult]] = defaultdict(list)
    for result in results:
        by_category[result.category].append(result)
    summary["categories"] = {
        category: {
            "total": len(items),
            "passed": sum(1 for item in items if item.passed),
            "pass_rate": sum(1 for item in items if item.passed) / len(items),
        }
        for category, items in sorted(by_category.items())
    }
    return summary
