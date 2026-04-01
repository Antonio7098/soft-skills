"""Add first-turn prompt text to scenarios.

Revision ID: 20260401_0035
Revises: 20260401_0034
Create Date: 2026-04-01 21:20:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260401_0035"
down_revision = "20260401_0034"
branch_labels = None
depends_on = None


def _default_prompt_text() -> str:
    return "Respond with the action or message you would deliver next."


def upgrade() -> None:
    op.add_column(
        "scenarios",
        sa.Column("prompt_text", sa.Text(), nullable=True),
    )
    bind = op.get_bind()
    bind.execute(
        sa.text(
            """
            UPDATE scenarios
            SET prompt_text = :default_prompt
            WHERE prompt_text IS NULL OR trim(prompt_text) = ''
            """
        ),
        {"default_prompt": _default_prompt_text()},
    )
    with op.batch_alter_table("scenarios") as batch_op:
        batch_op.alter_column("prompt_text", existing_type=sa.Text(), nullable=False)


def downgrade() -> None:
    with op.batch_alter_table("scenarios") as batch_op:
        batch_op.drop_column("prompt_text")
