from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.query_event import QueryEvent


def record_query_event(
    db: Session,
    user_id: int,
    status: str,
    latency_ms: int,
    provider: str,
) -> QueryEvent:
    event = QueryEvent(
        user_id=user_id,
        status=status,
        latency_ms=max(0, latency_ms),
        provider=provider,
    )
    db.add(event)
    db.commit()
    return event


def get_query_summary(db: Session, user_id: int) -> dict[str, float | int]:
    total, successful, average_latency = db.execute(
        select(
            func.count(QueryEvent.id),
            func.count(QueryEvent.id).filter(QueryEvent.status == "completed"),
            func.coalesce(func.avg(QueryEvent.latency_ms), 0),
        ).where(QueryEvent.user_id == user_id)
    ).one()

    return {
        "total_queries": int(total or 0),
        "successful_queries": int(successful or 0),
        "average_latency_ms": round(float(average_latency or 0), 2),
    }
