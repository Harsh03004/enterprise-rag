from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.jwt import create_access_token
from app.core.security import verify_password
from app.crud.user import create_user, get_user_by_email, get_user_by_username
from app.db.dependencies import get_db
from app.schemas.auth import LoginRequest, Token
from app.schemas.user import UserCreate, UserResponse

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def register_user(
    user: UserCreate,
    db: Session = Depends(get_db),
):
    existing_user = get_user_by_email(db, user.email)
    if existing_user or get_user_by_username(db, user.username):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email or username is already registered.",
        )

    try:
        return create_user(db, user)
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email or username is already registered.",
        ) from exc


@router.post(
    "/login",
    response_model=Token,
)
def login(
    credentials: LoginRequest,
    db: Session = Depends(get_db),
):
    user = get_user_by_email(db, credentials.email)

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not verify_password(
        credentials.password,
        user.hashed_password,
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    access_token = create_access_token(
        data={
            "sub": str(user.id),
        }
    )

    return Token(
        access_token=access_token,
        token_type="bearer",
    )
