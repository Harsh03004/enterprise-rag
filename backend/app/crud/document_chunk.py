from sqlalchemy.orm import Session

from app.models.document_chunk import DocumentChunk


def create_document_chunk(
    db: Session,
    document_id: int,
    chunk_index: int,
    content: str,
) -> DocumentChunk:
    chunk = DocumentChunk(
        document_id=document_id,
        chunk_index=chunk_index,
        content=content,
    )

    db.add(chunk)

    return chunk

def create_document_chunks(
    db: Session,
    document_id: int,
    chunks: list[str],
) -> list[DocumentChunk]:

    existing_chunks = (
        db.query(DocumentChunk)
        .filter(DocumentChunk.document_id == document_id)
        .all()
    )

    if existing_chunks:
        return existing_chunks

    db_chunks = []

    for index, content in enumerate(chunks):
        chunk = create_document_chunk(
            db=db,
            document_id=document_id,
            chunk_index=index,
            content=content,
        )

        db_chunks.append(chunk)

    db.commit()

    for chunk in db_chunks:
        db.refresh(chunk)

    return db_chunks