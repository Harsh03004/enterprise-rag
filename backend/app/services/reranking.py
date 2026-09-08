from sentence_transformers import CrossEncoder


MODEL_NAME = "cross-encoder/ms-marco-MiniLM-L-6-v2"

model = CrossEncoder(MODEL_NAME)


def rerank_chunks(
    query: str,
    results,
    limit: int = 5,
):
    if not results:
        return []

    pairs = [
        (query, chunk.content)
        for chunk, document, distance in results
    ]

    scores = model.predict(pairs)

    ranked = sorted(
        zip(results, scores),
        key=lambda item: float(item[1]),
        reverse=True,
    )

    return [
        (result, float(score))
        for result, score in ranked[:limit]
    ]


def has_sufficient_confidence(
    ranked_results,
    minimum_score: float = -12.0,
) -> bool:
    """
    Determine whether the strongest retrieved chunk is relevant
    enough to support an answer.

    The reranker score is the primary confidence signal. We do not
    require a score margin between the first and second chunks because
    broad questions can legitimately have several similarly relevant
    chunks.
    """

    if not ranked_results:
        return False

    best_score = float(ranked_results[0][1])

    return best_score >= minimum_score


def score_chunks(
    query: str,
    results,
):
    if not results:
        return []

    pairs = [
        (
            query,
            chunk.content,
        )
        for chunk, document, distance in results
    ]

    scores = model.predict(pairs)

    return [
        (
            result,
            float(score),
        )
        for result, score in zip(results, scores)
    ]
