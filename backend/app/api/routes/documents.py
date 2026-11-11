# ruff: noqa: B008

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    UploadFile,
    status,
)
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.crud.collection import get_collection
from app.crud.document import (
    create_document,
    delete_document,
    update_document_collection,
    update_document_filename,
)
from app.db.dependencies import get_db
from app.models.document import Document
from app.models.user import User
from app.schemas.document import (
    DocumentCollectionUpdate,
    DocumentResponse,
    DocumentUpdate,
    DocumentURLCreate,
)
from app.services.document_jobs import enqueue_document_processing
from app.services.document_service import (
    save_uploaded_file,
    validate_upload_filename,
)
from app.services.web_extraction import validate_url

router = APIRouter(
    prefix="/documents",
    tags=["Documents"],
)


@router.post(
    "/upload",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_document(
    file: UploadFile = File(...),
    collection_id: int | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        filename = validate_upload_filename(file.filename)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=str(exc),
        ) from exc

    if collection_id is not None:
        collection = get_collection(
            db=db,
            collection_id=collection_id,
            user_id=current_user.id,
        )

        if collection is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Collection not found.",
            )

    try:
        file_path = await save_uploaded_file(
            file=file,
            user_id=current_user.id,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=str(exc),
        ) from exc
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc

    document = create_document(
        db=db,
        user_id=current_user.id,
        filename=filename,
        content_type=file.content_type or "application/octet-stream",
        file_path=file_path,
        collection_id=collection_id,
    )

    try:
        enqueue_document_processing(db=db, document=document)
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc

    return document


@router.post(
    "/url",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
)
def ingest_url(
    request: DocumentURLCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    collection_id: int | None = None,
):
    url = request.url.strip()

    if not url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="URL cannot be empty.",
        )

    try:
        validate_url(url)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    if collection_id is not None:
        collection = get_collection(
            db=db,
            collection_id=collection_id,
            user_id=current_user.id,
        )

        if collection is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Collection not found.",
            )

    document = create_document(
        db=db,
        user_id=current_user.id,
        filename=url,
        content_type="text/html",
        file_path=None,
        source_url=url,
        collection_id=collection_id,
    )

    try:
        enqueue_document_processing(db=db, document=document)
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc

    return document


@router.get(
    "",
    response_model=list[DocumentResponse],
)
def list_documents(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    documents = db.scalars(
        select(Document)
        .where(Document.user_id == current_user.id)
        .order_by(Document.created_at.desc())
    ).all()

    return documents


@router.post(
    "/{document_id}/retry",
    response_model=DocumentResponse,
)
def retry_document_processing(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    document = db.scalars(
        select(Document).where(
            Document.id == document_id,
            Document.user_id == current_user.id,
        )
    ).first()

    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found.",
        )

    if document.status == "processing":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Document is already being processed.",
        )

    try:
        enqueue_document_processing(db=db, document=document)
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc

    return document


@router.patch(
    "/{document_id}",
    response_model=DocumentResponse,
)
def rename_document(
    document_id: int,
    request: DocumentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    filename = request.filename.strip()

    if not filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Document name cannot be empty.",
        )

    document = update_document_filename(
        db=db,
        document_id=document_id,
        user_id=current_user.id,
        filename=filename,
    )

    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found.",
        )

    return document


@router.delete(
    "/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def remove_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    deleted = delete_document(
        db=db,
        document_id=document_id,
        user_id=current_user.id,
    )

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found.",
        )


@router.patch(
    "/{document_id}/collection",
    response_model=DocumentResponse,
)
def update_document_collection_route(
    document_id: int,
    request: DocumentCollectionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    document = db.scalars(
        select(Document).where(
            Document.id == document_id,
            Document.user_id == current_user.id,
        )
    ).first()

    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found.",
        )

    if request.collection_id is not None:
        collection = get_collection(
            db=db,
            collection_id=request.collection_id,
            user_id=current_user.id,
        )

        if collection is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Collection not found.",
            )

    updated_document = update_document_collection(
        db=db,
        document_id=document_id,
        user_id=current_user.id,
        collection_id=request.collection_id,
    )

    if updated_document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found.",
        )

    return updated_document
