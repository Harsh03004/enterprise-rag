"""store cited source metadata with assistant messages

Revision ID: c4e19b8a6d72
Revises: 9e2f4a6b8c1d
Create Date: 2026-10-08

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "c4e19b8a6d72"
down_revision: str | Sequence[str] | None = "9e2f4a6b8c1d"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "messages",
        sa.Column(
            "sources",
            sa.JSON(),
            nullable=False,
            server_default=sa.text("'[]'::json"),
        ),
    )


def downgrade() -> None:
    op.drop_column("messages", "sources")
