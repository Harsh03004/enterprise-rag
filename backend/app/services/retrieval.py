from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.services.embedding import generate_embedding


def search_similar_chunks(
    db: Session,
    query: str,
    user_id: int,
    document_id: int | None = None,
    limit: int = 5,
):
    query_embedding = generate_embedding(query)

    statement = (
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
        statement = statement.where(
            Document.id == document_id
        )

    statement = (
        statement
        .order_by("distance")
        .limit(limit)
    )

    return db.execute(statement).all()