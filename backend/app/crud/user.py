from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.user import User
from app.schemas.user import UserCreate


def get_user_by_email(db: Session, email: str) -> User | None:
    statement = select(User).where(func.lower(User.email) == email.strip().lower())
    return db.scalar(statement)


def get_user_by_username(db: Session, username: str) -> User | None:
    statement = select(User).where(User.username == username)
    return db.scalar(statement)


def create_user(db: Session, user: UserCreate) -> User:
    db_user = User(
        email=user.email.strip().lower(),
        username=user.username,
        hashed_password=hash_password(user.password),
    )

    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return db_user
