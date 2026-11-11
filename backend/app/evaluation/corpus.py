"""Reproducible evaluation corpus.

The corpus files live in the repository. Before an evaluation run they are
ingested for a dedicated, login-disabled evaluation user through the same
storage and processing code used for real uploads, inside a single collection.

Ingestion is skipped when the stored fingerprint (file bytes plus chunking and
embedding settings) still matches, so repeated runs are fast; any change to the
files or those settings triggers a clean re-ingest.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import mimetypes
import secrets
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path

from fastapi import UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session
from starlette.datastructures import Headers

from app.core.config import settings
from app.core.security import hash_password
from app.crud.collection import create_collection
from app.crud.document import create_document, delete_document
from app.crud.user import get_user_by_email
from app.models.app_setting import AppSetting
from app.models.collection import Collection
from app.models.document import Document
from app.models.user import User
from app.services.document_processing import process_document
from app.services.document_service import save_uploaded_file
from app.services.rag_settings import get_rag_config

EVALUATION_USER_EMAIL = "rag-evaluation@example.com"
EVALUATION_USERNAME = "rag-evaluation"
EVALUATION_COLLECTION = "Evaluation corpus"
STATE_KEY = "evaluation_corpus"
# Bump when ingestion behaviour changes in a way the fingerprint cannot see.
INGESTION_VERSION = 1

CONTENT_TYPES = {".md": "text/markdown", ".txt": "text/plain"}


@dataclass
class CorpusScope:
    user_id: int
    collection_id: int
    document_ids: dict[str, int]
    reingested: bool


def corpus_fingerprint(corpus_dir: Path, filenames: list[str], rag_config: dict) -> str:
    digest = hashlib.sha256()
    digest.update(
        json.dumps(
            {
                "ingestion_version": INGESTION_VERSION,
                "chunk_size": rag_config.get("chunk_size"),
                "chunk_overlap": rag_config.get("chunk_overlap"),
                "embedding_model": settings.embedding_model,
                "files": sorted(filenames),
            },
            sort_keys=True,
        ).encode()
    )
    for name in sorted(filenames):
        digest.update(name.encode())
        digest.update(hashlib.sha256((corpus_dir / name).read_bytes()).digest())
    return digest.hexdigest()


def _evaluation_user(db: Session) -> User:
    user = get_user_by_email(db, EVALUATION_USER_EMAIL)
    if user is None:
        # A random, discarded password and is_active=False: this account only
        # owns evaluation documents and can never be used to sign in.
        user = User(
            email=EVALUATION_USER_EMAIL,
            username=EVALUATION_USERNAME,
            hashed_password=hash_password(secrets.token_urlsafe(32)),
            is_active=False,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    return user


def _evaluation_collection(db: Session, user_id: int) -> Collection:
    collection = db.scalar(
        select(Collection).where(
            Collection.user_id == user_id,
            Collection.name == EVALUATION_COLLECTION,
        )
    )
    return collection or create_collection(db, user_id=user_id, name=EVALUATION_COLLECTION)


def _ingest_file(db: Session, path: Path, user_id: int, collection_id: int) -> Document:
    content_type = CONTENT_TYPES.get(path.suffix.lower()) or (
        mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    )
    upload = UploadFile(
        file=BytesIO(path.read_bytes()),
        filename=path.name,
        headers=Headers({"content-type": content_type}),
    )
    file_path = asyncio.run(save_uploaded_file(upload, user_id=user_id))
    document = create_document(
        db,
        user_id=user_id,
        filename=path.name,
        content_type=content_type,
        file_path=file_path,
        collection_id=collection_id,
    )
    process_document(db, document)
    db.refresh(document)
    return document


def ensure_corpus(
    db: Session,
    corpus_dir: str | Path,
    filenames: list[str],
    reingest: bool = False,
    log=print,
) -> CorpusScope:
    """Make the evaluation collection hold exactly the given corpus files."""
    corpus_dir = Path(corpus_dir)
    missing = [name for name in filenames if not (corpus_dir / name).is_file()]
    if missing:
        raise FileNotFoundError(f"Corpus files not found in {corpus_dir}: {', '.join(missing)}")
    if not filenames:
        raise ValueError("The evaluation dataset does not list any corpus files.")

    user = _evaluation_user(db)
    collection = _evaluation_collection(db, user.id)
    fingerprint = corpus_fingerprint(corpus_dir, filenames, get_rag_config(db))

    documents = db.scalars(
        select(Document).where(Document.user_id == user.id)
    ).all()
    by_name = {document.filename: document for document in documents}
    state = db.get(AppSetting, STATE_KEY)
    current = (
        not reingest
        and state is not None
        and state.value.get("fingerprint") == fingerprint
        and set(by_name) == set(filenames)
        and all(
            document.status == "processed" and document.collection_id == collection.id
            for document in documents
        )
    )
    if current:
        log(f"Evaluation corpus up to date ({len(filenames)} documents, collection {collection.id}).")
        return CorpusScope(user.id, collection.id, {d.filename: d.id for d in documents}, False)

    log(f"Ingesting evaluation corpus ({len(filenames)} documents)...")
    for document in documents:
        delete_document(db, document_id=document.id, user_id=user.id)

    document_ids: dict[str, int] = {}
    for name in filenames:
        document = _ingest_file(db, corpus_dir / name, user.id, collection.id)
        document_ids[name] = document.id
        log(f"  {name}: document {document.id}, status {document.status}")

    value = {"fingerprint": fingerprint, "document_ids": document_ids, "collection_id": collection.id}
    if state is None:
        db.add(AppSetting(key=STATE_KEY, value=value))
    else:
        state.value = value
    db.commit()
    return CorpusScope(user.id, collection.id, document_ids, True)
