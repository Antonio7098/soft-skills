"""Add circuit breaker record for multi-worker deployments.

Revision ID: 20260327_0015
Revises: 20260327_0014
Create Date: 2026-03-27 13:00:00.000000

"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "20260327_0015"
down_revision = "20260327_0014"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "circuit_breakers",
        sa.Column("name", sa.String(length=128), primary_key=True),
        sa.Column("status", sa.String(length=32), nullable=False, index=True),
        sa.Column("failure_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_failure_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_failure_reason", sa.Text(), nullable=True),
        sa.Column("opened_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("circuit_breakers")
