from __future__ import annotations

import argparse

from sqlalchemy import select

from app.core.config import settings
from app.db.session import SessionLocal
from app.models.document import Document
from app.services.document_processing import process_document


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Re-extract and re-embed documents using EMBEDDING_MODEL."
    )
    parser.add_argument("--user-id", type=int, default=None)
    parser.add_argument("--document-id", type=int, default=None)
    parser.add_argument(
        "--confirm-reindex",
        action="store_true",
        help="Required acknowledgement that existing chunk vectors will be replaced.",
    )
    args = parser.parse_args()
    if not args.confirm_reindex:
        parser.error("Pass --confirm-reindex after backing up the database and stopping API/worker services.")

    db = SessionLocal()
    failures = 0
    try:
        statement = select(Document).order_by(Document.id)
        if args.user_id is not None:
            statement = statement.where(Document.user_id == args.user_id)
        if args.document_id is not None:
            statement = statement.where(Document.id == args.document_id)
        documents = db.scalars(statement).all()
        if not documents:
            print("No matching documents found.")
            return

        print(f"Reindexing {len(documents)} documents with {settings.embedding_model}.")
        for number, document in enumerate(documents, start=1):
            print(f"[{number}/{len(documents)}] {document.id}: {document.filename}")
            try:
                count = process_document(db, document, rebuild_chunks=True)
                print(f"  Rebuilt {count} chunks.")
            except Exception as exc:
                failures += 1
                print(f"  FAILED: {exc}")
        print(f"Completed with {failures} failed documents.")
        if failures:
            raise SystemExit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
