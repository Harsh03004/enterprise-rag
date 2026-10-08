from sqlalchemy.orm import Session

from app.models.document_chunk import DocumentChunk
from app.services.chunking import ChunkData


def create_document_chunk(
    db: Session,
    document_id: int,
    chunk_index: int,
    chunk_data: ChunkData,
) -> DocumentChunk:
    chunk = DocumentChunk(
        document_id=document_id,
        chunk_index=chunk_index,
        content=chunk_data.content,
        page_number=chunk_data.page_number,
        section_heading=chunk_data.section_heading,
        block_type=chunk_data.block_type,
        token_count=chunk_data.token_count,
    )

    db.add(chunk)

    return chunk


def create_document_chunks(
    db: Session,
    document_id: int,
    chunks: list[ChunkData],
) -> list[DocumentChunk]:

    existing_chunks = (
        db.query(DocumentChunk).filter(DocumentChunk.document_id == document_id).all()
    )

    if existing_chunks:
        return existing_chunks

    db_chunks = []

    for index, chunk_data in enumerate(chunks):
        chunk = create_document_chunk(
            db=db,
            document_id=document_id,
            chunk_index=index,
            chunk_data=chunk_data,
        )

        db_chunks.append(chunk)

    db.commit()

    for chunk in db_chunks:
        db.refresh(chunk)

    return db_chunks
