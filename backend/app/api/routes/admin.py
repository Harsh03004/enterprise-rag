# ruff: noqa: B008, I001

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_admin
from app.db.dependencies import get_db
from app.models.document import Document
from app.models.processing_job import ProcessingJob
from app.models.query_event import QueryEvent
from app.models.user import User


router = APIRouter(prefix="/admin", tags=["Administration"])


@router.get("/summary")
def admin_summary(
    _admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    users = db.scalar(select(func.count(User.id))) or 0
    documents = db.scalar(select(func.count(Document.id))) or 0
    jobs = db.scalar(select(func.count(ProcessingJob.id))) or 0
    queries, average_latency = db.execute(
        select(
            func.count(QueryEvent.id),
            func.coalesce(func.avg(QueryEvent.latency_ms), 0),
        )
    ).one()

    return {
        "users": int(users),
        "documents": int(documents),
        "processing_jobs": int(jobs),
        "queries": int(queries or 0),
        "average_query_latency_ms": round(float(average_latency or 0), 2),
    }


@router.get("/users")
def admin_users(
    _admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    users = db.scalars(select(User).order_by(User.created_at.desc())).all()
    return [
        {
            "id": user.id,
            "email": user.email,
            "username": user.username,
            "is_active": user.is_active,
            "created_at": user.created_at,
        }
        for user in users
    ]
