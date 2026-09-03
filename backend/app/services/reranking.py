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
    minimum_margin: float = 0.05,
) -> bool:
    """
    Determine whether retrieved evidence is strong enough
    to answer the user's question.

    The margin requirement is intentionally small because
    broad questions such as summaries can legitimately have
    several similarly relevant chunks.
    """

    if not ranked_results:
        return False

    best_score = ranked_results[0][1]

    if best_score < minimum_score:
        return False

    if len(ranked_results) == 1:
        return True

    second_score = ranked_results[1][1]
    margin = best_score - second_score

    return margin >= minimum_margin


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
