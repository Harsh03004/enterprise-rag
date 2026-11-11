from sqlalchemy.orm import Session

from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.services.chunking import chunk_text_with_metadata
from app.services.document_service import materialize_uploaded_file
from app.services.embedding import generate_embedding
from app.services.rag_settings import get_rag_config
from app.services.text_extraction import extract_text_blocks
from app.services.web_extraction import extract_webpage_text


def process_document(db: Session, document: Document, rebuild_chunks: bool = False) -> int:
    document.status = "processing"
    document.processing_error = None
    db.commit()

    try:
        rag_config = get_rag_config(db)
        existing_chunks = (
            db.query(DocumentChunk)
            .filter(DocumentChunk.document_id == document.id)
            .order_by(DocumentChunk.chunk_index)
            .all()
        )

        if existing_chunks and not rebuild_chunks:
            # Recover partially embedded legacy documents without reparsing or
            # replacing their chunk content.
            db_chunks = existing_chunks
            embedded_count = 0
            for chunk in db_chunks:
                if chunk.embedding is None:
                    chunk.embedding = generate_embedding(chunk.content)
                    embedded_count += 1
        else:
            # Stage extraction, chunking, and every vector before touching the
            # currently searchable rows. A failed reindex therefore leaves the
            # previous chunks intact.
            if document.source_url:
                text_blocks = [(extract_webpage_text(document.source_url), None)]
            else:
                if not document.file_path:
                    raise ValueError("Document has no file path or source URL.")

                with materialize_uploaded_file(document.file_path) as local_path:
                    text_blocks = extract_text_blocks(local_path)

            if not any(text.strip() for text, _page_number in text_blocks):
                raise ValueError("Document contains no extractable text.")

            chunks = [
                chunk
                for text, page_number in text_blocks
                for chunk in chunk_text_with_metadata(
                    text,
                    chunk_size=int(rag_config["chunk_size"]),
                    chunk_overlap=int(rag_config["chunk_overlap"]),
                    page_number=page_number,
                )
            ]
            if not chunks:
                raise ValueError("Document produced no chunks.")

            db_chunks = []
            for index, chunk_data in enumerate(chunks):
                chunk = DocumentChunk(
                    document_id=document.id,
                    chunk_index=index,
                    content=chunk_data.content,
                    page_number=chunk_data.page_number,
                    section_heading=chunk_data.section_heading,
                    block_type=chunk_data.block_type,
                    token_count=chunk_data.token_count,
                )
                chunk.embedding = generate_embedding(chunk.content)
                db_chunks.append(chunk)
            embedded_count = len(db_chunks)

            if rebuild_chunks:
                db.query(DocumentChunk).filter(
                    DocumentChunk.document_id == document.id
                ).delete(synchronize_session=False)
            db.add_all(db_chunks)

        # Commit the new chunk set and processed status together. When replacing
        # rows, PostgreSQL applies the delete and inserts atomically.
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
