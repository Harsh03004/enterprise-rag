from datetime import UTC, datetime, timedelta
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.query_event import QueryEvent


def record_query_event(
    db: Session,
    user_id: int,
    status: str,
    latency_ms: int,
    provider: str,
    model: str | None = None,
    retrieval_count: int = 0,
    citation_count: int = 0,
    prompt_tokens: int = 0,
    completion_tokens: int = 0,
    fallback: bool = False,
    estimated_cost_usd: float = 0.0,
    cache_hit: bool = False,
    retrieval_latency_ms: int = 0,
    generation_latency_ms: int = 0,
    verification_latency_ms: int = 0,
) -> QueryEvent:
    event = QueryEvent(
        user_id=user_id,
        status=status,
        latency_ms=max(0, latency_ms),
        provider=provider,
        model=model,
        retrieval_count=max(0, retrieval_count),
        citation_count=max(0, citation_count),
        prompt_tokens=max(0, prompt_tokens),
        completion_tokens=max(0, completion_tokens),
        fallback=fallback,
        estimated_cost_usd=max(0.0, estimated_cost_usd),
        cache_hit=cache_hit,
        retrieval_latency_ms=max(0, retrieval_latency_ms),
        generation_latency_ms=max(0, generation_latency_ms),
        verification_latency_ms=max(0, verification_latency_ms),
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


def get_admin_analytics(db: Session, days: int = 30) -> dict:
    start = datetime.now(UTC) - timedelta(days=days)
    failed_count = func.count(QueryEvent.id).filter(QueryEvent.status != "completed")
    total, failed, fallback, cache_hits, retrieval_ms, generation_ms, verification_ms, average_ms, p95, retrieved, citations, prompt_tokens, completion_tokens, cost = db.execute(
        select(
            func.count(QueryEvent.id),
            failed_count,
            func.count(QueryEvent.id).filter(QueryEvent.fallback.is_(True)),
            func.count(QueryEvent.id).filter(QueryEvent.cache_hit.is_(True)),
            func.coalesce(func.avg(QueryEvent.retrieval_latency_ms), 0),
            func.coalesce(func.avg(QueryEvent.generation_latency_ms), 0),
            func.coalesce(func.avg(QueryEvent.verification_latency_ms), 0),
            func.coalesce(func.avg(QueryEvent.latency_ms), 0),
            func.percentile_disc(0.95).within_group(QueryEvent.latency_ms),
            func.coalesce(func.sum(QueryEvent.retrieval_count), 0),
            func.coalesce(func.sum(QueryEvent.citation_count), 0),
            func.coalesce(func.sum(QueryEvent.prompt_tokens), 0),
            func.coalesce(func.sum(QueryEvent.completion_tokens), 0),
            func.coalesce(func.sum(QueryEvent.estimated_cost_usd), 0),
        ).where(QueryEvent.created_at >= start)
    ).one()

    day = func.date(QueryEvent.created_at).label("date")
    daily_rows = db.execute(
        select(
            day,
            func.count(QueryEvent.id).label("queries"),
            failed_count.label("failures"),
            func.coalesce(func.avg(QueryEvent.latency_ms), 0).label("average_latency_ms"),
        )
        .where(QueryEvent.created_at >= start)
        .group_by(day)
        .order_by(day)
    ).all()
    daily = [
        {
            "date": value.isoformat() if hasattr(value, "isoformat") else str(value),
            "queries": int(queries or 0),
            "failures": int(day_failures or 0),
            "average_latency_ms": round(float(day_average or 0), 2),
        }
        for value, queries, day_failures, day_average in daily_rows
    ]

    normalized_model = func.coalesce(QueryEvent.model, "unknown")
    provider_rows = db.execute(
        select(
            QueryEvent.provider,
            normalized_model.label("model"),
            func.count(QueryEvent.id).label("queries"),
            failed_count.label("failures"),
            func.coalesce(func.avg(QueryEvent.latency_ms), 0).label("average_latency_ms"),
            func.coalesce(func.sum(QueryEvent.prompt_tokens), 0).label("prompt_tokens"),
            func.coalesce(func.sum(QueryEvent.completion_tokens), 0).label("completion_tokens"),
            func.coalesce(func.sum(QueryEvent.estimated_cost_usd), 0).label("estimated_cost_usd"),
        )
        .where(QueryEvent.created_at >= start)
        .group_by(QueryEvent.provider, normalized_model)
        .order_by(QueryEvent.provider, normalized_model)
    ).all()
    providers = [
        {
            "provider": provider,
            "model": model,
            "queries": int(queries or 0),
            "failures": int(provider_failures or 0),
            "average_latency_ms": round(float(provider_average or 0), 2),
            "prompt_tokens": int(provider_prompt_tokens or 0),
            "completion_tokens": int(provider_completion_tokens or 0),
            "estimated_cost_usd": round(float(provider_cost or 0), 6),
        }
        for provider, model, queries, provider_failures, provider_average,
        provider_prompt_tokens, provider_completion_tokens, provider_cost in provider_rows
    ]

    return {
        "days": days,
        "total_queries": int(total or 0),
        "failed_queries": int(failed or 0),
        "fallback_queries": int(fallback or 0),
        "cache_hits": int(cache_hits or 0),
        "retrieval_latency_ms": round(float(retrieval_ms or 0), 2),
        "generation_latency_ms": round(float(generation_ms or 0), 2),
        "verification_latency_ms": round(float(verification_ms or 0), 2),
        "average_latency_ms": round(float(average_ms or 0), 2),
        "p95_latency_ms": int(p95 or 0),
        "retrieved_chunks": int(retrieved or 0),
        "citations": int(citations or 0),
        "prompt_tokens": int(prompt_tokens or 0),
        "completion_tokens": int(completion_tokens or 0),
        "estimated_cost_usd": round(float(cost or 0), 6),
        "daily": daily,
        "providers": providers,
    }
