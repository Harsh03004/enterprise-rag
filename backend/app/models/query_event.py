from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class QueryEvent(Base):
    __tablename__ = "query_events"

    id: Mapped[int] = mapped_column(primary_key=True)

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    status: Mapped[str] = mapped_column(String(30), nullable=False)
    latency_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    provider: Mapped[str] = mapped_column(String(50), nullable=False)
    model: Mapped[str | None] = mapped_column(String(255), nullable=True)
    retrieval_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    citation_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    prompt_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    completion_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    fallback: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    estimated_cost_usd: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    cache_hit: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    retrieval_latency_ms: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    generation_latency_ms: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    verification_latency_ms: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )
