# ruff: noqa: B008, I001

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_admin
from app.core.config import is_admin_email
from app.db.dependencies import get_db
from app.models.document import Document
from app.models.evaluation_run import EvaluationRun
from app.models.processing_job import ProcessingJob
from app.models.query_event import QueryEvent
from app.models.user import User
from app.services.analytics import get_admin_analytics
from app.services.rag_settings import get_rag_config, save_rag_config


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
            "can_change_status": user.id != _admin.id and not is_admin_email(user.email),
            "created_at": user.created_at,
        }
        for user in users
    ]


def validate_user_status_change(admin: User, target: User, is_active: bool) -> None:
    if is_active:
        return
    if target.id == admin.id or is_admin_email(target.email):
        raise HTTPException(
            status_code=403,
            detail="Administrator accounts cannot be deactivated here.",
        )


@router.patch("/users/{user_id}/status")
def update_admin_user_status(
    user_id: int,
    is_active: bool = Body(..., embed=True),
    _admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found.")
    validate_user_status_change(_admin, user, is_active)
    user.is_active = is_active
    db.commit()
    db.refresh(user)
    return {
        "id": user.id,
        "email": user.email,
        "username": user.username,
        "is_active": user.is_active,
        "can_change_status": user.id != _admin.id and not is_admin_email(user.email),
        "created_at": user.created_at,
    }


@router.get("/analytics")
def admin_analytics(
    days: int = Query(default=30, ge=1, le=365),
    _admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    return get_admin_analytics(db, days=days)


@router.get("/settings/rag")
def read_rag_settings(
    _admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    return get_rag_config(db)


@router.patch("/settings/rag")
def update_rag_settings(
    updates: dict = Body(...),
    _admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    try:
        return save_rag_config(db, updates)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


def _evaluation_run_payload(run: EvaluationRun, include_results: bool = False) -> dict:
    payload = {
        "id": run.id,
        "dataset_name": run.dataset_name,
        "user_id": run.user_id,
        "document_id": run.document_id,
        "collection_id": run.collection_id,
        "provider": run.provider,
        "model": run.model,
        "summary": run.summary,
        "case_errors": run.case_errors,
        "status": "incomplete" if run.case_errors else "completed",
        "regression_failures": run.regression_failures,
        "max_regression": run.max_regression,
        "created_at": run.created_at,
    }
    if include_results:
        payload["results"] = run.results
    return payload


@router.get("/evaluations")
def list_evaluation_runs(
    limit: int = Query(default=50, ge=1, le=200),
    _admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    runs = db.scalars(
        select(EvaluationRun).order_by(EvaluationRun.created_at.desc()).limit(limit)
    ).all()
    return [_evaluation_run_payload(run) for run in runs]


@router.get("/evaluations/{run_id}")
def get_evaluation_run(
    run_id: int,
    _admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    run = db.get(EvaluationRun, run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Evaluation run not found.")
    return _evaluation_run_payload(run, include_results=True)
