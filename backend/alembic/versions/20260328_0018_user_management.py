"""Add is_active to user_accounts.

Revision ID: 20260328_0018_user_management
Revises: 20260328_0017_prompt_library
Create Date: 2026-03-28

"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260328_0018_user_management"
down_revision = "20260328_0017"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "user_accounts",
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
    )


def downgrade() -> None:
    op.drop_column("user_accounts", "is_active")
