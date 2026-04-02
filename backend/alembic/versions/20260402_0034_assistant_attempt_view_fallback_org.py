"""Allow assistant attempt summaries to fall back without membership rows.

Revision ID: 20260402_0034
Revises: 20260401_0033
Create Date: 2026-04-02 14:05:00.000000
"""

from __future__ import annotations

from alembic import context as _context
from alembic import op


revision = "20260402_0034"
down_revision = "20260401_0033"
branch_labels = None
depends_on = None


def _sql_for_dialect(*, sqlite_sql: str, postgres_sql: str) -> str:
    if _context.get_context().dialect.name == "postgresql":
        return postgres_sql
    return sqlite_sql


def upgrade() -> None:
    op.execute("DROP VIEW IF EXISTS assistant_safe_attempt_summaries_v")
    op.execute(
        _sql_for_dialect(
            sqlite_sql="""
        CREATE VIEW assistant_safe_attempt_summaries_v AS
        SELECT
            COALESCE(
                om.organisation_id,
                (
                    SELECT c.organisation_id
                    FROM collections AS c
                    WHERE c.id = a.content_item_id
                    LIMIT 1
                )
            ) AS organisation_id,
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
        LEFT JOIN organisation_memberships AS om
          ON om.user_id = a.user_id
        LEFT JOIN assessments AS ass
          ON ass.id = a.assessment_id
            """,
            postgres_sql="""
        CREATE VIEW assistant_safe_attempt_summaries_v AS
        SELECT
            COALESCE(
                om.organisation_id,
                (
                    SELECT c.organisation_id
                    FROM collections AS c
                    WHERE c.id = a.content_item_id
                    LIMIT 1
                )
            ) AS organisation_id,
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
        LEFT JOIN organisation_memberships AS om
          ON om.user_id = a.user_id
        LEFT JOIN assessments AS ass
          ON ass.id = a.assessment_id
            """,
        )
    )


def downgrade() -> None:
    op.execute("DROP VIEW IF EXISTS assistant_safe_attempt_summaries_v")
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
