"""Add prompt version, render metrics, and render event records.

Revision ID: 20260328_0017
Revises: 20260327_0016
Create Date: 2026-03-28 00:00:00.000000

"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "20260328_0017"
down_revision = "20260327_0016"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "prompt_versions",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(length=128), nullable=False, index=True),
        sa.Column("version", sa.String(length=32), nullable=False, index=True),
        sa.Column("prompt_type", sa.String(length=32), nullable=False, index=True),
        sa.Column("template", sa.Text(), nullable=False),
        sa.Column("variables_schema", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("output_schema", sa.JSON(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, index=True),
        sa.Column("parent_version_id", sa.Integer(), nullable=True, index=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("name", "version", name="ix_prompt_versions_name_version"),
    )

    op.create_table(
        "prompt_render_metrics",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("prompt_version_id", sa.Integer(), nullable=False, index=True),
        sa.Column("render_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("success_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("failure_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("avg_latency_ms", sa.Float(), nullable=True),
        sa.Column("total_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_rendered_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("prompt_version_id", name="ix_prompt_render_metrics_version_id"),
    )

    op.create_table(
        "prompt_render_events",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("event_id", sa.String(length=32), nullable=False, unique=True, index=True),
        sa.Column("prompt_version_id", sa.Integer(), nullable=False, index=True),
        sa.Column("success", sa.Boolean(), nullable=False),
        sa.Column("latency_ms", sa.Integer(), nullable=True),
        sa.Column("tokens", sa.Integer(), nullable=True),
        sa.Column("error_code", sa.String(length=32), nullable=True),
        sa.Column("trace_id", sa.String(length=32), nullable=True, index=True),
        sa.Column("rendered_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("prompt_render_events")
    op.drop_table("prompt_render_metrics")
    op.drop_table("prompt_versions")
