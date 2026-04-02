"""Widen workflow identifier columns for longer runtime keys.

Revision ID: 20260401_0033
Revises: 20260401_0032
Create Date: 2026-04-01 20:05:00.000000
"""

from __future__ import annotations

from alembic import context as _context
from alembic import op
import sqlalchemy as sa


revision = "20260401_0033"
down_revision = "20260401_0032"
branch_labels = None
depends_on = None


def _drop_dependent_views() -> None:
    op.execute("DROP VIEW IF EXISTS admin_agent_workflow_events_v")
    op.execute("DROP VIEW IF EXISTS admin_agent_evaluation_runs_v")
    op.execute("DROP VIEW IF EXISTS admin_agent_assistant_sessions_v")
    op.execute("DROP VIEW IF EXISTS admin_agent_provider_calls_v")
    op.execute("DROP VIEW IF EXISTS admin_agent_pipeline_runs_v")
    op.execute("DROP VIEW IF EXISTS assistant_safe_recommendations_v")
    op.execute("DROP VIEW IF EXISTS assistant_safe_progress_snapshots_v")
    op.execute("DROP VIEW IF EXISTS assistant_safe_attempt_summaries_v")
    op.execute("DROP VIEW IF EXISTS assistant_safe_collections_v")


def _sql_for_dialect(*, sqlite_sql: str, postgres_sql: str) -> str:
    if _context.get_context().dialect.name == "postgresql":
        return postgres_sql
    return sqlite_sql


def _create_assistant_views() -> None:
    op.execute(
        """
        CREATE VIEW assistant_safe_collections_v AS
        SELECT
            c.organisation_id,
            c.id AS collection_id,
            c.title,
            c.summary,
            c.target_audience,
            c.difficulty,
            c.content_format_mix,
            c.target_skill_slugs,
            c.target_competency_slugs,
            c.author_user_id,
            (
                SELECT count(*)
                FROM collection_saves AS cs
                WHERE cs.collection_id = c.id
            ) AS saved_count,
            c.rating_count,
            c.avg_rating,
            c.created_at,
            c.updated_at
        FROM collections AS c
        WHERE c.author_user_id IS NOT NULL
        """
    )
    op.execute(
        _sql_for_dialect(
            sqlite_sql="""
        CREATE VIEW assistant_safe_attempt_summaries_v AS
        SELECT
            om.organisation_id,
            a.user_id,
            a.id AS attempt_id,
            a.session_id,
            NULL AS practice_run_id,
            a.practice_type,
            a.content_item_id,
            a.content_item_type,
            a.status,
            a.assessment_id,
            ass.overall_score,
            CASE
                WHEN ass.strengths IS NULL OR json_array_length(ass.strengths) = 0 THEN NULL
                ELSE json_extract(ass.strengths, '$[0]')
            END AS strength_summary,
            CASE
                WHEN ass.next_actions IS NULL OR json_array_length(ass.next_actions) = 0 THEN NULL
                ELSE json_extract(ass.next_actions, '$[0]')
            END AS next_action_summary,
            a.created_at,
            a.submitted_at,
            a.assessed_at
        FROM attempts AS a
        JOIN organisation_memberships AS om
          ON om.user_id = a.user_id
        LEFT JOIN assessments AS ass
          ON ass.id = a.assessment_id
            """,
            postgres_sql="""
        CREATE VIEW assistant_safe_attempt_summaries_v AS
        SELECT
            om.organisation_id,
            a.user_id,
            a.id AS attempt_id,
            a.session_id,
            NULL AS practice_run_id,
            a.practice_type,
            a.content_item_id,
            a.content_item_type,
            a.status,
            a.assessment_id,
            ass.overall_score,
            CASE
                WHEN ass.strengths IS NULL OR jsonb_array_length(ass.strengths::jsonb) = 0 THEN NULL
                ELSE ass.strengths->>0
            END AS strength_summary,
            CASE
                WHEN ass.next_actions IS NULL OR jsonb_array_length(ass.next_actions::jsonb) = 0 THEN NULL
                ELSE ass.next_actions->>0
            END AS next_action_summary,
            a.created_at,
            a.submitted_at,
            a.assessed_at
        FROM attempts AS a
        JOIN organisation_memberships AS om
          ON om.user_id = a.user_id
        LEFT JOIN assessments AS ass
          ON ass.id = a.assessment_id
            """,
        )
    )
    op.execute(
        _sql_for_dialect(
            sqlite_sql="""
        CREATE VIEW assistant_safe_progress_snapshots_v AS
        SELECT
            om.organisation_id,
            ps.learner_id AS user_id,
            ps.id AS snapshot_id,
            ps.source_assessment_id,
            json_extract(ps.snapshot_payload, '$.weak_skill_slugs') AS weak_skill_slugs,
            json_extract(ps.snapshot_payload, '$.stagnating_skill_slugs') AS stagnating_skill_slugs,
            json_extract(ps.snapshot_payload, '$.coverage_gap_skill_slugs') AS coverage_gap_skill_slugs,
            COALESCE(json_array_length(json_extract(ps.snapshot_payload, '$.skill_states')), 0) AS skill_state_count,
            COALESCE(json_array_length(json_extract(ps.snapshot_payload, '$.competency_states')), 0) AS competency_state_count,
            ps.created_at
        FROM progression_snapshots AS ps
        JOIN organisation_memberships AS om
          ON om.user_id = ps.learner_id
            """,
            postgres_sql="""
        CREATE VIEW assistant_safe_progress_snapshots_v AS
        SELECT
            om.organisation_id,
            ps.learner_id AS user_id,
            ps.id AS snapshot_id,
            ps.source_assessment_id,
            ps.snapshot_payload->'weak_skill_slugs' AS weak_skill_slugs,
            ps.snapshot_payload->'stagnating_skill_slugs' AS stagnating_skill_slugs,
            ps.snapshot_payload->'coverage_gap_skill_slugs' AS coverage_gap_skill_slugs,
            COALESCE(jsonb_array_length((ps.snapshot_payload->>'skill_states')::jsonb), 0) AS skill_state_count,
            COALESCE(jsonb_array_length((ps.snapshot_payload->>'competency_states')::jsonb), 0) AS competency_state_count,
            ps.created_at
        FROM progression_snapshots AS ps
        JOIN organisation_memberships AS om
          ON om.user_id = ps.learner_id
            """,
        )
    )
    op.execute(
        _sql_for_dialect(
            sqlite_sql="""
        CREATE VIEW assistant_safe_recommendations_v AS
        SELECT
            om.organisation_id,
            ra.learner_id AS user_id,
            ra.id AS recommendation_id,
            ra.progress_snapshot_id,
            ra.context_snapshot_id,
            ra.candidate_count,
            json_extract(ra.artifact_payload, '$.items[0].content_id') AS top_pick_ref,
            json_extract(ra.artifact_payload, '$.items[0].reasons[0]') AS top_pick_reason,
            json_extract(ra.artifact_payload, '$.alternatives') AS alternative_refs,
            ra.created_at
        FROM recommendation_artifacts AS ra
        JOIN organisation_memberships AS om
          ON om.user_id = ra.learner_id
            """,
            postgres_sql="""
        CREATE VIEW assistant_safe_recommendations_v AS
        SELECT
            om.organisation_id,
            ra.learner_id AS user_id,
            ra.id AS recommendation_id,
            ra.progress_snapshot_id,
            ra.context_snapshot_id,
            ra.candidate_count,
            ra.artifact_payload->'items'->0->>'content_id' AS top_pick_ref,
            ra.artifact_payload->'items'->0->'reasons'->>0 AS top_pick_reason,
            ra.artifact_payload->'alternatives' AS alternative_refs,
            ra.created_at
        FROM recommendation_artifacts AS ra
        JOIN organisation_memberships AS om
          ON om.user_id = ra.learner_id
            """,
        )
    )


def _create_dependent_views() -> None:
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
    _create_assistant_views()


def upgrade() -> None:
    _drop_dependent_views()
    with op.batch_alter_table("workflow_events") as batch_op:
        batch_op.alter_column(
            "workflow_id",
            type_=sa.String(length=128),
            existing_type=sa.String(length=64),
            existing_nullable=True,
        )
    with op.batch_alter_table("collection_verification_reviews") as batch_op:
        batch_op.alter_column(
            "workflow_id",
            type_=sa.String(length=128),
            existing_type=sa.String(length=64),
            existing_nullable=True,
        )
    with op.batch_alter_table("content_generation_artifacts") as batch_op:
        batch_op.alter_column(
            "workflow_id",
            type_=sa.String(length=128),
            existing_type=sa.String(length=64),
            existing_nullable=True,
        )
    with op.batch_alter_table("practice_runs") as batch_op:
        batch_op.alter_column(
            "workflow_id",
            type_=sa.String(length=128),
            existing_type=sa.String(length=64),
        )
    with op.batch_alter_table("practice_sessions") as batch_op:
        batch_op.alter_column(
            "workflow_id",
            type_=sa.String(length=128),
            existing_type=sa.String(length=64),
        )
    with op.batch_alter_table("attempts") as batch_op:
        batch_op.alter_column(
            "workflow_id",
            type_=sa.String(length=128),
            existing_type=sa.String(length=64),
        )
    with op.batch_alter_table("assessments") as batch_op:
        batch_op.alter_column(
            "workflow_id",
            type_=sa.String(length=128),
            existing_type=sa.String(length=64),
        )
    with op.batch_alter_table("progression_snapshots") as batch_op:
        batch_op.alter_column(
            "workflow_id",
            type_=sa.String(length=128),
            existing_type=sa.String(length=64),
        )
    with op.batch_alter_table("recommendation_artifacts") as batch_op:
        batch_op.alter_column(
            "workflow_id",
            type_=sa.String(length=128),
            existing_type=sa.String(length=64),
        )
    with op.batch_alter_table("assistant_turns") as batch_op:
        batch_op.alter_column(
            "workflow_id",
            type_=sa.String(length=128),
            existing_type=sa.String(length=64),
        )
    with op.batch_alter_table("generation_streams") as batch_op:
        batch_op.alter_column(
            "workflow_id",
            type_=sa.String(length=128),
            existing_type=sa.String(length=64),
            existing_nullable=True,
        )
    with op.batch_alter_table("progress_recalculations") as batch_op:
        batch_op.alter_column(
            "workflow_id",
            type_=sa.String(length=128),
            existing_type=sa.String(length=64),
        )
    with op.batch_alter_table("evaluation_runs") as batch_op:
        batch_op.alter_column(
            "workflow_id",
            type_=sa.String(length=128),
            existing_type=sa.String(length=64),
            existing_nullable=True,
        )
    with op.batch_alter_table("release_gate_decisions") as batch_op:
        batch_op.alter_column(
            "workflow_id",
            type_=sa.String(length=128),
            existing_type=sa.String(length=64),
            existing_nullable=True,
        )
    _create_dependent_views()


def downgrade() -> None:
    _drop_dependent_views()
    with op.batch_alter_table("release_gate_decisions") as batch_op:
        batch_op.alter_column(
            "workflow_id",
            type_=sa.String(length=64),
            existing_type=sa.String(length=128),
            existing_nullable=True,
        )
    with op.batch_alter_table("evaluation_runs") as batch_op:
        batch_op.alter_column(
            "workflow_id",
            type_=sa.String(length=64),
            existing_type=sa.String(length=128),
            existing_nullable=True,
        )
    with op.batch_alter_table("progress_recalculations") as batch_op:
        batch_op.alter_column(
            "workflow_id",
            type_=sa.String(length=64),
            existing_type=sa.String(length=128),
        )
    with op.batch_alter_table("generation_streams") as batch_op:
        batch_op.alter_column(
            "workflow_id",
            type_=sa.String(length=64),
            existing_type=sa.String(length=128),
            existing_nullable=True,
        )
    with op.batch_alter_table("assistant_turns") as batch_op:
        batch_op.alter_column(
            "workflow_id",
            type_=sa.String(length=64),
            existing_type=sa.String(length=128),
        )
    with op.batch_alter_table("recommendation_artifacts") as batch_op:
        batch_op.alter_column(
            "workflow_id",
            type_=sa.String(length=64),
            existing_type=sa.String(length=128),
        )
    with op.batch_alter_table("progression_snapshots") as batch_op:
        batch_op.alter_column(
            "workflow_id",
            type_=sa.String(length=64),
            existing_type=sa.String(length=128),
        )
    with op.batch_alter_table("assessments") as batch_op:
        batch_op.alter_column(
            "workflow_id",
            type_=sa.String(length=64),
            existing_type=sa.String(length=128),
        )
    with op.batch_alter_table("attempts") as batch_op:
        batch_op.alter_column(
            "workflow_id",
            type_=sa.String(length=64),
            existing_type=sa.String(length=128),
        )
    with op.batch_alter_table("practice_sessions") as batch_op:
        batch_op.alter_column(
            "workflow_id",
            type_=sa.String(length=64),
            existing_type=sa.String(length=128),
        )
    with op.batch_alter_table("practice_runs") as batch_op:
        batch_op.alter_column(
            "workflow_id",
            type_=sa.String(length=64),
            existing_type=sa.String(length=128),
        )
    with op.batch_alter_table("content_generation_artifacts") as batch_op:
        batch_op.alter_column(
            "workflow_id",
            type_=sa.String(length=64),
            existing_type=sa.String(length=128),
            existing_nullable=True,
        )
    with op.batch_alter_table("collection_verification_reviews") as batch_op:
        batch_op.alter_column(
            "workflow_id",
            type_=sa.String(length=64),
            existing_type=sa.String(length=128),
            existing_nullable=True,
        )
    with op.batch_alter_table("workflow_events") as batch_op:
        batch_op.alter_column(
            "workflow_id",
            type_=sa.String(length=64),
            existing_type=sa.String(length=128),
            existing_nullable=True,
        )
    _create_dependent_views()
