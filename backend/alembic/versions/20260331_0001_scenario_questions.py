"""add_scenario_questions

Add authored questions to scenarios for multi-question practice expansion.

Revision ID: scenario_questions
Revises: sprint15_phase3
Create Date: 2026-03-31

"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "scenario_questions"
down_revision = "sprint15_phase3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    connection = op.get_bind()
    result = connection.execute(
        sa.text("SELECT name FROM pragma_table_info('scenarios') WHERE name='questions'")
    )
    if result.fetchone() is None:
        connection.execute(
            sa.text("ALTER TABLE scenarios ADD COLUMN questions JSON NOT NULL DEFAULT '[]'")
        )
    connection.commit()


def downgrade() -> None:
    connection = op.get_bind()
    connection.execute(sa.text("ALTER TABLE scenarios DROP COLUMN questions"))
    connection.commit()
