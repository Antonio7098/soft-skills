"""Refresh assistant collections SQL surface for current lifecycle semantics.

Revision ID: 20260330_0025
Revises: 20260330_0024
Create Date: 2026-03-30 13:45:00.000000

"""

from __future__ import annotations

from alembic import op

revision = "20260330_0025"
down_revision = "20260330_0024"
branch_labels = None
depends_on = None


def upgrade() -> None:
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
            c.lifecycle_state,
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
        """
    )


def downgrade() -> None:
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
