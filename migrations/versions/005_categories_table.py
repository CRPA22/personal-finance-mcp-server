"""Create categories table with default data.

Revision ID: 005
Revises: 004
Create Date: 2026-06-08

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "005"
down_revision: Union[str, None] = "004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

EXPENSE_CATEGORIES = [
    "alimentación",
    "supermercado",
    "restaurantes",
    "transporte",
    "combustible",
    "vivienda",
    "alquiler",
    "servicios",
    "electricidad",
    "agua",
    "internet",
    "teléfono",
    "entretenimiento",
    "streaming",
    "cine",
    "suscripciones",
    "salud",
    "farmacia",
    "medicamentos",
    "educación",
    "ropa",
    "regalos",
    "donaciones",
    "viajes",
    "hotel",
    "seguros",
    "impuestos",
    "otro",
]

INCOME_CATEGORIES = [
    "salario",
    "freelance",
    "inversiones",
    "dividendos",
    "intereses",
    "alquiler_ingreso",
    "regalo",
    "reembolso",
    "venta",
    "otro",
]

TRANSFER_CATEGORIES = [
    "transferencia",
]


def upgrade() -> None:
    op.create_table(
        "categories",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("type", sa.String(20), nullable=False),
        sa.Column("is_default", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint("type IN ('income', 'expense', 'transfer')", name="ck_categories_type"),
    )
    op.create_index("ix_categories_type", "categories", ["type"])
    op.create_index(
        "ix_categories_name_type",
        "categories",
        ["name", "type"],
        unique=True,
    )

    # Seed de datos
    conn = op.get_bind()

    rows = []
    for name in EXPENSE_CATEGORIES:
        rows.append({"name": name, "type": "expense"})
    for name in INCOME_CATEGORIES:
        rows.append({"name": name, "type": "income"})
    for name in TRANSFER_CATEGORIES:
        rows.append({"name": name, "type": "transfer"})

    conn.execute(
        sa.text("""
            INSERT INTO categories (id, name, type, is_default, created_at)
            VALUES (gen_random_uuid(), :name, :type, true, NOW() AT TIME ZONE 'UTC')
            ON CONFLICT DO NOTHING
        """),
        rows,
    )


def downgrade() -> None:
    op.drop_index("ix_categories_name_type", table_name="categories")
    op.drop_index("ix_categories_type", table_name="categories")
    op.drop_table("categories")
