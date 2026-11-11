"""persist evaluation runs for the admin dashboard

Revision ID: d9a84c1f2b70
Revises: c4e19b8a6d72
Create Date: 2026-10-09
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "d9a84c1f2b70"
down_revision: str | Sequence[str] | None = "c4e19b8a6d72"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("processing_jobs", sa.Column("rebuild_chunks", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.create_table(
        "app_settings",
        sa.Column("key", sa.String(length=100), primary_key=True),
        sa.Column("value", sa.JSON(), nullable=False),
    )
    op.add_column("query_events", sa.Column("model", sa.String(length=255), nullable=True))
    op.add_column("query_events", sa.Column("retrieval_count", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("query_events", sa.Column("citation_count", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("query_events", sa.Column("prompt_tokens", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("query_events", sa.Column("completion_tokens", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("query_events", sa.Column("fallback", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("query_events", sa.Column("estimated_cost_usd", sa.Float(), nullable=False, server_default="0"))
    op.add_column("query_events", sa.Column("cache_hit", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("query_events", sa.Column("retrieval_latency_ms", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("query_events", sa.Column("generation_latency_ms", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("query_events", sa.Column("verification_latency_ms", sa.Integer(), nullable=False, server_default="0"))
    op.create_table(
        "evaluation_runs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("dataset_name", sa.String(length=255), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("document_id", sa.Integer(), nullable=True),
        sa.Column("collection_id", sa.Integer(), nullable=True),
        sa.Column("provider", sa.String(length=50), nullable=False),
        sa.Column("model", sa.String(length=255), nullable=False),
        sa.Column("summary", sa.JSON(), nullable=False),
        sa.Column("results", sa.JSON(), nullable=False),
        sa.Column("case_errors", sa.JSON(), nullable=False),
        sa.Column("regression_failures", sa.JSON(), nullable=False),
        sa.Column("max_regression", sa.Float(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index("ix_evaluation_runs_created_at", "evaluation_runs", ["created_at"])


def downgrade() -> None:
    op.drop_column("processing_jobs", "rebuild_chunks")
    op.drop_column("query_events", "verification_latency_ms")
    op.drop_column("query_events", "generation_latency_ms")
    op.drop_column("query_events", "retrieval_latency_ms")
    op.drop_index("ix_evaluation_runs_created_at", table_name="evaluation_runs")
    op.drop_table("evaluation_runs")
    op.drop_table("app_settings")
    op.drop_column("query_events", "fallback")
    op.drop_column("query_events", "estimated_cost_usd")
    op.drop_column("query_events", "cache_hit")
    op.drop_column("query_events", "completion_tokens")
    op.drop_column("query_events", "prompt_tokens")
    op.drop_column("query_events", "citation_count")
    op.drop_column("query_events", "retrieval_count")
    op.drop_column("query_events", "model")
