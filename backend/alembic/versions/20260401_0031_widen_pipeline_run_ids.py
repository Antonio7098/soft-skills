"""Widen pipeline run identifier columns for subpipeline UUIDs.

Revision ID: 20260401_0031
Revises: 20260401_0030
Create Date: 2026-04-01 18:00:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260401_0031"
down_revision = "increase_prompt_id_64"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column("pipeline_runs", "pipeline_run_id", type_=sa.String(length=64), existing_type=sa.String(length=32))
    op.alter_column("provider_calls", "pipeline_run_id", type_=sa.String(length=64), existing_type=sa.String(length=32), existing_nullable=True)
    op.alter_column("pipeline_execution_traces", "pipeline_run_id", type_=sa.String(length=64), existing_type=sa.String(length=32))
    op.alter_column("assistant_turns", "pipeline_run_id", type_=sa.String(length=64), existing_type=sa.String(length=32), existing_nullable=True)
    op.alter_column("assistant_tool_calls", "child_run_id", type_=sa.String(length=64), existing_type=sa.String(length=32), existing_nullable=True)
    op.alter_column("assessments", "pipeline_run_id", type_=sa.String(length=64), existing_type=sa.String(length=32))
    op.alter_column("evaluation_runs", "pipeline_run_id", type_=sa.String(length=64), existing_type=sa.String(length=32), existing_nullable=True)


def downgrade() -> None:
    op.alter_column("evaluation_runs", "pipeline_run_id", type_=sa.String(length=32), existing_type=sa.String(length=64), existing_nullable=True)
    op.alter_column("assessments", "pipeline_run_id", type_=sa.String(length=32), existing_type=sa.String(length=64))
    op.alter_column("assistant_tool_calls", "child_run_id", type_=sa.String(length=32), existing_type=sa.String(length=64), existing_nullable=True)
    op.alter_column("assistant_turns", "pipeline_run_id", type_=sa.String(length=32), existing_type=sa.String(length=64), existing_nullable=True)
    op.alter_column("pipeline_execution_traces", "pipeline_run_id", type_=sa.String(length=32), existing_type=sa.String(length=64))
    op.alter_column("provider_calls", "pipeline_run_id", type_=sa.String(length=32), existing_type=sa.String(length=64), existing_nullable=True)
    op.alter_column("pipeline_runs", "pipeline_run_id", type_=sa.String(length=32), existing_type=sa.String(length=64))
