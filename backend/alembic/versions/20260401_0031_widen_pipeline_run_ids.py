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


def _drop_admin_agent_views() -> None:
    op.execute("DROP VIEW IF EXISTS admin_agent_workflow_events_v")
    op.execute("DROP VIEW IF EXISTS admin_agent_evaluation_runs_v")
    op.execute("DROP VIEW IF EXISTS admin_agent_assistant_sessions_v")
    op.execute("DROP VIEW IF EXISTS admin_agent_provider_calls_v")
    op.execute("DROP VIEW IF EXISTS admin_agent_pipeline_runs_v")
    op.execute("DROP VIEW IF EXISTS assistant_safe_attempt_summaries_v")
    op.execute("DROP VIEW IF EXISTS assistant_safe_collections_v")
    op.execute("DROP VIEW IF EXISTS assistant_safe_taxonomy_v")


def _create_admin_agent_views() -> None:
    op.execute(
        """
        CREATE VIEW admin_agent_pipeline_runs_v AS
        SELECT
            COALESCE(event_org.organisation_id, membership_org.organisation_id) AS organisation_id,
            pr.pipeline_run_id,
            pr.pipeline_name,
            pr.topology,
            pr.execution_mode,
            pr.status AS run_status,
            pr.request_id,
            pr.trace_id,
            CASE
                WHEN pr.user_id IS NULL THEN NULL
                ELSE 'user_' || substr(pr.user_id, 1, 8)
            END AS actor_alias,
            pr.failed_stage,
            pr.error AS error_summary,
            pr.started_at,
            pr.finished_at
        FROM pipeline_runs AS pr
        LEFT JOIN (
            SELECT
                trace_id,
                max(organisation_id) AS organisation_id
            FROM workflow_events
            WHERE trace_id IS NOT NULL
              AND organisation_id IS NOT NULL
            GROUP BY trace_id
        ) AS event_org
          ON event_org.trace_id = pr.trace_id
        LEFT JOIN (
            SELECT
                pr_inner.pipeline_run_id,
                max(om.organisation_id) AS organisation_id
            FROM pipeline_runs AS pr_inner
            LEFT JOIN organisation_memberships AS om
              ON om.user_id = pr_inner.user_id
            GROUP BY pr_inner.pipeline_run_id
        ) AS membership_org
          ON membership_org.pipeline_run_id = pr.pipeline_run_id
        """
    )

    op.execute(
        """
        CREATE VIEW admin_agent_provider_calls_v AS
        SELECT
            COALESCE(pipeline_org.organisation_id, trace_org.organisation_id) AS organisation_id,
            pc.call_id,
            pc.operation,
            pc.provider,
            pc.model_id,
            pc.success,
            pc.latency_ms,
            pc.pipeline_run_id,
            pc.request_id,
            pc.trace_id,
            pc.created_at
        FROM provider_calls AS pc
        LEFT JOIN admin_agent_pipeline_runs_v AS pipeline_org
          ON pipeline_org.pipeline_run_id = pc.pipeline_run_id
        LEFT JOIN (
            SELECT
                trace_id,
                max(organisation_id) AS organisation_id
            FROM admin_agent_pipeline_runs_v
            WHERE trace_id IS NOT NULL
              AND organisation_id IS NOT NULL
            GROUP BY trace_id
        ) AS trace_org
          ON trace_org.trace_id = pc.trace_id
        """
    )

    op.execute(
        """
        CREATE VIEW admin_agent_assistant_sessions_v AS
        SELECT
            om.organisation_id,
            s.id AS session_id,
            CASE
                WHEN s.user_id IS NULL THEN NULL
                ELSE 'user_' || substr(s.user_id, 1, 8)
            END AS user_alias,
            s.title AS session_title,
            s.status AS session_status,
            COALESCE(turn_counts.turn_count, 0) AS turn_count,
            s.created_at,
            s.updated_at
        FROM assistant_sessions AS s
        JOIN organisation_memberships AS om
          ON om.user_id = s.user_id
        LEFT JOIN (
            SELECT
                session_id,
                count(*) AS turn_count
            FROM assistant_turns
            GROUP BY session_id
        ) AS turn_counts
          ON turn_counts.session_id = s.id
        """
    )

    op.execute(
        """
        CREATE VIEW admin_agent_evaluation_runs_v AS
        SELECT
            COALESCE(
                pipeline_org.organisation_id,
                learner_org.organisation_id,
                trigger_org.organisation_id
            ) AS organisation_id,
            er.id AS evaluation_run_id,
            er.suite_id,
            er.suite_type,
            er.suite_version,
            er.status AS run_status,
            CASE
                WHEN er.triggered_by_user_id IS NULL THEN NULL
                ELSE 'user_' || substr(er.triggered_by_user_id, 1, 8)
            END AS triggered_by_alias,
            CASE
                WHEN er.learner_id IS NULL THEN NULL
                ELSE 'user_' || substr(er.learner_id, 1, 8)
            END AS learner_alias,
            er.passed,
            er.subject_type,
            er.subject_ref,
            er.request_id,
            er.trace_id,
            er.workflow_id,
            er.pipeline_run_id,
            er.started_at,
            er.completed_at
        FROM evaluation_runs AS er
        LEFT JOIN admin_agent_pipeline_runs_v AS pipeline_org
          ON pipeline_org.pipeline_run_id = er.pipeline_run_id
        LEFT JOIN (
            SELECT
                user_id,
                max(organisation_id) AS organisation_id
            FROM organisation_memberships
            GROUP BY user_id
        ) AS learner_org
          ON learner_org.user_id = er.learner_id
        LEFT JOIN (
            SELECT
                user_id,
                max(organisation_id) AS organisation_id
            FROM organisation_memberships
            GROUP BY user_id
        ) AS trigger_org
          ON trigger_org.user_id = er.triggered_by_user_id
        """
    )

    op.execute(
        """
        CREATE VIEW admin_agent_workflow_events_v AS
        SELECT
            COALESCE(we.organisation_id, pipeline_org.organisation_id) AS organisation_id,
            we.event_id,
            we.event_type,
            we.request_id,
            we.trace_id,
            we.workflow_id,
            we.error_code,
            we.occurred_at
        FROM workflow_events AS we
        LEFT JOIN (
            SELECT
                trace_id,
                max(organisation_id) AS organisation_id
            FROM admin_agent_pipeline_runs_v
            WHERE trace_id IS NOT NULL
              AND organisation_id IS NOT NULL
            GROUP BY trace_id
        ) AS pipeline_org
          ON pipeline_org.trace_id = we.trace_id
        """
    )


def upgrade() -> None:
    _drop_admin_agent_views()
    with op.batch_alter_table("pipeline_runs") as batch_op:
        batch_op.alter_column(
            "pipeline_run_id", type_=sa.String(length=64), existing_type=sa.String(length=32)
        )
    with op.batch_alter_table("provider_calls") as batch_op:
        batch_op.alter_column(
            "pipeline_run_id",
            type_=sa.String(length=64),
            existing_type=sa.String(length=32),
            existing_nullable=True,
        )
    with op.batch_alter_table("pipeline_execution_traces") as batch_op:
        batch_op.alter_column(
            "pipeline_run_id", type_=sa.String(length=64), existing_type=sa.String(length=32)
        )
    with op.batch_alter_table("assistant_turns") as batch_op:
        batch_op.alter_column(
            "pipeline_run_id",
            type_=sa.String(length=64),
            existing_type=sa.String(length=32),
            existing_nullable=True,
        )
    with op.batch_alter_table("assistant_tool_calls") as batch_op:
        batch_op.alter_column(
            "child_run_id",
            type_=sa.String(length=64),
            existing_type=sa.String(length=32),
            existing_nullable=True,
        )
    with op.batch_alter_table("assessments") as batch_op:
        batch_op.alter_column(
            "pipeline_run_id", type_=sa.String(length=64), existing_type=sa.String(length=32)
        )
    with op.batch_alter_table("evaluation_runs") as batch_op:
        batch_op.alter_column(
            "pipeline_run_id",
            type_=sa.String(length=64),
            existing_type=sa.String(length=32),
            existing_nullable=True,
        )
    _create_admin_agent_views()


def downgrade() -> None:
    _drop_admin_agent_views()
    op.alter_column(
        "evaluation_runs",
        "pipeline_run_id",
        type_=sa.String(length=32),
        existing_type=sa.String(length=64),
        existing_nullable=True,
    )
    op.alter_column(
        "assessments",
        "pipeline_run_id",
        type_=sa.String(length=32),
        existing_type=sa.String(length=64),
    )
    op.alter_column(
        "assistant_tool_calls",
        "child_run_id",
        type_=sa.String(length=32),
        existing_type=sa.String(length=64),
        existing_nullable=True,
    )
    op.alter_column(
        "assistant_turns",
        "pipeline_run_id",
        type_=sa.String(length=32),
        existing_type=sa.String(length=64),
        existing_nullable=True,
    )
    op.alter_column(
        "pipeline_execution_traces",
        "pipeline_run_id",
        type_=sa.String(length=32),
        existing_type=sa.String(length=64),
    )
    op.alter_column(
        "provider_calls",
        "pipeline_run_id",
        type_=sa.String(length=32),
        existing_type=sa.String(length=64),
        existing_nullable=True,
    )
    op.alter_column(
        "pipeline_runs",
        "pipeline_run_id",
        type_=sa.String(length=32),
        existing_type=sa.String(length=64),
    )
    _create_admin_agent_views()
