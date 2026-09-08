"""add processing error to documents

Revision ID: 40c15ca2ce1f
Revises: a18d5c70bed4
Create Date: 2026-09-05 00:16:26.385559

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "40c15ca2ce1f"
down_revision: Union[str, Sequence[str], None] = "a18d5c70bed4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "documents",
        sa.Column(
            "processing_error",
            sa.Text(),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column(
        "documents",
        "processing_error",
    )