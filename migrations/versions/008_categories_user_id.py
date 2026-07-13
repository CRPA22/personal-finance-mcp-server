"""Add user_id to categories for custom per-user categories.

Revision ID: 008
Revises: 007
Create Date: 2026-06-08

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "008"
down_revision: Union[str, None] = "007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Eliminar índice único anterior (name, type)
    op.drop_index("ix_categories_name_type", table_name="categories")

    # Agregar user_id nullable (NULL = categoría del sistema)
    op.add_column(
        "categories",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_categories_user_id",
        "categories",
        "users",
        ["user_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # Nuevo índice único: (name, type, user_id) — permite mismo nombre para distintos usuarios
    op.create_index(
        "ix_categories_name_type_user",
        "categories",
        ["name", "type", "user_id"],
        unique=True,
    )
    op.create_index("ix_categories_user_id", "categories", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_categories_user_id", table_name="categories")
    op.drop_index("ix_categories_name_type_user", table_name="categories")
    op.drop_constraint("fk_categories_user_id", "categories", type_="foreignkey")
    op.drop_column("categories", "user_id")
    op.create_index(
        "ix_categories_name_type",
        "categories",
        ["name", "type"],
        unique=True,
    )
