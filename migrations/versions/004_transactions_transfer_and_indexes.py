"""Add transfer support to transactions: user_id, transfer_peer_id, indexes.

Revision ID: 004
Revises: 003
Create Date: 2026-06-08

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "004"
down_revision: Union[str, None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- transactions: agregar user_id ---
    op.add_column(
        "transactions",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    # Poblar user_id desde la cuenta asociada
    op.execute(
        sa.text("""
            UPDATE transactions t
            SET user_id = a.user_id
            FROM accounts a
            WHERE t.account_id = a.id
        """)
    )
    op.alter_column("transactions", "user_id", nullable=False)
    op.create_foreign_key(
        "fk_transactions_user_id",
        "transactions",
        "users",
        ["user_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # --- transactions: agregar transfer_peer_id ---
    op.add_column(
        "transactions",
        sa.Column("transfer_peer_id", postgresql.UUID(as_uuid=True), nullable=True),
    )

    # --- Índices de rendimiento ---
    op.create_index("ix_accounts_user_id", "accounts", ["user_id"])
    op.create_index("ix_transactions_account_id", "transactions", ["account_id"])
    op.create_index("ix_transactions_user_id", "transactions", ["user_id"])
    op.create_index("ix_transactions_date", "transactions", ["date"])
    op.create_index("ix_audit_logs_user_id", "audit_logs", ["user_id"])
    op.create_index("ix_audit_logs_entity_type", "audit_logs", ["entity_type"])
    op.create_index("ix_audit_logs_created_at", "audit_logs", ["created_at"])

    # --- Migrar transferencias antiguas (category=transferencia + type=expense/income) ---
    # Las que tienen category='transferencia' pasan a type='transfer'
    op.execute(
        sa.text("""
            UPDATE transactions
            SET type = 'transfer'
            WHERE category = 'transferencia'
        """)
    )


def downgrade() -> None:
    # Revertir transferencias al tipo original según si su saldo es salida o entrada
    # (heurística: las que tienen transfer_peer_id nulo o par externo se dejan como expense)
    op.execute(
        sa.text("""
            UPDATE transactions
            SET type = 'expense'
            WHERE category = 'transferencia' AND type = 'transfer'
        """)
    )

    op.drop_index("ix_audit_logs_created_at", table_name="audit_logs")
    op.drop_index("ix_audit_logs_entity_type", table_name="audit_logs")
    op.drop_index("ix_audit_logs_user_id", table_name="audit_logs")
    op.drop_index("ix_transactions_date", table_name="transactions")
    op.drop_index("ix_transactions_user_id", table_name="transactions")
    op.drop_index("ix_transactions_account_id", table_name="transactions")
    op.drop_index("ix_accounts_user_id", table_name="accounts")

    op.drop_constraint("fk_transactions_user_id", "transactions", type_="foreignkey")
    op.drop_column("transactions", "transfer_peer_id")
    op.drop_column("transactions", "user_id")
