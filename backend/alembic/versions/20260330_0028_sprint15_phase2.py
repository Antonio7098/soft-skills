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

import sqlalchemy as sa
from alembic import context as _context
from alembic import op

revision = "sprint15_phase2"
down_revision = "sprint15_phase1"
branch_labels = None
depends_on = None


def _is_sqlite() -> bool:
    return _context.get_context().dialect.name == "sqlite"


def _is_postgres() -> bool:
    return _context.get_context().dialect.name == "postgresql"


def _table_exists(connection, table_name: str) -> bool:
    if _is_sqlite():
        result = connection.execute(
            sa.text("SELECT name FROM sqlite_master WHERE type='table' AND name=:name"),
            {"name": table_name},
        )
    else:
        result = connection.execute(
            sa.text(
                "SELECT table_name FROM information_schema.tables "
                "WHERE table_schema = 'public' AND table_name = :name"
            ),
            {"name": table_name},
        )
    return result.fetchone() is not None


def upgrade() -> None:
    connection = op.get_bind()

    # Check what exists
    prompts_exists = _table_exists(connection, "prompts")
    legacy_prompts_exists = _table_exists(connection, "_legacy_prompts")
    prompt_versions_exists = _table_exists(connection, "prompt_versions")
    legacy_prompt_versions_exists = _table_exists(connection, "_legacy_prompt_versions")
    rubrics_exists = _table_exists(connection, "rubrics")
    legacy_rubrics_exists = _table_exists(connection, "_legacy_rubrics")
    rubric_criteria_exists = _table_exists(connection, "rubric_criteria")
    legacy_rubric_criteria_exists = _table_exists(connection, "_legacy_rubric_criteria")

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

    # Dialect-specific type for auto-increment PK
    if _is_postgres():
        autoincrement_pk = "SERIAL"
        timestamp_type = "TIMESTAMP WITH TIME ZONE"
    else:
        autoincrement_pk = "INTEGER PRIMARY KEY AUTOINCREMENT"
        timestamp_type = "DATETIME"

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
            "created_at {ts} NOT NULL,"
            "updated_at {ts} NOT NULL"
            ")".format(ts=timestamp_type)
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
            "variables_schema JSON NOT NULL DEFAULT '{{}}',"
            "created_at {ts} NOT NULL,"
            "updated_at {ts} NOT NULL"
            ")".format(ts=timestamp_type)
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
            "id {pk},"
            "prompt_id VARCHAR(32) NOT NULL,"
            "version VARCHAR(64) NOT NULL,"
            "template TEXT NOT NULL,"
            "variables_schema JSON NOT NULL DEFAULT '{{}}',"
            "output_schema JSON,"
            "status VARCHAR(32) NOT NULL DEFAULT 'draft',"
            "parent_version_id INTEGER,"
            "created_at {ts} NOT NULL,"
            "updated_at {ts} NOT NULL"
            ")".format(pk=autoincrement_pk, ts=timestamp_type)
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
            "id {pk},"
            "rubric_id VARCHAR(32) NOT NULL,"
            "version VARCHAR(64) NOT NULL,"
            "criteria JSON NOT NULL DEFAULT '[]',"
            "status VARCHAR(32) NOT NULL DEFAULT 'draft',"
            "created_at {ts} NOT NULL,"
            "updated_at {ts} NOT NULL"
            ")".format(pk=autoincrement_pk, ts=timestamp_type)
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
            "created_at {ts} NOT NULL,"
            "PRIMARY KEY (organisation_id, task_kind)"
            ")".format(ts=timestamp_type)
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
            "created_at {ts} NOT NULL,"
            "PRIMARY KEY (organisation_id, skill_slug)"
            ")".format(ts=timestamp_type)
        )
    )


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
