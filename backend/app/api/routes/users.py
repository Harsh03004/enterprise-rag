# ruff: noqa: B008

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.db.dependencies import get_db
from app.models.user import User
from app.schemas.user import UserResponse
from app.services.analytics import get_query_summary

router = APIRouter(
    prefix="/users",
    tags=["Users"],
)


@router.get(
    "/me",
    response_model=UserResponse,
)
def get_me(
    current_user: User = Depends(get_current_user),
):
    return current_user


@router.get("/me/analytics")
def get_my_analytics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return get_query_summary(db=db, user_id=current_user.id)
