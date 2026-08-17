from sqlalchemy.orm import Session

from app.models.document_chunk import DocumentChunk
from app.services.embedding import generate_embedding


def embed_document_chunk(
    db: Session,
    chunk: DocumentChunk,
) -> None:
    chunk.embedding = generate_embedding(chunk.content)

    db.commit()
    db.refresh(chunk)