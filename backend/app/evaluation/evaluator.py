from __future__ import annotations

import re
from dataclasses import dataclass

from app.evaluation.dataset import EvaluationCase
from app.evaluation.metrics import (
    average,
    citation_precision,
    citation_recall,
    fallback_accuracy,
    keyword_recall,
    retrieval_precision,
    retrieval_recall,
    token_f1,
)
from app.services.llm import generate_response
from app.services.rag import (
    build_context_and_sources,
    build_rag_prompt,
    verify_citations,
)
from app.services.reranking import rerank_chunks
from app.services.retrieval import search_similar_chunks


FALLBACK_PHRASES = (
    "i could not verify",
    "i could not find",
    "cannot answer",
    "can't answer",
    "not enough information",
    "not found in the document",
    "not provided in the document",
)

def _extract_citation_ids(answer: str) -> list[int]:
    matches = re.findall(
        r"\[Source\s+(\d+)\]",
        answer,
        flags=re.IGNORECASE,
    )

    citation_ids: list[int] = []

    for value in matches:
        source_id = int(value)

        if source_id not in citation_ids:
            citation_ids.append(source_id)

    return citation_ids


@dataclass
class EvaluationResult:
    case_id: str
    category: str
    question: str

    answer: str
    fallback: bool

    retrieval_recall: float | None
    retrieval_precision: float | None

    answer_f1: float | None
    keyword_recall: float | None

    citation_ids: list[int]
    citation_recall: float | None
    citation_precision: float | None

    fallback_accuracy: float

    passed: bool

    def to_dict(self) -> dict:
        return {
            "case_id": self.case_id,
            "category": self.category,
            "question": self.question,
            "answer": self.answer,
            "fallback": self.fallback,
            "retrieval_recall": self.retrieval_recall,
            "retrieval_precision": self.retrieval_precision,
            "answer_f1": self.answer_f1,
            "keyword_recall": self.keyword_recall,
            "citation_ids": self.citation_ids,
            "citation_recall": self.citation_recall,
            "citation_precision": self.citation_precision,
            "fallback_accuracy": self.fallback_accuracy,
            "passed": self.passed,
        }


def _is_fallback(answer: str) -> bool:
    normalized = answer.lower().strip()

    return any(
        phrase in normalized
        for phrase in FALLBACK_PHRASES
    )


def evaluate_case(
    db,
    case: EvaluationCase,
    user_id: int,
    document_id: int | None = None,
    collection_id: int | None = None,
) -> EvaluationResult:
    """
    Evaluate one RAG case without creating a conversation.

    Retrieval and reranking happen exactly once.
    """

    # ---------------------------------------------------------
    # 1. Retrieve
    # ---------------------------------------------------------

    candidates = search_similar_chunks(
        db=db,
        query=case.question,
        user_id=user_id,
        document_id=document_id,
        collection_id=collection_id,
        limit=5,
        candidate_limit=20,
    )

    # ---------------------------------------------------------
    # 2. Rerank
    # ---------------------------------------------------------

    ranked_results = rerank_chunks(
        query=case.question,
        results=candidates,
        limit=5,
    )

    # ---------------------------------------------------------
    # 3. Retrieval metrics
    # ---------------------------------------------------------

    retrieved_chunk_ids = [
        result[0].id
        for result, _score in ranked_results
    ]

    retrieval_recall_score = None
    retrieval_precision_score = None

    if case.relevant_chunk_ids:
        retrieval_recall_score = retrieval_recall(
            retrieved_chunk_ids,
            case.relevant_chunk_ids,
        )

        retrieval_precision_score = retrieval_precision(
            retrieved_chunk_ids,
            case.relevant_chunk_ids,
        )

    # ---------------------------------------------------------
    # 4. Build context
    # ---------------------------------------------------------

    context, sources = build_context_and_sources(
    [
        result
        for result, _score in ranked_results
    ]
)

    # ---------------------------------------------------------
    # 5. Build prompt
    # ---------------------------------------------------------

    prompt = build_rag_prompt(
    question=case.question,
    history="",
    context=context,
)

    # ---------------------------------------------------------
    # 6. Generate answer
    # ---------------------------------------------------------

    answer = generate_response(prompt)

    if not answer:
        answer = ""

    # ---------------------------------------------------------
    # 7. Verify citations
    # ---------------------------------------------------------

    answer, verified_sources = verify_citations(
        answer=answer,
        sources=sources,
    )

    # ---------------------------------------------------------
    # 8. Citation metrics
    #
    # Convert expected chunk IDs into the source-number
    # namespace used by [Source N].
    # ---------------------------------------------------------

    expected_source_ids: list[int] = []

    if case.relevant_chunk_ids:
        relevant_chunks = set(case.relevant_chunk_ids)

        for source in sources:
            chunk_id = source.get("chunk_id")

            if chunk_id in relevant_chunks:
                source_id = source.get("id")

                if source_id is not None:
                    expected_source_ids.append(
                        int(source_id)
                    )

    citation_ids = _extract_citation_ids(answer)

    citation_recall_score = None
    citation_precision_score = None

    if expected_source_ids:
        citation_recall_score = citation_recall(
            citation_ids,
            expected_source_ids,
        )

        citation_precision_score = citation_precision(
            citation_ids,
            expected_source_ids,
        )

    # ---------------------------------------------------------
    # 9. Answer metrics
    # ---------------------------------------------------------

    answer_f1_score = None

    if case.expected_answer:
        answer_f1_score = token_f1(
            answer,
            case.expected_answer,
        )

    keyword_recall_score = None

    if case.expected_keywords:
        keyword_recall_score = keyword_recall(
            answer,
            case.expected_keywords,
        )

    # ---------------------------------------------------------
    # 10. Fallback
    # ---------------------------------------------------------

    fallback = _is_fallback(answer)

    fallback_accuracy_score = fallback_accuracy(
        fallback,
        case.should_fallback,
    )

    # ---------------------------------------------------------
    # 11. Pass criteria
    # ---------------------------------------------------------

    checks: list[bool] = []

    if retrieval_recall_score is not None:
        checks.append(
            retrieval_recall_score >= 0.5
        )

    if retrieval_precision_score is not None:
        checks.append(
            retrieval_precision_score >= 0.2
        )

    if answer_f1_score is not None:
        checks.append(
            answer_f1_score >= 0.5
        )

    if keyword_recall_score is not None:
        checks.append(
            keyword_recall_score >= 0.5
        )

    if citation_recall_score is not None:
        checks.append(
            citation_recall_score >= 0.5
        )

    if case.should_fallback:
        checks.append(
            fallback_accuracy_score == 1.0
        )
    else:
        checks.append(
            not fallback
        )

    passed = all(checks) if checks else False

    return EvaluationResult(
        case_id=case.id,
        category=case.category,
        question=case.question,
        answer=answer,
        fallback=fallback,
        retrieval_recall=retrieval_recall_score,
        retrieval_precision=retrieval_precision_score,
        answer_f1=answer_f1_score,
        keyword_recall=keyword_recall_score,
        citation_ids=citation_ids,
        citation_recall=citation_recall_score,
        citation_precision=citation_precision_score,
        fallback_accuracy=fallback_accuracy_score,
        passed=passed,
    )


def summarize_results(
    results: list[EvaluationResult],
) -> dict:
    if not results:
        return {
            "total": 0,
            "passed": 0,
            "failed": 0,
            "pass_rate": 0.0,
            "retrieval_recall": 0.0,
            "retrieval_precision": 0.0,
            "answer_f1": 0.0,
            "keyword_recall": 0.0,
            "citation_recall": 0.0,
            "citation_precision": 0.0,
            "fallback_accuracy": 0.0,
            "citation_count": 0.0,
        }

    return {
        "total": len(results),

        "passed": sum(
            1
            for result in results
            if result.passed
        ),

        "failed": sum(
            1
            for result in results
            if not result.passed
        ),

        "pass_rate": (
            sum(
                1
                for result in results
                if result.passed
            )
            / len(results)
        ),

        "retrieval_recall": average(
            result.retrieval_recall
            for result in results
            if result.retrieval_recall is not None
        ),

        "retrieval_precision": average(
            result.retrieval_precision
            for result in results
            if result.retrieval_precision is not None
        ),

        "answer_f1": average(
            result.answer_f1
            for result in results
            if result.answer_f1 is not None
        ),

        "keyword_recall": average(
            result.keyword_recall
            for result in results
            if result.keyword_recall is not None
        ),

        "citation_recall": average(
            result.citation_recall
            for result in results
            if result.citation_recall is not None
        ),

        "citation_precision": average(
            result.citation_precision
            for result in results
            if result.citation_precision is not None
        ),

        "fallback_accuracy": average(
            result.fallback_accuracy
            for result in results
        ),

        "citation_count": average(
            len(result.citation_ids)
            for result in results
        ),
    }