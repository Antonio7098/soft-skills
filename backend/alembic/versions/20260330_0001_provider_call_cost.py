"""Add cost tracking to provider_calls.

Revision ID: 20260330_0001
Revises: 20260326_0007
Create Date: 2026-03-30 00:00:00.000000

"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260330_0001"
down_revision = "20260326_0007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "provider_calls",
        sa.Column("prompt_tokens", sa.Integer(), server_default="0", nullable=False),
    )
    op.add_column(
        "provider_calls",
        sa.Column("completion_tokens", sa.Integer(), server_default="0", nullable=False),
    )
    op.add_column("provider_calls", sa.Column("cost_usd", sa.Float(), nullable=True))


def downgrade() -> None:
    op.drop_column("provider_calls", "cost_usd")
    op.drop_column("provider_calls", "completion_tokens")
    op.drop_column("provider_calls", "prompt_tokens")
