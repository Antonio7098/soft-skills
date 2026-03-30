"""Add password auth to user accounts.

Revision ID: 20260330_0023
Revises: 20260330_0022
Create Date: 2026-03-30 11:15:00.000000

"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260330_0023"
down_revision = "20260330_0022"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "user_accounts",
        sa.Column("password_hash", sa.String(length=255), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("user_accounts", "password_hash")
