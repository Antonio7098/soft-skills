"""Progression snapshots, recommendations, and recalculation audit."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "20260325_0004"
down_revision = "20260325_0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "progression_snapshots",
        sa.Column("id", sa.String(length=32), primary_key=True),
        sa.Column("learner_id", sa.String(length=32), nullable=False),
        sa.Column("source_assessment_id", sa.String(length=32), nullable=False),
        sa.Column("trace_id", sa.String(length=32), nullable=False),
        sa.Column("workflow_id", sa.String(length=64), nullable=False),
        sa.Column("engine_version", sa.String(length=64), nullable=False),
        sa.Column("schema_version", sa.String(length=64), nullable=False),
        sa.Column("config_version", sa.String(length=64), nullable=False),
        sa.Column("evidence_ledger_schema_version", sa.String(length=64), nullable=False),
        sa.Column("snapshot_payload", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_progression_snapshots_learner_id",
        "progression_snapshots",
        ["learner_id"],
        unique=False,
    )
    op.create_index(
        "ix_progression_snapshots_source_assessment_id",
        "progression_snapshots",
        ["source_assessment_id"],
        unique=False,
    )
    op.create_index(
        "ix_progression_snapshots_trace_id",
        "progression_snapshots",
        ["trace_id"],
        unique=False,
    )
    op.create_index(
        "ix_progression_snapshots_workflow_id",
        "progression_snapshots",
        ["workflow_id"],
        unique=False,
    )
    op.create_index(
        "ix_progression_snapshots_config_version",
        "progression_snapshots",
        ["config_version"],
        unique=False,
    )

    op.create_table(
        "recommendation_artifacts",
        sa.Column("id", sa.String(length=32), primary_key=True),
        sa.Column("learner_id", sa.String(length=32), nullable=False),
        sa.Column("progress_snapshot_id", sa.String(length=32), nullable=False),
        sa.Column("trace_id", sa.String(length=32), nullable=False),
        sa.Column("workflow_id", sa.String(length=64), nullable=False),
        sa.Column("engine_version", sa.String(length=64), nullable=False),
        sa.Column("schema_version", sa.String(length=64), nullable=False),
        sa.Column("config_version", sa.String(length=64), nullable=False),
        sa.Column("context_snapshot_id", sa.String(length=64), nullable=False),
        sa.Column("candidate_count", sa.Integer(), nullable=False),
        sa.Column("artifact_payload", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_recommendation_artifacts_learner_id",
        "recommendation_artifacts",
        ["learner_id"],
        unique=False,
    )
    op.create_index(
        "ix_recommendation_artifacts_progress_snapshot_id",
        "recommendation_artifacts",
        ["progress_snapshot_id"],
        unique=False,
    )
    op.create_index(
        "ix_recommendation_artifacts_trace_id",
        "recommendation_artifacts",
        ["trace_id"],
        unique=False,
    )
    op.create_index(
        "ix_recommendation_artifacts_workflow_id",
        "recommendation_artifacts",
        ["workflow_id"],
        unique=False,
    )
    op.create_index(
        "ix_recommendation_artifacts_config_version",
        "recommendation_artifacts",
        ["config_version"],
        unique=False,
    )
    op.create_index(
        "ix_recommendation_artifacts_context_snapshot_id",
        "recommendation_artifacts",
        ["context_snapshot_id"],
        unique=False,
    )

    op.create_table(
        "progress_recalculations",
        sa.Column("id", sa.String(length=32), primary_key=True),
        sa.Column("learner_id", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("trace_id", sa.String(length=32), nullable=False),
        sa.Column("workflow_id", sa.String(length=64), nullable=False),
        sa.Column("config_version", sa.String(length=64), nullable=False),
        sa.Column("previous_snapshot_id", sa.String(length=32), nullable=True),
        sa.Column("next_snapshot_id", sa.String(length=32), nullable=True),
        sa.Column("next_recommendation_id", sa.String(length=32), nullable=True),
        sa.Column("diff_summary", sa.JSON(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "ix_progress_recalculations_learner_id",
        "progress_recalculations",
        ["learner_id"],
        unique=False,
    )
    op.create_index(
        "ix_progress_recalculations_status",
        "progress_recalculations",
        ["status"],
        unique=False,
    )
    op.create_index(
        "ix_progress_recalculations_trace_id",
        "progress_recalculations",
        ["trace_id"],
        unique=False,
    )
    op.create_index(
        "ix_progress_recalculations_workflow_id",
        "progress_recalculations",
        ["workflow_id"],
        unique=False,
    )
    op.create_index(
        "ix_progress_recalculations_config_version",
        "progress_recalculations",
        ["config_version"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_progress_recalculations_config_version", table_name="progress_recalculations")
    op.drop_index("ix_progress_recalculations_workflow_id", table_name="progress_recalculations")
    op.drop_index("ix_progress_recalculations_trace_id", table_name="progress_recalculations")
    op.drop_index("ix_progress_recalculations_status", table_name="progress_recalculations")
    op.drop_index("ix_progress_recalculations_learner_id", table_name="progress_recalculations")
    op.drop_table("progress_recalculations")

    op.drop_index(
        "ix_recommendation_artifacts_context_snapshot_id",
        table_name="recommendation_artifacts",
    )
    op.drop_index("ix_recommendation_artifacts_config_version", table_name="recommendation_artifacts")
    op.drop_index("ix_recommendation_artifacts_workflow_id", table_name="recommendation_artifacts")
    op.drop_index("ix_recommendation_artifacts_trace_id", table_name="recommendation_artifacts")
    op.drop_index(
        "ix_recommendation_artifacts_progress_snapshot_id",
        table_name="recommendation_artifacts",
    )
    op.drop_index("ix_recommendation_artifacts_learner_id", table_name="recommendation_artifacts")
    op.drop_table("recommendation_artifacts")

    op.drop_index("ix_progression_snapshots_config_version", table_name="progression_snapshots")
    op.drop_index("ix_progression_snapshots_workflow_id", table_name="progression_snapshots")
    op.drop_index("ix_progression_snapshots_trace_id", table_name="progression_snapshots")
    op.drop_index(
        "ix_progression_snapshots_source_assessment_id",
        table_name="progression_snapshots",
    )
    op.drop_index("ix_progression_snapshots_learner_id", table_name="progression_snapshots")
    op.drop_table("progression_snapshots")
