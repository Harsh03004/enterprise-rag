from sqlalchemy.orm import Session

from app.crud.document_chunk import create_document_chunks
from app.models.document import Document
from app.services.chunking import chunk_text
from app.services.embedding import generate_embedding
from app.services.text_extraction import extract_text


def process_document(
    db: Session,
    document: Document,
) -> int:
    document.status = "processing"
    db.commit()

    try:
        text = extract_text(document.file_path)

        if not text.strip():
            raise ValueError(
                "Document contains no extractable text"
            )

        chunks = chunk_text(text)

        db_chunks = create_document_chunks(
            db=db,
            document_id=document.id,
            chunks=chunks,
        )

        embedded_count = 0

        for chunk in db_chunks:
            if chunk.embedding is None:
                chunk.embedding = generate_embedding(
                    chunk.content
                )
                embedded_count += 1

        db.commit()

        document.status = "processed"
        db.commit()

        print(f"Embedded {embedded_count} chunks")

        return len(db_chunks)

    except Exception:
        document.status = "failed"
        db.commit()
        raise