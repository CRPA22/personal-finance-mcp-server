"""Create currencies table and account_types table with seed data.

Revision ID: 006
Revises: 005
Create Date: 2026-06-08

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "006"
down_revision: Union[str, None] = "005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

CURRENCIES = [
    {"code": "PEN", "name": "Sol peruano",   "symbol": "S/"},
    {"code": "USD", "name": "Dólar americano","symbol": "$"},
    {"code": "EUR", "name": "Euro",           "symbol": "€"},
]

ACCOUNT_TYPES = [
    {"code": "checking",   "label": "Cuenta corriente"},
    {"code": "savings",    "label": "Cuenta de ahorros"},
    {"code": "investment", "label": "Inversiones"},
    {"code": "credit",     "label": "Tarjeta de crédito"},
    {"code": "cash",       "label": "Efectivo"},
]


def upgrade() -> None:
    # --- Tabla: currencies ---
    op.create_table(
        "currencies",
        sa.Column("code",   sa.String(3),  primary_key=True),
        sa.Column("name",   sa.String(100), nullable=False),
        sa.Column("symbol", sa.String(10),  nullable=False),
        sa.PrimaryKeyConstraint("code"),
    )

    conn = op.get_bind()
    conn.execute(
        sa.text("INSERT INTO currencies (code, name, symbol) VALUES (:code, :name, :symbol)"),
        CURRENCIES,
    )

    # --- Tabla: account_types ---
    op.create_table(
        "account_types",
        sa.Column("code",  sa.String(50),  primary_key=True),
        sa.Column("label", sa.String(100), nullable=False),
        sa.PrimaryKeyConstraint("code"),
    )

    conn.execute(
        sa.text("INSERT INTO account_types (code, label) VALUES (:code, :label)"),
        ACCOUNT_TYPES,
    )

    # --- FK en accounts.currency → currencies.code ---
    op.create_foreign_key(
        "fk_accounts_currency",
        "accounts",
        "currencies",
        ["currency"],
        ["code"],
    )

    # --- FK en accounts.type → account_types.code ---
    op.create_foreign_key(
        "fk_accounts_type",
        "accounts",
        "account_types",
        ["type"],
        ["code"],
    )


def downgrade() -> None:
    op.drop_constraint("fk_accounts_type",     "accounts", type_="foreignkey")
    op.drop_constraint("fk_accounts_currency", "accounts", type_="foreignkey")
    op.drop_table("account_types")
    op.drop_table("currencies")
