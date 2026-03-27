"""Add pipeline definition, stage definition, and execution trace records.

Revision ID: 20260327_0016
Revises: 20260327_0015
Create Date: 2026-03-27 17:30:00.000000

"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "20260327_0016"
down_revision = "20260327_0015"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "pipeline_definitions",
        sa.Column("pipeline_name", sa.String(length=128), primary_key=True),
        sa.Column("topology", sa.String(length=128), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "stage_definitions",
            sa.JSON(),
            nullable=False,
            server_default="[]",
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "stage_definitions",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("pipeline_name", sa.String(length=128), nullable=False, index=True),
        sa.Column("stage_name", sa.String(length=128), nullable=False),
        sa.Column("stage_kind", sa.String(length=32), nullable=False),
        sa.Column(
            "dependencies",
            sa.JSON(),
            nullable=False,
            server_default="[]",
        ),
        sa.Column("runner_class", sa.String(length=128), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
    )
    op.create_index(
        "ix_stage_definitions_pipeline_stage",
        "stage_definitions",
        ["pipeline_name", "stage_name"],
        unique=True,
    )

    op.create_table(
        "pipeline_execution_traces",
        sa.Column("pipeline_run_id", sa.String(length=32), primary_key=True),
        sa.Column("pipeline_name", sa.String(length=128), nullable=False, index=True),
        sa.Column(
            "execution_sequence",
            sa.JSON(),
            nullable=False,
            server_default="[]",
        ),
        sa.Column("total_duration_ms", sa.Integer(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("pipeline_execution_traces")
    op.drop_table("stage_definitions")
    op.drop_table("pipeline_definitions")
