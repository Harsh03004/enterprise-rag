"""make document file path nullable

Revision ID: a1d7ad146126
Revises: a977ff19951d
Create Date: 2026-08-27 19:29:13.580791

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1d7ad146126'
down_revision: Union[str, Sequence[str], None] = 'a977ff19951d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.alter_column(
        "documents",
        "file_path",
        existing_type=sa.String(length=500),
        nullable=True,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.alter_column(
        "documents",
        "file_path",
        existing_type=sa.String(length=500),
        nullable=False,
    )
