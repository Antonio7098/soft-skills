"""sprint15_phase1_prompt_rubric_versioning

Add FK columns for parent-child prompt/rubric model.
Phase 1 of sprint 15.

Revision ID: sprint15_phase1
Revises: 4ce9c9df899b
Create Date: 2026-03-30

"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "sprint15_phase1"
down_revision = "4ce9c9df899b"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("assessments") as batch_op:
        batch_op.add_column(
            sa.Column(
                "rubric_version_id",
                sa.Integer(),
                nullable=True,
            ),
        )
        batch_op.create_index(
            "ix_assessments_rubric_version_id",
            ["rubric_version_id"],
            unique=False,
        )

    with op.batch_alter_table("attempts") as batch_op:
        batch_op.add_column(
            sa.Column(
                "rubric_version_id",
                sa.Integer(),
                nullable=True,
            ),
        )
        batch_op.create_index(
            "ix_attempts_rubric_version_id",
            ["rubric_version_id"],
            unique=False,
        )

    with op.batch_alter_table("practice_sessions") as batch_op:
        batch_op.add_column(
            sa.Column(
                "rubric_version_id",
                sa.Integer(),
                nullable=True,
            ),
        )
        batch_op.create_index(
            "ix_practice_sessions_rubric_version_id",
            ["rubric_version_id"],
            unique=False,
        )


def downgrade() -> None:
    with op.batch_alter_table("practice_sessions") as batch_op:
        batch_op.drop_index("ix_practice_sessions_rubric_version_id")
        batch_op.drop_column("rubric_version_id")

    with op.batch_alter_table("attempts") as batch_op:
        batch_op.drop_index("ix_attempts_rubric_version_id")
        batch_op.drop_column("rubric_version_id")

    with op.batch_alter_table("assessments") as batch_op:
        batch_op.drop_index("ix_assessments_rubric_version_id")
        batch_op.drop_column("rubric_version_id")
