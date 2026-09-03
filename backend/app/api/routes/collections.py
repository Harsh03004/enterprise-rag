from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.crud.collection import (
    create_collection,
    delete_collection,
    get_collections,
    update_collection,
)
from app.db.dependencies import get_db
from app.models.user import User
from app.schemas.collection import (
    CollectionCreate,
    CollectionResponse,
    CollectionUpdate,
)


router = APIRouter(
    prefix="/collections",
    tags=["Collections"],
)


@router.post(
    "",
    response_model=CollectionResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_new_collection(
    request: CollectionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    name = request.name.strip()

    if not name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Collection name cannot be empty.",
        )

    return create_collection(
        db=db,
        user_id=current_user.id,
        name=name,
    )


@router.get(
    "",
    response_model=list[CollectionResponse],
)
def list_user_collections(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return get_collections(
        db=db,
        user_id=current_user.id,
    )


@router.patch(
    "/{collection_id}",
    response_model=CollectionResponse,
)
def rename_collection(
    collection_id: int,
    request: CollectionUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    name = request.name.strip()

    if not name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Collection name cannot be empty.",
        )

    collection = update_collection(
        db=db,
        collection_id=collection_id,
        user_id=current_user.id,
        name=name,
    )

    if collection is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Collection not found.",
        )

    return collection


@router.delete(
    "/{collection_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def remove_collection(
    collection_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    deleted = delete_collection(
        db=db,
        collection_id=collection_id,
        user_id=current_user.id,
    )

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Collection not found.",
        )

    return None