"""Admin learner relationship access grants."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "20260326_0007"
down_revision = "20260326_0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "admin_learner_relationships",
        sa.Column("learner_user_id", sa.String(length=32), primary_key=True),
        sa.Column("admin_user_id", sa.String(length=32), primary_key=True),
        sa.Column("relationship_type", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_admin_learner_relationships_relationship_type",
        "admin_learner_relationships",
        ["relationship_type"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_admin_learner_relationships_relationship_type",
        table_name="admin_learner_relationships",
    )
    op.drop_table("admin_learner_relationships")
