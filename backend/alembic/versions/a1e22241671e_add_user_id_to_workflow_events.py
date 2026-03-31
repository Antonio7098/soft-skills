"""add_user_id_to_workflow_events"""

revision = "a1e22241671e"
down_revision = "scenario_questions"
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade() -> None:
    op.add_column(
        "workflow_events",
        sa.Column("user_id", sa.String(64), nullable=True),
    )
    op.create_index(
        op.f("ix_workflow_events_user_id"),
        "workflow_events",
        ["user_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_workflow_events_user_id"), table_name="workflow_events")
    op.drop_column("workflow_events", "user_id")
