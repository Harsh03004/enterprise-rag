"""add structured metadata to document chunks

Revision ID: 7c0b8d0c9e1a
Revises: 40f357f993de
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "7c0b8d0c9e1a"
down_revision: str | Sequence[str] | None = "40f357f993de"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "document_chunks", sa.Column("page_number", sa.Integer(), nullable=True)
    )
    op.add_column(
        "document_chunks",
        sa.Column("section_heading", sa.String(length=500), nullable=True),
    )
    op.add_column(
        "document_chunks", sa.Column("block_type", sa.String(length=50), nullable=True)
    )
    op.add_column(
        "document_chunks", sa.Column("token_count", sa.Integer(), nullable=True)
    )


def downgrade() -> None:
    op.drop_column("document_chunks", "token_count")
    op.drop_column("document_chunks", "block_type")
    op.drop_column("document_chunks", "section_heading")
    op.drop_column("document_chunks", "page_number")
