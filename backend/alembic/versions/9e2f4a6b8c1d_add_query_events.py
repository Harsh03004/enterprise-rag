"""add query analytics events

Revision ID: 9e2f4a6b8c1d
Revises: 8d1e3f5a7b2c
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "9e2f4a6b8c1d"
down_revision: str | Sequence[str] | None = "8d1e3f5a7b2c"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "query_events",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("latency_ms", sa.Integer(), nullable=False),
        sa.Column("provider", sa.String(length=50), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_query_events_user_id", "query_events", ["user_id"], unique=False
    )
    op.create_index(
        "ix_query_events_created_at", "query_events", ["created_at"], unique=False
    )


def downgrade() -> None:
    op.drop_index("ix_query_events_created_at", table_name="query_events")
    op.drop_index("ix_query_events_user_id", table_name="query_events")
    op.drop_table("query_events")
