"""Add organisation_id to prompt_items, scenarios, skills, competencies, rubrics.

Revision ID: 20260329_0019
Revises: 20260328_0018
Create Date: 2026-03-29 00:00:00.000000

"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "20260329_0019"
down_revision = "20260328_0018"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "prompt_items",
        sa.Column("organisation_id", sa.String(length=32), nullable=True, index=True),
    )
    op.create_foreign_key(
        "fk_prompt_items_organisation",
        "prompt_items",
        "organisations",
        ["organisation_id"],
        ["id"],
    )

    op.add_column(
        "scenarios",
        sa.Column("organisation_id", sa.String(length=32), nullable=True, index=True),
    )
    op.create_foreign_key(
        "fk_scenarios_organisation",
        "scenarios",
        "organisations",
        ["organisation_id"],
        ["id"],
    )

    op.add_column(
        "skills",
        sa.Column("organisation_id", sa.String(length=32), nullable=True, index=True),
    )
    op.create_foreign_key(
        "fk_skills_organisation",
        "skills",
        "organisations",
        ["organisation_id"],
        ["id"],
    )
    op.drop_constraint("skills_name_key", "skills", type_="unique")
    op.create_unique_constraint(
        "uq_skill_org_slug",
        "skills",
        ["slug", "organisation_id"],
    )

    op.add_column(
        "competencies",
        sa.Column("organisation_id", sa.String(length=32), nullable=True, index=True),
    )
    op.create_foreign_key(
        "fk_competencies_organisation",
        "competencies",
        "organisations",
        ["organisation_id"],
        ["id"],
    )
    op.drop_constraint("competencies_name_key", "competencies", type_="unique")
    op.create_unique_constraint(
        "uq_competency_org_slug",
        "competencies",
        ["slug", "organisation_id"],
    )

    op.add_column(
        "rubrics",
        sa.Column("organisation_id", sa.String(length=32), nullable=True, index=True),
    )
    op.create_foreign_key(
        "fk_rubrics_organisation",
        "rubrics",
        "organisations",
        ["organisation_id"],
        ["id"],
    )

    op.create_table(
        "org_skill_maps",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("organisation_id", sa.String(length=32), nullable=False, index=True),
        sa.Column("competency_slug", sa.String(length=64), nullable=False, index=True),
        sa.Column("skill_slug", sa.String(length=64), nullable=False, index=True),
        sa.Column("weight", sa.Float(), nullable=False),
        sa.UniqueConstraint(
            "organisation_id",
            "competency_slug",
            "skill_slug",
            name="uq_org_skill_map",
        ),
    )


def downgrade() -> None:
    op.drop_table("org_skill_maps")

    op.drop_constraint("fk_rubrics_organisation", "rubrics", type_="foreignkey")
    op.drop_column("rubrics", "organisation_id")

    op.drop_constraint("uq_competency_org_slug", "competencies", type_="unique")
    op.create_unique_constraint("competencies_name_key", "competencies", ["name"])
    op.drop_constraint("fk_competencies_organisation", "competencies", type_="foreignkey")
    op.drop_column("competencies", "organisation_id")

    op.drop_constraint("fk_skills_organisation", "skills", type_="unique")
    op.create_unique_constraint("skills_name_key", "skills", ["name"])
    op.drop_constraint("fk_skills_organisation", "skills", type_="foreignkey")
    op.drop_column("skills", "organisation_id")

    op.drop_constraint("fk_scenarios_organisation", "scenarios", type_="foreignkey")
    op.drop_column("scenarios", "organisation_id")

    op.drop_constraint("fk_prompt_items_organisation", "prompt_items", type_="foreignkey")
    op.drop_column("prompt_items", "organisation_id")
