"""Seed default user for development.

Revision ID: 002
Revises: 001
Create Date: 2025-02-19

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    conn = op.get_bind()
    conn.execute(
        sa.text("""
            INSERT INTO users (id, email, hashed_password, role, created_at)
            VALUES (
                '00000000-0000-0000-0000-000000000001'::uuid,
                'default@finance-mcp.local',
                'unused-placeholder',
                'user',
                NOW() AT TIME ZONE 'UTC'
            )
            ON CONFLICT (id) DO NOTHING
        """)
    )


def downgrade() -> None:
    op.execute(
        sa.text("DELETE FROM users WHERE id = '00000000-0000-0000-0000-000000000001'::uuid")
    )
