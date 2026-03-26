"""Evaluation framework and progression replay linkage."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "20260326_0009"
down_revision = "20260326_0008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "progression_snapshots",
        sa.Column("previous_snapshot_id", sa.String(length=32), nullable=True),
    )

    op.create_table(
        "evaluation_suites",
        sa.Column("suite_id", sa.String(length=64), primary_key=True),
        sa.Column("suite_type", sa.String(length=32), nullable=False),
        sa.Column("suite_version", sa.String(length=64), nullable=False),
        sa.Column("benchmark_set_version", sa.String(length=64), nullable=True),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("requires_learner_id", sa.Boolean(), nullable=False),
        sa.Column("definition_payload", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_evaluation_suites_suite_type", "evaluation_suites", ["suite_type"], unique=False)

    op.create_table(
        "evaluation_runs",
        sa.Column("id", sa.String(length=32), primary_key=True),
        sa.Column("suite_id", sa.String(length=64), nullable=False),
        sa.Column("suite_type", sa.String(length=32), nullable=False),
        sa.Column("suite_version", sa.String(length=64), nullable=False),
        sa.Column("benchmark_set_version", sa.String(length=64), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("triggered_by_user_id", sa.String(length=32), nullable=False),
        sa.Column("learner_id", sa.String(length=32), nullable=True),
        sa.Column("request_id", sa.String(length=32), nullable=True),
        sa.Column("trace_id", sa.String(length=32), nullable=True),
        sa.Column("workflow_id", sa.String(length=64), nullable=True),
        sa.Column("pipeline_run_id", sa.String(length=32), nullable=True),
        sa.Column("subject_type", sa.String(length=64), nullable=True),
        sa.Column("subject_ref", sa.String(length=128), nullable=True),
        sa.Column("passed", sa.Boolean(), nullable=False),
        sa.Column("aggregate_metrics", sa.JSON(), nullable=False),
        sa.Column("summary", sa.JSON(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_evaluation_runs_suite_id", "evaluation_runs", ["suite_id"], unique=False)
    op.create_index("ix_evaluation_runs_suite_type", "evaluation_runs", ["suite_type"], unique=False)
    op.create_index("ix_evaluation_runs_status", "evaluation_runs", ["status"], unique=False)
    op.create_index(
        "ix_evaluation_runs_triggered_by_user_id",
        "evaluation_runs",
        ["triggered_by_user_id"],
        unique=False,
    )
    op.create_index("ix_evaluation_runs_learner_id", "evaluation_runs", ["learner_id"], unique=False)
    op.create_index("ix_evaluation_runs_request_id", "evaluation_runs", ["request_id"], unique=False)
    op.create_index("ix_evaluation_runs_trace_id", "evaluation_runs", ["trace_id"], unique=False)
    op.create_index("ix_evaluation_runs_workflow_id", "evaluation_runs", ["workflow_id"], unique=False)
    op.create_index(
        "ix_evaluation_runs_pipeline_run_id",
        "evaluation_runs",
        ["pipeline_run_id"],
        unique=False,
    )

    op.create_table(
        "evaluation_case_results",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("evaluation_run_id", sa.String(length=32), nullable=False),
        sa.Column("case_id", sa.String(length=128), nullable=False),
        sa.Column("case_label", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("error_code", sa.String(length=32), nullable=True),
        sa.Column("metrics", sa.JSON(), nullable=False),
        sa.Column("detail_payload", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_evaluation_case_results_evaluation_run_id",
        "evaluation_case_results",
        ["evaluation_run_id"],
        unique=False,
    )
    op.create_index(
        "ix_evaluation_case_results_case_id",
        "evaluation_case_results",
        ["case_id"],
        unique=False,
    )
    op.create_index(
        "ix_evaluation_case_results_status",
        "evaluation_case_results",
        ["status"],
        unique=False,
    )

    op.create_table(
        "release_gate_decisions",
        sa.Column("id", sa.String(length=32), primary_key=True),
        sa.Column("evaluation_run_id", sa.String(length=32), nullable=False),
        sa.Column("decided_by_user_id", sa.String(length=32), nullable=False),
        sa.Column("request_id", sa.String(length=32), nullable=True),
        sa.Column("trace_id", sa.String(length=32), nullable=True),
        sa.Column("workflow_id", sa.String(length=64), nullable=True),
        sa.Column("subject_type", sa.String(length=64), nullable=False),
        sa.Column("subject_ref", sa.String(length=128), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("summary", sa.JSON(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_release_gate_decisions_evaluation_run_id",
        "release_gate_decisions",
        ["evaluation_run_id"],
        unique=False,
    )
    op.create_index(
        "ix_release_gate_decisions_decided_by_user_id",
        "release_gate_decisions",
        ["decided_by_user_id"],
        unique=False,
    )
    op.create_index(
        "ix_release_gate_decisions_request_id",
        "release_gate_decisions",
        ["request_id"],
        unique=False,
    )
    op.create_index(
        "ix_release_gate_decisions_trace_id",
        "release_gate_decisions",
        ["trace_id"],
        unique=False,
    )
    op.create_index(
        "ix_release_gate_decisions_workflow_id",
        "release_gate_decisions",
        ["workflow_id"],
        unique=False,
    )
    op.create_index(
        "ix_release_gate_decisions_subject_type",
        "release_gate_decisions",
        ["subject_type"],
        unique=False,
    )
    op.create_index(
        "ix_release_gate_decisions_subject_ref",
        "release_gate_decisions",
        ["subject_ref"],
        unique=False,
    )
    op.create_index(
        "ix_release_gate_decisions_status",
        "release_gate_decisions",
        ["status"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_release_gate_decisions_status", table_name="release_gate_decisions")
    op.drop_index("ix_release_gate_decisions_subject_ref", table_name="release_gate_decisions")
    op.drop_index("ix_release_gate_decisions_subject_type", table_name="release_gate_decisions")
    op.drop_index("ix_release_gate_decisions_workflow_id", table_name="release_gate_decisions")
    op.drop_index("ix_release_gate_decisions_trace_id", table_name="release_gate_decisions")
    op.drop_index("ix_release_gate_decisions_request_id", table_name="release_gate_decisions")
    op.drop_index(
        "ix_release_gate_decisions_decided_by_user_id",
        table_name="release_gate_decisions",
    )
    op.drop_index(
        "ix_release_gate_decisions_evaluation_run_id",
        table_name="release_gate_decisions",
    )
    op.drop_table("release_gate_decisions")

    op.drop_index("ix_evaluation_case_results_status", table_name="evaluation_case_results")
    op.drop_index("ix_evaluation_case_results_case_id", table_name="evaluation_case_results")
    op.drop_index(
        "ix_evaluation_case_results_evaluation_run_id",
        table_name="evaluation_case_results",
    )
    op.drop_table("evaluation_case_results")

    op.drop_index("ix_evaluation_runs_pipeline_run_id", table_name="evaluation_runs")
    op.drop_index("ix_evaluation_runs_workflow_id", table_name="evaluation_runs")
    op.drop_index("ix_evaluation_runs_trace_id", table_name="evaluation_runs")
    op.drop_index("ix_evaluation_runs_request_id", table_name="evaluation_runs")
    op.drop_index("ix_evaluation_runs_learner_id", table_name="evaluation_runs")
    op.drop_index(
        "ix_evaluation_runs_triggered_by_user_id",
        table_name="evaluation_runs",
    )
    op.drop_index("ix_evaluation_runs_status", table_name="evaluation_runs")
    op.drop_index("ix_evaluation_runs_suite_type", table_name="evaluation_runs")
    op.drop_index("ix_evaluation_runs_suite_id", table_name="evaluation_runs")
    op.drop_table("evaluation_runs")

    op.drop_index("ix_evaluation_suites_suite_type", table_name="evaluation_suites")
    op.drop_table("evaluation_suites")

    op.drop_column("progression_snapshots", "previous_snapshot_id")
