"""sprint15_phase2_prompt_rubric_tables

Create parent-child prompt/rubric tables and org config tables.
Phase 2 of sprint 15.
Per MVP spec: "No migration of existing data - start fresh".
Legacy tables renamed to _legacy_ prefix.

Revision ID: sprint15_phase2
Revises: sprint15_phase1
Create Date: 2026-03-30

"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "sprint15_phase2"
down_revision = "sprint15_phase1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    connection = op.get_bind()

    # Check what exists
    result = connection.execute(
        sa.text("SELECT name FROM sqlite_master WHERE type='table' AND name='prompts'")
    )
    prompts_exists = result.fetchone() is not None

    result = connection.execute(
        sa.text("SELECT name FROM sqlite_master WHERE type='table' AND name='_legacy_prompts'")
    )
    legacy_prompts_exists = result.fetchone() is not None

    result = connection.execute(
        sa.text("SELECT name FROM sqlite_master WHERE type='table' AND name='prompt_versions'")
    )
    prompt_versions_exists = result.fetchone() is not None

    result = connection.execute(
        sa.text(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='_legacy_prompt_versions'"
        )
    )
    legacy_prompt_versions_exists = result.fetchone() is not None

    result = connection.execute(
        sa.text("SELECT name FROM sqlite_master WHERE type='table' AND name='rubrics'")
    )
    rubrics_exists = result.fetchone() is not None

    result = connection.execute(
        sa.text("SELECT name FROM sqlite_master WHERE type='table' AND name='_legacy_rubrics'")
    )
    legacy_rubrics_exists = result.fetchone() is not None

    result = connection.execute(
        sa.text("SELECT name FROM sqlite_master WHERE type='table' AND name='rubric_criteria'")
    )
    rubric_criteria_exists = result.fetchone() is not None

    result = connection.execute(
        sa.text(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='_legacy_rubric_criteria'"
        )
    )
    legacy_rubric_criteria_exists = result.fetchone() is not None

    # Handle prompts - rename or drop
    if prompts_exists:
        if legacy_prompts_exists:
            connection.execute(sa.text("DROP TABLE prompts"))
        else:
            connection.execute(sa.text("ALTER TABLE prompts RENAME TO _legacy_prompts"))

    # Handle prompt_versions - rename or drop
    if prompt_versions_exists:
        if legacy_prompt_versions_exists:
            connection.execute(sa.text("DROP TABLE prompt_versions"))
        else:
            connection.execute(
                sa.text("ALTER TABLE prompt_versions RENAME TO _legacy_prompt_versions")
            )

    # Handle rubrics - rename or drop
    if rubrics_exists:
        if legacy_rubrics_exists:
            connection.execute(sa.text("DROP TABLE rubrics"))
        else:
            connection.execute(sa.text("ALTER TABLE rubrics RENAME TO _legacy_rubrics"))

    # Handle rubric_criteria - rename or drop
    if rubric_criteria_exists:
        if legacy_rubric_criteria_exists:
            connection.execute(sa.text("DROP TABLE rubric_criteria"))
        else:
            connection.execute(
                sa.text("ALTER TABLE rubric_criteria RENAME TO _legacy_rubric_criteria")
            )

    connection.commit()

    # Use raw SQL for tables with unique constraints (SQLite limitation)
    # --- NEW RUBRICS TABLE (parent) ---
    connection.execute(
        sa.text(
            "CREATE TABLE rubrics ("
            "id VARCHAR(32) PRIMARY KEY,"
            "skill_slug VARCHAR(64) NOT NULL,"
            "organisation_id VARCHAR(32),"
            "name VARCHAR(255) NOT NULL,"
            "description TEXT,"
            "content_type VARCHAR(64) NOT NULL,"
            "schema_version VARCHAR(32) NOT NULL,"
            "created_at DATETIME NOT NULL,"
            "updated_at DATETIME NOT NULL"
            ")"
        )
    )
    connection.execute(
        sa.text("CREATE INDEX IF NOT EXISTS ix_rubrics_skill_slug ON rubrics (skill_slug)")
    )
    connection.execute(
        sa.text(
            "CREATE INDEX IF NOT EXISTS ix_rubrics_organisation_id ON rubrics (organisation_id)"
        )
    )
    connection.execute(
        sa.text(
            "CREATE UNIQUE INDEX IF NOT EXISTS uq_rubric_skill_org ON rubrics (skill_slug, organisation_id)"
        )
    )

    # --- NEW PROMPTS TABLE (parent) ---
    connection.execute(
        sa.text(
            "CREATE TABLE prompts ("
            "id VARCHAR(32) PRIMARY KEY,"
            "organisation_id VARCHAR(32),"
            "name VARCHAR(128) NOT NULL,"
            "description TEXT,"
            "prompt_type VARCHAR(32) NOT NULL,"
            "variables_schema JSON NOT NULL DEFAULT '{}',"
            "created_at DATETIME NOT NULL,"
            "updated_at DATETIME NOT NULL"
            ")"
        )
    )
    connection.execute(
        sa.text(
            "CREATE INDEX IF NOT EXISTS ix_prompts_organisation_id ON prompts (organisation_id)"
        )
    )
    connection.execute(
        sa.text(
            "CREATE UNIQUE INDEX IF NOT EXISTS uq_prompt_org_name ON prompts (organisation_id, name)"
        )
    )

    # --- NEW PROMPT VERSIONS TABLE (child, replaces current) ---
    connection.execute(
        sa.text(
            "CREATE TABLE prompt_versions ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT,"
            "prompt_id VARCHAR(32) NOT NULL,"
            "version VARCHAR(64) NOT NULL,"
            "template TEXT NOT NULL,"
            "variables_schema JSON NOT NULL DEFAULT '{}',"
            "output_schema JSON,"
            "status VARCHAR(32) NOT NULL DEFAULT 'draft',"
            "parent_version_id INTEGER,"
            "created_at DATETIME NOT NULL,"
            "updated_at DATETIME NOT NULL"
            ")"
        )
    )
    connection.execute(
        sa.text(
            "CREATE INDEX IF NOT EXISTS ix_prompt_versions_prompt_id ON prompt_versions (prompt_id)"
        )
    )
    connection.execute(
        sa.text("CREATE INDEX IF NOT EXISTS ix_prompt_versions_status ON prompt_versions (status)")
    )
    connection.execute(
        sa.text(
            "CREATE UNIQUE INDEX IF NOT EXISTS uq_prompt_version_prompt_version ON prompt_versions (prompt_id, version)"
        )
    )

    # --- RUBRIC VERSIONS TABLE (child, embeds criteria JSON) ---
    connection.execute(
        sa.text(
            "CREATE TABLE rubric_versions ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT,"
            "rubric_id VARCHAR(32) NOT NULL,"
            "version VARCHAR(64) NOT NULL,"
            "criteria JSON NOT NULL DEFAULT '[]',"
            "status VARCHAR(32) NOT NULL DEFAULT 'draft',"
            "created_at DATETIME NOT NULL,"
            "updated_at DATETIME NOT NULL"
            ")"
        )
    )
    connection.execute(
        sa.text(
            "CREATE INDEX IF NOT EXISTS ix_rubric_versions_rubric_id ON rubric_versions (rubric_id)"
        )
    )
    connection.execute(
        sa.text("CREATE INDEX IF NOT EXISTS ix_rubric_versions_status ON rubric_versions (status)")
    )
    connection.execute(
        sa.text(
            "CREATE UNIQUE INDEX IF NOT EXISTS uq_rubric_version_rubric_version ON rubric_versions (rubric_id, version)"
        )
    )

    # --- ORGANISATION PROMPT CONFIG ---
    connection.execute(
        sa.text(
            "CREATE TABLE organisation_prompt_configs ("
            "organisation_id VARCHAR(32) NOT NULL,"
            "task_kind VARCHAR(32) NOT NULL,"
            "prompt_id VARCHAR(32) NOT NULL,"
            "prompt_version_id INTEGER NOT NULL,"
            "created_at DATETIME NOT NULL,"
            "PRIMARY KEY (organisation_id, task_kind)"
            ")"
        )
    )

    # --- ORGANISATION RUBRIC CONFIG ---
    connection.execute(
        sa.text(
            "CREATE TABLE organisation_rubric_configs ("
            "organisation_id VARCHAR(32) NOT NULL,"
            "skill_slug VARCHAR(64) NOT NULL,"
            "rubric_id VARCHAR(32) NOT NULL,"
            "rubric_version_id INTEGER NOT NULL,"
            "created_at DATETIME NOT NULL,"
            "PRIMARY KEY (organisation_id, skill_slug)"
            ")"
        )
    )

    connection.commit()


def downgrade() -> None:
    connection = op.get_bind()
    connection.execute(sa.text("DROP TABLE IF EXISTS organisation_rubric_configs"))
    connection.execute(sa.text("DROP TABLE IF EXISTS organisation_prompt_configs"))
    connection.execute(sa.text("DROP TABLE IF EXISTS rubric_versions"))
    connection.execute(sa.text("DROP TABLE IF EXISTS prompt_versions"))
    connection.execute(sa.text("DROP TABLE IF EXISTS prompts"))
    connection.execute(sa.text("ALTER TABLE _legacy_rubric_criteria RENAME TO rubric_criteria"))
    connection.execute(sa.text("ALTER TABLE _legacy_rubrics RENAME TO rubrics"))
    connection.execute(sa.text("ALTER TABLE _legacy_prompts RENAME TO prompts"))
    connection.commit()
