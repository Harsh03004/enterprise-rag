from fastapi import APIRouter, Depends, File, UploadFile, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.crud.document import create_document
from app.db.dependencies import get_db
from app.models.user import User
from app.schemas.document import DocumentResponse
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

    return document