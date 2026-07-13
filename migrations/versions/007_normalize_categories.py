"""Normalize transaction categories to Spanish and add missing categories.

Revision ID: 007
Revises: 006
Create Date: 2026-06-08

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "007"
down_revision: Union[str, None] = "006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Nuevas categorías a agregar
NEW_CATEGORIES = [
    {"name": "familia",    "type": "expense"},
    {"name": "familia",    "type": "income"},
    {"name": "electrónica","type": "expense"},
    {"name": "hogar",      "type": "expense"},
]

# Mapeo: (category_actual, type) → category_normalizada
MAPPINGS = [
    # Gastos
    ("accommodation",  "expense", "hotel"),
    ("education",      "expense", "educación"),
    ("electronics",    "expense", "electrónica"),
    ("entertainment",  "expense", "entretenimiento"),
    ("family",         "expense", "familia"),
    ("food",           "expense", "alimentación"),
    ("groceries",      "expense", "supermercado"),
    ("household",      "expense", "hogar"),
    ("other",          "expense", "otro"),
    ("phone",          "expense", "teléfono"),
    ("reimbursement",  "expense", "otro"),
    ("restaurants",    "expense", "restaurantes"),
    ("subscriptions",  "expense", "suscripciones"),
    ("transportation", "expense", "transporte"),
    # Ingresos
    ("family",         "income",  "familia"),
    ("reimbursement",  "income",  "reembolso"),
    ("salary",         "income",  "salario"),
]


def upgrade() -> None:
    conn = op.get_bind()

    # Insertar categorías faltantes
    conn.execute(
        sa.text("""
            INSERT INTO categories (id, name, type, is_default, created_at)
            VALUES (gen_random_uuid(), :name, :type, true, NOW() AT TIME ZONE 'UTC')
            ON CONFLICT (name, type) DO NOTHING
        """),
        NEW_CATEGORIES,
    )

    # Normalizar categorías en transacciones
    for old_cat, tx_type, new_cat in MAPPINGS:
        conn.execute(
            sa.text("""
                UPDATE transactions
                SET category = :new_cat
                WHERE category = :old_cat AND type = :tx_type
            """),
            {"old_cat": old_cat, "tx_type": tx_type, "new_cat": new_cat},
        )


def downgrade() -> None:
    conn = op.get_bind()

    # Revertir normalizaciones
    for old_cat, tx_type, new_cat in reversed(MAPPINGS):
        conn.execute(
            sa.text("""
                UPDATE transactions
                SET category = :old_cat
                WHERE category = :new_cat AND type = :tx_type
            """),
            {"old_cat": old_cat, "tx_type": tx_type, "new_cat": new_cat},
        )

    # Eliminar categorías agregadas
    for cat in NEW_CATEGORIES:
        conn.execute(
            sa.text("DELETE FROM categories WHERE name = :name AND type = :type"),
            cat,
        )
