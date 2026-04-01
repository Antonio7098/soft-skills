"""increase prompt id length to 64

Revision ID: increase_prompt_id_64
Revises: sprint15_phase3
Create Date: 2026-04-01

"""

from __future__ import annotations

from alembic import context as _context
from alembic import op

revision = "increase_prompt_id_64"
down_revision = "sprint15_phase3"
branch_labels = None
depends_on = None


def _is_postgres() -> bool:
    return _context.get_context().dialect.name == "postgresql"


def upgrade() -> None:
    # Increase prompt ID length from 32 to 64 chars
    # Only needed for PostgreSQL - SQLite doesn't enforce VARCHAR length
    if _is_postgres():
        op.execute("ALTER TABLE prompts ALTER COLUMN id TYPE VARCHAR(64)")
        op.execute("ALTER TABLE prompt_versions ALTER COLUMN prompt_id TYPE VARCHAR(64)")
        op.execute(
            "ALTER TABLE organisation_prompt_configs ALTER COLUMN prompt_id TYPE VARCHAR(64)"
        )


def downgrade() -> None:
    pass
