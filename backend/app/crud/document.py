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