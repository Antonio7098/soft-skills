"""Add organisation_id to prompt_items, scenarios, skills, competencies, rubrics.

Revision ID: 20260329_0019
Revises: 20260328_0018_user_management
Create Date: 2026-03-29 00:00:00.000000

"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "20260329_0019"
down_revision = "20260328_0018_user_management"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("prompt_items") as batch_op:
        batch_op.alter_column("collection_id", existing_type=sa.String(length=32), nullable=True)
        batch_op.add_column(sa.Column("organisation_id", sa.String(length=32), nullable=True))
        batch_op.create_index("ix_prompt_items_organisation_id", ["organisation_id"])

    with op.batch_alter_table("scenarios") as batch_op:
        batch_op.alter_column("collection_id", existing_type=sa.String(length=32), nullable=True)
        batch_op.add_column(sa.Column("organisation_id", sa.String(length=32), nullable=True))
        batch_op.create_index("ix_scenarios_organisation_id", ["organisation_id"])

    with op.batch_alter_table("skills") as batch_op:
        batch_op.add_column(sa.Column("organisation_id", sa.String(length=32), nullable=True))
        batch_op.create_index("ix_skills_organisation_id", ["organisation_id"])
        batch_op.create_unique_constraint(
            "uq_skill_org_slug",
            ["slug", "organisation_id"],
        )

    with op.batch_alter_table("competencies") as batch_op:
        batch_op.add_column(sa.Column("organisation_id", sa.String(length=32), nullable=True))
        batch_op.create_index("ix_competencies_organisation_id", ["organisation_id"])
        batch_op.create_unique_constraint(
            "uq_competency_org_slug",
            ["slug", "organisation_id"],
        )

    with op.batch_alter_table("rubrics") as batch_op:
        batch_op.add_column(sa.Column("organisation_id", sa.String(length=32), nullable=True))
        batch_op.create_index("ix_rubrics_organisation_id", ["organisation_id"])

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

    with op.batch_alter_table("rubrics") as batch_op:
        batch_op.drop_index("ix_rubrics_organisation_id")
        batch_op.drop_column("organisation_id")

    with op.batch_alter_table("competencies") as batch_op:
        batch_op.drop_constraint("uq_competency_org_slug", type_="unique")
        batch_op.drop_index("ix_competencies_organisation_id")
        batch_op.drop_column("organisation_id")

    with op.batch_alter_table("skills") as batch_op:
        batch_op.drop_constraint("uq_skill_org_slug", type_="unique")
        batch_op.drop_index("ix_skills_organisation_id")
        batch_op.drop_column("organisation_id")

    with op.batch_alter_table("scenarios") as batch_op:
        batch_op.drop_index("ix_scenarios_organisation_id")
        batch_op.drop_column("organisation_id")
        batch_op.alter_column("collection_id", existing_type=sa.String(length=32), nullable=False)

    with op.batch_alter_table("prompt_items") as batch_op:
        batch_op.drop_index("ix_prompt_items_organisation_id")
        batch_op.drop_column("organisation_id")
        batch_op.alter_column("collection_id", existing_type=sa.String(length=32), nullable=False)
