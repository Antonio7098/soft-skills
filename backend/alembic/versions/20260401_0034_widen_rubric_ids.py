"""Widen rubric identifier columns for generated rubric ids.

Revision ID: 20260401_0034
Revises: 20260401_0033
Create Date: 2026-04-01 20:10:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260401_0034"
down_revision = "20260401_0033"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("organisation_rubric_configs") as batch_op:
        batch_op.alter_column(
            "rubric_id",
            type_=sa.String(length=64),
            existing_type=sa.String(length=32),
        )
    with op.batch_alter_table("rubrics") as batch_op:
        batch_op.alter_column(
            "id",
            type_=sa.String(length=64),
            existing_type=sa.String(length=32),
        )
    with op.batch_alter_table("rubric_versions") as batch_op:
        batch_op.alter_column(
            "rubric_id",
            type_=sa.String(length=64),
            existing_type=sa.String(length=32),
        )


def downgrade() -> None:
    with op.batch_alter_table("rubric_versions") as batch_op:
        batch_op.alter_column(
            "rubric_id",
            type_=sa.String(length=32),
            existing_type=sa.String(length=64),
        )
    with op.batch_alter_table("rubrics") as batch_op:
        batch_op.alter_column(
            "id",
            type_=sa.String(length=32),
            existing_type=sa.String(length=64),
        )
    with op.batch_alter_table("organisation_rubric_configs") as batch_op:
        batch_op.alter_column(
            "rubric_id",
            type_=sa.String(length=32),
            existing_type=sa.String(length=64),
        )
