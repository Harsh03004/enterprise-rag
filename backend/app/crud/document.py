from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.document import Document


def create_document(
    db: Session,
    user_id: int,
    filename: str,
    content_type: str,
    file_path: str,
) -> Document:
    document = Document(
        user_id=user_id,
        filename=filename,
        content_type=content_type,
        file_path=file_path,
        status="uploaded",
    )

    db.add(document)
    db.commit()
    db.refresh(document)

    return document


def get_document(
    db: Session,
    document_id: int,
    user_id: int,
) -> Document | None:
    statement = select(Document).where(
        Document.id == document_id,
        Document.user_id == user_id,
    )

    return db.scalar(statement)


def update_document_filename(
    db: Session,
    document_id: int,
    user_id: int,
    filename: str,
) -> Document | None:
    document = get_document(
        db=db,
        document_id=document_id,
        user_id=user_id,
    )

    if document is None:
        return None

    document.filename = filename

    db.commit()
    db.refresh(document)

    return document


def delete_document(
    db: Session,
    document_id: int,
    user_id: int,
) -> bool:
    document = get_document(
        db=db,
        document_id=document_id,
        user_id=user_id,
    )

    if document is None:
        return False

    db.delete(document)
    db.commit()

    return True