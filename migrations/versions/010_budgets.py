"""Create budgets and budget_alerts tables.

Revision ID: 010
Revises: 009
Create Date: 2026-06-08

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "010"
down_revision: Union[str, None] = "009"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "budgets",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("category_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("month", sa.Date(), nullable=False),          # primer día del mes: 2025-06-01
        sa.Column("limit_amount", sa.Numeric(15, 2), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False, server_default="PEN"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["category_id"], ["categories.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["currency"], ["currencies.code"]),
        sa.UniqueConstraint("user_id", "category_id", "month", name="uq_budget_user_category_month"),
    )
    op.create_index("ix_budgets_user_id", "budgets", ["user_id"])
    op.create_index("ix_budgets_month", "budgets", ["month"])

    op.create_table(
        "budget_alerts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("budget_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("threshold_percent", sa.Integer(), nullable=False),   # ej: 80 → alerta al 80%
        sa.Column("triggered_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["budget_id"], ["budgets.id"], ondelete="CASCADE"),
        sa.CheckConstraint("threshold_percent BETWEEN 1 AND 100", name="ck_threshold_percent"),
    )


def downgrade() -> None:
    op.drop_table("budget_alerts")
    op.drop_index("ix_budgets_month", table_name="budgets")
    op.drop_index("ix_budgets_user_id", table_name="budgets")
    op.drop_table("budgets")
