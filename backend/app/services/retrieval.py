import re

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.services.embedding import generate_embedding


def keyword_query(question: str) -> str:
    """OR-combine the question's words for websearch_to_tsquery.

    Stop words are removed by the "english" text-search configuration; quotes
    and operators are stripped so user text cannot change query semantics.
    """
    words = re.findall(r"[A-Za-z0-9][A-Za-z0-9._-]*", question)
    terms = [word for word in words if len(word) > 1 and word.lower() not in {"or", "and", "not"}]
    return " or ".join(dict.fromkeys(terms)) or question


def search_similar_chunks(
    db: Session,
    query: str,
    user_id: int,
    document_id: int | None = None,
    collection_id: int | None = None,
    limit: int = 5,
    candidate_limit: int | None = None,
):
    if candidate_limit is None:
        candidate_limit = limit

    query_embedding = generate_embedding(query)

    # ---------------------------------------------------------
    # 1. Semantic / vector search
    # ---------------------------------------------------------

    vector_statement = (
        select(
            DocumentChunk,
            Document,
            DocumentChunk.embedding.cosine_distance(
                query_embedding
            ).label("distance"),
        )
        .join(
            Document,
            Document.id == DocumentChunk.document_id,
        )
        .where(
            Document.user_id == user_id,
            DocumentChunk.embedding.is_not(None),
        )
    )

    # Strict document scope
    if document_id is not None:
        vector_statement = vector_statement.where(
            Document.id == document_id
        )

    # Strict collection scope
    if collection_id is not None:
        vector_statement = vector_statement.where(
            Document.collection_id == collection_id
        )

    vector_results = (
        db.execute(
            vector_statement
            .order_by("distance")
            .limit(candidate_limit)
        )
        .all()
    )

    # ---------------------------------------------------------
    # 2. Keyword / full-text search
    # ---------------------------------------------------------

    # Match chunks containing ANY of the question's terms, ranked by
    # ts_rank_cd. websearch_to_tsquery on the raw question ANDs every word,
    # so natural-language questions usually matched nothing and retrieval
    # silently became vector-only.
    keyword_vector = func.websearch_to_tsquery(
        "english",
        keyword_query(query),
    )

    keyword_rank = func.ts_rank_cd(
        func.to_tsvector(
            "english",
            DocumentChunk.content,
        ),
        keyword_vector,
    )

    keyword_statement = (
        select(
            DocumentChunk,
            Document,
            keyword_rank.label("keyword_rank"),
        )
        .join(
            Document,
            Document.id == DocumentChunk.document_id,
        )
        .where(
            Document.user_id == user_id,
            func.to_tsvector(
                "english",
                DocumentChunk.content,
            ).op("@@")(keyword_vector),
        )
    )

    # Strict document scope
    if document_id is not None:
        keyword_statement = keyword_statement.where(
            Document.id == document_id
        )

    # Strict collection scope
    if collection_id is not None:
        keyword_statement = keyword_statement.where(
            Document.collection_id == collection_id
        )

    keyword_results = (
        db.execute(
            keyword_statement
            .order_by(keyword_rank.desc())
            .limit(candidate_limit)
        )
        .all()
    )

    # ---------------------------------------------------------
    # 3. Reciprocal Rank Fusion
    # ---------------------------------------------------------

    scores: dict[int, float] = {}
    chunks: dict[int, tuple] = {}

    k = 60

    for rank, row in enumerate(
        vector_results,
        start=1,
    ):
        chunk, document, distance = row

        scores[chunk.id] = (
            scores.get(chunk.id, 0.0)
            + 1.0 / (k + rank)
        )

        chunks[chunk.id] = (
            chunk,
            document,
            distance,
        )

    for rank, row in enumerate(
        keyword_results,
        start=1,
    ):
        chunk, document, _keyword_rank = row

        scores[chunk.id] = (
            scores.get(chunk.id, 0.0)
            + 1.0 / (k + rank)
        )

        if chunk.id not in chunks:
            chunks[chunk.id] = (
                chunk,
                document,
                1.0,
            )

    # ---------------------------------------------------------
    # 4. Sort by combined hybrid score
    # ---------------------------------------------------------

    ranked_chunk_ids = sorted(
        scores,
        key=lambda chunk_id: scores[chunk_id],
        reverse=True,
    )[:candidate_limit]

    return [
        chunks[chunk_id]
        for chunk_id in ranked_chunk_ids
    ]