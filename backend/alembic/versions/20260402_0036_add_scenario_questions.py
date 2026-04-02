"""Add questions array to scenarios.

Revision ID: 20260402_0036
Revises: 20260401_0035
Create Date: 2026-04-02 10:00:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260402_0036"
down_revision = "20260401_0035"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "scenarios",
        sa.Column("questions", sa.JSON(), nullable=False, server_default="[]"),
    )


def downgrade() -> None:
    with op.batch_alter_table("scenarios") as batch_op:
        batch_op.drop_column("questions")
