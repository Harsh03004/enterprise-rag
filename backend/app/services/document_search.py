import re

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.document import Document


def extract_document_reference(question: str) -> str | None:
    patterns = [
        r"\bassignment\s+\d+\b",
        r"\bassignment\s+\d+\s+pdf\b",
    ]

    for pattern in patterns:
        match = re.search(pattern, question, re.IGNORECASE)

        if match:
            return match.group(0)

    return None


def find_documents(
    db: Session,
    user_id: int,
    query: str,
    limit: int = 5,
):
    search_term = f"%{query.strip()}%"

    statement = (
        select(Document)
        .where(
            Document.user_id == user_id,
            Document.filename.ilike(search_term),
        )
        .order_by(Document.created_at.desc())
        .limit(limit)
    )

    return db.scalars(statement).all()