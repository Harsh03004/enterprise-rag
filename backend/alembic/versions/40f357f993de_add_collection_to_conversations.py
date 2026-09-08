"""add collection to conversations

Revision ID: 40f357f993de
Revises: 40c15ca2ce1f
Create Date: 2026-09-07 01:34:44.203053

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "40f357f993de"
down_revision: Union[str, Sequence[str], None] = "40c15ca2ce1f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "conversations",
        sa.Column(
            "collection_id",
            sa.Integer(),
            nullable=True,
        ),
    )

    op.create_index(
        "ix_conversations_collection_id",
        "conversations",
        ["collection_id"],
        unique=False,
    )

    op.create_foreign_key(
        "fk_conversations_collection_id_collections",
        "conversations",
        "collections",
        ["collection_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_conversations_collection_id_collections",
        "conversations",
        type_="foreignkey",
    )

    op.drop_index(
        "ix_conversations_collection_id",
        table_name="conversations",
    )

    op.drop_column(
        "conversations",
        "collection_id",
    )