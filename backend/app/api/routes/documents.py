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
from app.crud.document import (
    create_document,
    delete_document,
    update_document_filename,
)
from app.db.dependencies import get_db
from app.models.document import Document
from app.models.user import User
from app.schemas.document import (
    DocumentResponse,
    DocumentUpdate,
)
from app.services.document_processing import process_document
from app.services.document_service import save_uploaded_file


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
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    file_path = await save_uploaded_file(
        file=file,
        user_id=current_user.id,
    )

    document = create_document(
        db=db,
        user_id=current_user.id,
        filename=file.filename,
        content_type=file.content_type,
        file_path=file_path,
    )

    process_document(
        db=db,
        document=document,
    )

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
        .where(
            Document.user_id == current_user.id
        )
        .order_by(
            Document.created_at.desc()
        )
    ).all()

    return documents


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

    return None