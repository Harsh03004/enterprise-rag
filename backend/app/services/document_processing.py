from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.crud.document_chunk import create_document_chunks
from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.services.chunking import chunk_text_with_metadata
from app.services.embedding import generate_embedding
from app.services.text_extraction import extract_text_blocks
from app.services.web_extraction import extract_webpage_text


def process_document(db: Session, document: Document) -> int:
    document.status = "processing"
    document.processing_error = None
    db.commit()

    try:
        # ---------------------------------------------------------
        # Extract text
        # ---------------------------------------------------------

        if document.source_url:
            text_blocks = [(extract_webpage_text(document.source_url), None)]
        else:
            if not document.file_path:
                raise ValueError("Document has no file path or source URL.")

            text_blocks = extract_text_blocks(document.file_path)

        if not any(text.strip() for text, _page_number in text_blocks):
            raise ValueError("Document contains no extractable text.")

        # ---------------------------------------------------------
        # Chunk text
        # ---------------------------------------------------------

        chunks = [
            chunk
            for text, page_number in text_blocks
            for chunk in chunk_text_with_metadata(
                text,
                page_number=page_number,
            )
        ]

        if not chunks:
            raise ValueError("Document produced no chunks.")

        # ---------------------------------------------------------
        # Create chunks
        # ---------------------------------------------------------

        db_chunks = create_document_chunks(
            db=db,
            document_id=document.id,
            chunks=chunks,
        )

        # ---------------------------------------------------------
        # Generate embeddings
        # ---------------------------------------------------------

        embedded_count = 0

        for chunk in db_chunks:
            if chunk.embedding is None:
                chunk.embedding = generate_embedding(chunk.content)
                embedded_count += 1

        db.commit()

        # ---------------------------------------------------------
        # Mark processed
        # ---------------------------------------------------------

        document.status = "processed"
        document.processing_error = None
        db.commit()

        print(
            f"Processed document {document.id}: "
            f"{len(db_chunks)} chunks, "
            f"{embedded_count} embeddings"
        )

        return len(db_chunks)

    except Exception as exc:
        # ---------------------------------------------------------
        # Roll back the current transaction first.
        # ---------------------------------------------------------

        db.rollback()

        # ---------------------------------------------------------
        # Remove chunks created by this processing attempt.
        # ---------------------------------------------------------

        try:
            db.query(DocumentChunk).filter(
                DocumentChunk.document_id == document.id
            ).delete(synchronize_session=False)

            db.commit()

        except SQLAlchemyError:
            db.rollback()

        # ---------------------------------------------------------
        # Reload the document after rollback.
        # ---------------------------------------------------------

        reloaded_document = db.get(
            Document,
            document.id,
        )

        if reloaded_document is not None:
            reloaded_document.status = "failed"
            reloaded_document.processing_error = str(exc)

            db.commit()

        raise
