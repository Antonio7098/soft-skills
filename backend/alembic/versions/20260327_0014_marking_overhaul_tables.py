"""Add rubric criteria and per-skill assessment tables.

Revision ID: 20260327_0014
Revises: 20260326_0013
Create Date: 2026-03-27 12:00:00.000000

"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "20260327_0014"
down_revision = "4f2e0968813a"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "rubric_criteria",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("rubric_id", sa.String(length=128), nullable=False),
        sa.Column("rubric_version", sa.String(length=32), nullable=False),
        sa.Column("criterion_ref", sa.String(length=64), nullable=False),
        sa.Column("skill_slug", sa.String(length=64), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("weight", sa.Float(), nullable=False),
        sa.Column("required", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("position", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("levels_json", sa.JSON(), nullable=False),
    )
    op.create_index("ix_rubric_criteria_rubric_id", "rubric_criteria", ["rubric_id"])
    op.create_index("ix_rubric_criteria_criterion_ref", "rubric_criteria", ["criterion_ref"])
    op.create_index("ix_rubric_criteria_skill_slug", "rubric_criteria", ["skill_slug"])

    op.create_table(
        "assessment_skill_results",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("assessment_id", sa.String(length=32), nullable=False),
        sa.Column("skill_slug", sa.String(length=64), nullable=False),
        sa.Column("score", sa.Integer(), nullable=False),
        sa.Column("rationale", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_assessment_skill_results_assessment_id",
        "assessment_skill_results",
        ["assessment_id"],
    )
    op.create_index(
        "ix_assessment_skill_results_skill_slug",
        "assessment_skill_results",
        ["skill_slug"],
    )

    op.create_table(
        "assessment_skill_evidence",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("assessment_id", sa.String(length=32), nullable=False),
        sa.Column("skill_slug", sa.String(length=64), nullable=False),
        sa.Column("quote", sa.Text(), nullable=False),
        sa.Column("explanation", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_assessment_skill_evidence_assessment_id",
        "assessment_skill_evidence",
        ["assessment_id"],
    )
    op.create_index(
        "ix_assessment_skill_evidence_skill_slug",
        "assessment_skill_evidence",
        ["skill_slug"],
    )


def downgrade() -> None:
    op.drop_index("ix_assessment_skill_evidence_skill_slug", table_name="assessment_skill_evidence")
    op.drop_index(
        "ix_assessment_skill_evidence_assessment_id",
        table_name="assessment_skill_evidence",
    )
    op.drop_table("assessment_skill_evidence")

    op.drop_index("ix_assessment_skill_results_skill_slug", table_name="assessment_skill_results")
    op.drop_index(
        "ix_assessment_skill_results_assessment_id",
        table_name="assessment_skill_results",
    )
    op.drop_table("assessment_skill_results")

    op.drop_index("ix_rubric_criteria_skill_slug", table_name="rubric_criteria")
    op.drop_index("ix_rubric_criteria_criterion_ref", table_name="rubric_criteria")
    op.drop_index("ix_rubric_criteria_rubric_id", table_name="rubric_criteria")
    op.drop_table("rubric_criteria")
