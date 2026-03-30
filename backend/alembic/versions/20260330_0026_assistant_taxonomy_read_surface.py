"""Add assistant-safe taxonomy SQL views.

Revision ID: 20260330_0026
Revises: 20260330_0025
Create Date: 2026-03-30 14:00:00.000000

"""

from __future__ import annotations

from alembic import op

revision = "20260330_0026"
down_revision = "20260330_0025"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("DROP VIEW IF EXISTS assistant_safe_competencies_v")
    op.execute("DROP VIEW IF EXISTS assistant_safe_skills_v")

    op.execute(
        """
        CREATE VIEW assistant_safe_skills_v AS
        SELECT
            s.organisation_id,
            s.slug AS skill_slug,
            s.name,
            s.description
        FROM skills AS s
        """
    )

    op.execute(
        """
        CREATE VIEW assistant_safe_competencies_v AS
        SELECT
            c.organisation_id,
            c.slug AS competency_slug,
            c.name,
            c.description,
            CASE
                WHEN c.organisation_id IS NULL THEN (
                    SELECT json_group_array(skill_slug)
                    FROM (
                        SELECT csm.skill_slug AS skill_slug
                        FROM competency_skill_map AS csm
                        WHERE csm.competency_slug = c.slug
                        ORDER BY csm.skill_slug
                    )
                )
                ELSE (
                    SELECT json_group_array(skill_slug)
                    FROM (
                        SELECT osm.skill_slug AS skill_slug
                        FROM org_skill_maps AS osm
                        WHERE osm.organisation_id = c.organisation_id
                          AND osm.competency_slug = c.slug
                        ORDER BY osm.skill_slug
                    )
                )
            END AS skill_slugs
        FROM competencies AS c
        """
    )


def downgrade() -> None:
    op.execute("DROP VIEW IF EXISTS assistant_safe_competencies_v")
    op.execute("DROP VIEW IF EXISTS assistant_safe_skills_v")
