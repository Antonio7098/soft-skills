"""Initial foundation tables."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "20260325_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "workflow_events",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("event_id", sa.String(length=32), nullable=False),
        sa.Column("event_type", sa.String(length=128), nullable=False),
        sa.Column("request_id", sa.String(length=32), nullable=True),
        sa.Column("trace_id", sa.String(length=32), nullable=True),
        sa.Column("workflow_id", sa.String(length=64), nullable=True),
        sa.Column("error_code", sa.String(length=32), nullable=True),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_workflow_events_event_id", "workflow_events", ["event_id"], unique=True)
    op.create_index("ix_workflow_events_event_type", "workflow_events", ["event_type"], unique=False)
    op.create_index("ix_workflow_events_request_id", "workflow_events", ["request_id"], unique=False)
    op.create_index("ix_workflow_events_trace_id", "workflow_events", ["trace_id"], unique=False)
    op.create_index("ix_workflow_events_workflow_id", "workflow_events", ["workflow_id"], unique=False)

    op.create_table(
        "pipeline_runs",
        sa.Column("pipeline_run_id", sa.String(length=32), primary_key=True),
        sa.Column("pipeline_name", sa.String(length=128), nullable=False),
        sa.Column("topology", sa.String(length=128), nullable=True),
        sa.Column("execution_mode", sa.String(length=64), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("request_id", sa.String(length=32), nullable=True),
        sa.Column("trace_id", sa.String(length=32), nullable=True),
        sa.Column("user_id", sa.String(length=64), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("failed_stage", sa.String(length=128), nullable=True),
        sa.Column("stage_results", sa.JSON(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_pipeline_runs_pipeline_name", "pipeline_runs", ["pipeline_name"], unique=False)
    op.create_index("ix_pipeline_runs_status", "pipeline_runs", ["status"], unique=False)
    op.create_index("ix_pipeline_runs_request_id", "pipeline_runs", ["request_id"], unique=False)
    op.create_index("ix_pipeline_runs_trace_id", "pipeline_runs", ["trace_id"], unique=False)
    op.create_index("ix_pipeline_runs_user_id", "pipeline_runs", ["user_id"], unique=False)

    op.create_table(
        "provider_calls",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("call_id", sa.String(length=32), nullable=False),
        sa.Column("operation", sa.String(length=64), nullable=False),
        sa.Column("provider", sa.String(length=64), nullable=False),
        sa.Column("model_id", sa.String(length=128), nullable=True),
        sa.Column("success", sa.Boolean(), nullable=False),
        sa.Column("latency_ms", sa.Integer(), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("pipeline_run_id", sa.String(length=32), nullable=True),
        sa.Column("request_id", sa.String(length=32), nullable=True),
        sa.Column("trace_id", sa.String(length=32), nullable=True),
        sa.Column("metrics", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_provider_calls_call_id", "provider_calls", ["call_id"], unique=True)
    op.create_index("ix_provider_calls_operation", "provider_calls", ["operation"], unique=False)
    op.create_index("ix_provider_calls_provider", "provider_calls", ["provider"], unique=False)
    op.create_index("ix_provider_calls_request_id", "provider_calls", ["request_id"], unique=False)
    op.create_index("ix_provider_calls_trace_id", "provider_calls", ["trace_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_provider_calls_trace_id", table_name="provider_calls")
    op.drop_index("ix_provider_calls_request_id", table_name="provider_calls")
    op.drop_index("ix_provider_calls_provider", table_name="provider_calls")
    op.drop_index("ix_provider_calls_operation", table_name="provider_calls")
    op.drop_index("ix_provider_calls_call_id", table_name="provider_calls")
    op.drop_table("provider_calls")

    op.drop_index("ix_pipeline_runs_user_id", table_name="pipeline_runs")
    op.drop_index("ix_pipeline_runs_trace_id", table_name="pipeline_runs")
    op.drop_index("ix_pipeline_runs_request_id", table_name="pipeline_runs")
    op.drop_index("ix_pipeline_runs_status", table_name="pipeline_runs")
    op.drop_index("ix_pipeline_runs_pipeline_name", table_name="pipeline_runs")
    op.drop_table("pipeline_runs")

    op.drop_index("ix_workflow_events_workflow_id", table_name="workflow_events")
    op.drop_index("ix_workflow_events_trace_id", table_name="workflow_events")
    op.drop_index("ix_workflow_events_request_id", table_name="workflow_events")
    op.drop_index("ix_workflow_events_event_type", table_name="workflow_events")
    op.drop_index("ix_workflow_events_event_id", table_name="workflow_events")
    op.drop_table("workflow_events")
