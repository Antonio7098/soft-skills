"""Add learner assistant read SQL views.

Revision ID: 20260330_0022
Revises: 20260329_0021
Create Date: 2026-03-30 09:00:00.000000

"""

from __future__ import annotations

from alembic import op

revision = "20260330_0022"
down_revision = "20260329_0021"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("DROP VIEW IF EXISTS assistant_safe_recommendations_v")
    op.execute("DROP VIEW IF EXISTS assistant_safe_progress_snapshots_v")
    op.execute("DROP VIEW IF EXISTS assistant_safe_attempt_summaries_v")
    op.execute("DROP VIEW IF EXISTS assistant_safe_collections_v")

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
        WHERE c.lifecycle_state = 'published'
        """
    )

    op.execute(
        """
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
        """
    )

    op.execute(
        """
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
        """
    )

    op.execute(
        """
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
        """
    )


def downgrade() -> None:
    op.execute("DROP VIEW IF EXISTS assistant_safe_recommendations_v")
    op.execute("DROP VIEW IF EXISTS assistant_safe_progress_snapshots_v")
    op.execute("DROP VIEW IF EXISTS assistant_safe_attempt_summaries_v")
    op.execute("DROP VIEW IF EXISTS assistant_safe_collections_v")
