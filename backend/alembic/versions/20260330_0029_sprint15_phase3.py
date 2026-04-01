"""sprint15_phase3_add_prompt_version_fk

Add prompt_version_id FK to content_generation_artifacts table.
Phase 3 of sprint 15.

Revision ID: sprint15_phase3
Revises: sprint15_phase2
Create Date: 2026-03-30

"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import context as _context
from alembic import op

revision = "sprint15_phase3"
down_revision = "sprint15_phase2"
branch_labels = None
depends_on = None


def _is_sqlite() -> bool:
    return _context.get_context().dialect.name == "sqlite"


def _column_exists(connection, table_name: str, column_name: str) -> bool:
    if _is_sqlite():
        result = connection.execute(
            sa.text("SELECT name FROM pragma_table_info(:table) WHERE name=:col"),
            {"table": table_name, "col": column_name},
        )
    else:
        result = connection.execute(
            sa.text(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_schema = 'public' AND table_name = :table AND column_name = :col"
            ),
            {"table": table_name, "col": column_name},
        )
    return result.fetchone() is not None


def upgrade() -> None:
    connection = op.get_bind()

    # Check if column already exists
    if not _column_exists(connection, "content_generation_artifacts", "prompt_version_id"):
        connection.execute(
            sa.text("ALTER TABLE content_generation_artifacts ADD COLUMN prompt_version_id INTEGER")
        )
        connection.execute(
            sa.text(
                "CREATE INDEX ix_content_generation_artifacts_prompt_version_id ON content_generation_artifacts (prompt_version_id)"
            )
        )


def downgrade() -> None:
    connection = op.get_bind()
    connection.execute(
        sa.text("DROP INDEX IF EXISTS ix_content_generation_artifacts_prompt_version_id")
    )
    connection.execute(
        sa.text("ALTER TABLE content_generation_artifacts DROP COLUMN prompt_version_id")
    )
