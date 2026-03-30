"""sprint15_phase3_add_prompt_version_fk

Add prompt_version_id FK to content_generation_artifacts table.
Phase 3 of sprint 15.

Revision ID: sprint15_phase3
Revises: sprint15_phase2
Create Date: 2026-03-30

"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "sprint15_phase3"
down_revision = "sprint15_phase2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    connection = op.get_bind()

    # Check if column already exists
    result = connection.execute(
        sa.text(
            "SELECT name FROM pragma_table_info('content_generation_artifacts') WHERE name='prompt_version_id'"
        )
    )
    if result.fetchone() is None:
        connection.execute(
            sa.text("ALTER TABLE content_generation_artifacts ADD COLUMN prompt_version_id INTEGER")
        )
        connection.execute(
            sa.text(
                "CREATE INDEX ix_content_generation_artifacts_prompt_version_id ON content_generation_artifacts (prompt_version_id)"
            )
        )

    connection.commit()


def downgrade() -> None:
    connection = op.get_bind()
    connection.execute(
        sa.text("DROP INDEX IF EXISTS ix_content_generation_artifacts_prompt_version_id")
    )
    connection.execute(
        sa.text("ALTER TABLE content_generation_artifacts DROP COLUMN prompt_version_id")
    )
    connection.commit()
