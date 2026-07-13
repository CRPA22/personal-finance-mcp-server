"""Replace transactions.category VARCHAR with category_id UUID FK.

Populates category_id from existing category text + type matching categories table.

Revision ID: 009
Revises: 008
Create Date: 2026-06-08

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "009"
down_revision: Union[str, None] = "008"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()

    # 1. Agregar category_id nullable
    op.add_column(
        "transactions",
        sa.Column("category_id", postgresql.UUID(as_uuid=True), nullable=True),
    )

    # 2. Poblar category_id haciendo match por (name=category, type=transaction.type)
    #    Para transferencias: type='transfer' en categories
    conn.execute(sa.text("""
        UPDATE transactions t
        SET category_id = c.id
        FROM categories c
        WHERE c.name = t.category
          AND c.type = t.type
          AND c.user_id IS NULL
    """))

    # 3. Si quedó alguna sin match (categoría no encontrada), asignar 'otro' del mismo tipo
    #    Para expense y income
    conn.execute(sa.text("""
        UPDATE transactions t
        SET category_id = (
            SELECT c.id FROM categories c
            WHERE c.name = 'otro' AND c.type = t.type AND c.user_id IS NULL
            LIMIT 1
        )
        WHERE t.category_id IS NULL AND t.type IN ('income', 'expense')
    """))

    # 4. Para transferencias sin match → categoría 'transferencia'
    conn.execute(sa.text("""
        UPDATE transactions t
        SET category_id = (
            SELECT c.id FROM categories c
            WHERE c.name = 'transferencia' AND c.type = 'transfer' AND c.user_id IS NULL
            LIMIT 1
        )
        WHERE t.category_id IS NULL AND t.type = 'transfer'
    """))

    # 5. Hacer NOT NULL y agregar FK
    op.alter_column("transactions", "category_id", nullable=False)
    op.create_foreign_key(
        "fk_transactions_category_id",
        "transactions",
        "categories",
        ["category_id"],
        ["id"],
    )
    op.create_index("ix_transactions_category_id", "transactions", ["category_id"])

    # 6. Eliminar columna category VARCHAR (ya no se necesita)
    op.drop_column("transactions", "category")


def downgrade() -> None:
    conn = op.get_bind()

    # Restaurar columna category VARCHAR
    op.add_column(
        "transactions",
        sa.Column("category", sa.String(100), nullable=True),
    )

    # Repoblar category desde categories.name
    conn.execute(sa.text("""
        UPDATE transactions t
        SET category = c.name
        FROM categories c
        WHERE c.id = t.category_id
    """))

    op.alter_column("transactions", "category", nullable=False)

    op.drop_index("ix_transactions_category_id", table_name="transactions")
    op.drop_constraint("fk_transactions_category_id", "transactions", type_="foreignkey")
    op.drop_column("transactions", "category_id")
