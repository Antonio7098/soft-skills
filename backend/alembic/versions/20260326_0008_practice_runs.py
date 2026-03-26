"""Aggregate practice runs."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "20260326_0008"
down_revision = "20260326_0007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "practice_runs",
        sa.Column("id", sa.String(length=32), primary_key=True),
        sa.Column("user_id", sa.String(length=32), nullable=False),
        sa.Column("workflow_id", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("total_items", sa.Integer(), nullable=False),
        sa.Column("completed_items", sa.Integer(), nullable=False),
        sa.Column("validated_items", sa.Integer(), nullable=False),
        sa.Column("failed_items", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_practice_runs_user_id", "practice_runs", ["user_id"], unique=False)
    op.create_index("ix_practice_runs_workflow_id", "practice_runs", ["workflow_id"], unique=False)
    op.create_index("ix_practice_runs_status", "practice_runs", ["status"], unique=False)

    op.add_column(
        "practice_sessions",
        sa.Column("practice_run_id", sa.String(length=32), nullable=True),
    )
    op.add_column(
        "practice_sessions",
        sa.Column("sequence_index", sa.Integer(), nullable=True),
    )
    op.create_index(
        "ix_practice_sessions_practice_run_id",
        "practice_sessions",
        ["practice_run_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_practice_sessions_practice_run_id", table_name="practice_sessions")
    op.drop_column("practice_sessions", "sequence_index")
    op.drop_column("practice_sessions", "practice_run_id")

    op.drop_index("ix_practice_runs_status", table_name="practice_runs")
    op.drop_index("ix_practice_runs_workflow_id", table_name="practice_runs")
    op.drop_index("ix_practice_runs_user_id", table_name="practice_runs")
    op.drop_table("practice_runs")
