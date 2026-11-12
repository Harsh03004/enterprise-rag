# ruff: noqa: B008

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.core.config import is_admin_email
from app.core.security import hash_password, verify_password
from app.crud.user import get_user_by_username
from app.db.dependencies import get_db
from app.models.user import User
from app.schemas.user import CurrentUserResponse, PasswordChange, UsernameUpdate
from app.services.analytics import get_query_summary

router = APIRouter(
    prefix="/users",
    tags=["Users"],
)


@router.get(
    "/me",
    response_model=CurrentUserResponse,
)
def get_me(
    current_user: User = Depends(get_current_user),
):
    return {
        "id": current_user.id,
        "email": current_user.email,
        "username": current_user.username,
        "is_active": current_user.is_active,
        "created_at": current_user.created_at,
        "is_admin": is_admin_email(current_user.email),
    }


@router.get("/me/analytics")
def get_my_analytics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return get_query_summary(db=db, user_id=current_user.id)


@router.patch("/me", response_model=CurrentUserResponse)
def update_me(
    update: UsernameUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    username = update.username.strip()
    if len(username) < 3:
        raise HTTPException(status_code=422, detail="Username must be at least 3 characters.")
    existing = get_user_by_username(db, username)
    if existing is not None and existing.id != current_user.id:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="That username is already taken.")
    current_user.username = username
    db.commit()
    db.refresh(current_user)
    return get_me(current_user)


@router.post("/me/password", status_code=status.HTTP_204_NO_CONTENT)
def change_password(
    change: PasswordChange,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not verify_password(change.current_password, current_user.hashed_password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Current password is incorrect.")
    if change.new_password == change.current_password:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Choose a password different from the current one.")
    current_user.hashed_password = hash_password(change.new_password)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
