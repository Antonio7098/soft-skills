"""Quick-practice session, attempt, and assessment persistence."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "20260325_0003"
down_revision = "20260325_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "practice_sessions",
        sa.Column("id", sa.String(length=32), primary_key=True),
        sa.Column("user_id", sa.String(length=32), nullable=False),
        sa.Column("practice_type", sa.String(length=32), nullable=False),
        sa.Column("content_item_id", sa.String(length=32), nullable=False),
        sa.Column("content_item_type", sa.String(length=32), nullable=False),
        sa.Column("workflow_id", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("delivery_version", sa.String(length=64), nullable=False),
        sa.Column("rubric_id", sa.String(length=128), nullable=False),
        sa.Column("rubric_version", sa.String(length=32), nullable=False),
        sa.Column("prompt_payload", sa.JSON(), nullable=False),
        sa.Column("last_attempt_id", sa.String(length=32), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_practice_sessions_user_id", "practice_sessions", ["user_id"], unique=False)
    op.create_index(
        "ix_practice_sessions_practice_type", "practice_sessions", ["practice_type"], unique=False
    )
    op.create_index(
        "ix_practice_sessions_content_item_id", "practice_sessions", ["content_item_id"], unique=False
    )
    op.create_index("ix_practice_sessions_workflow_id", "practice_sessions", ["workflow_id"], unique=False)
    op.create_index("ix_practice_sessions_status", "practice_sessions", ["status"], unique=False)
    op.create_index("ix_practice_sessions_rubric_id", "practice_sessions", ["rubric_id"], unique=False)

    op.create_table(
        "attempts",
        sa.Column("id", sa.String(length=32), primary_key=True),
        sa.Column("session_id", sa.String(length=32), nullable=False),
        sa.Column("user_id", sa.String(length=32), nullable=False),
        sa.Column("workflow_id", sa.String(length=64), nullable=False),
        sa.Column("practice_type", sa.String(length=32), nullable=False),
        sa.Column("content_item_id", sa.String(length=32), nullable=False),
        sa.Column("content_item_type", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("response_mode", sa.String(length=32), nullable=False),
        sa.Column("response_text", sa.Text(), nullable=True),
        sa.Column("delivery_version", sa.String(length=64), nullable=False),
        sa.Column("rubric_id", sa.String(length=128), nullable=False),
        sa.Column("rubric_version", sa.String(length=32), nullable=False),
        sa.Column("assessment_id", sa.String(length=32), nullable=True),
        sa.Column("last_error_code", sa.String(length=32), nullable=True),
        sa.Column("trace_id", sa.String(length=32), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("assessed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_attempts_session_id", "attempts", ["session_id"], unique=False)
    op.create_index("ix_attempts_user_id", "attempts", ["user_id"], unique=False)
    op.create_index("ix_attempts_workflow_id", "attempts", ["workflow_id"], unique=False)
    op.create_index("ix_attempts_practice_type", "attempts", ["practice_type"], unique=False)
    op.create_index("ix_attempts_content_item_id", "attempts", ["content_item_id"], unique=False)
    op.create_index("ix_attempts_status", "attempts", ["status"], unique=False)
    op.create_index("ix_attempts_rubric_id", "attempts", ["rubric_id"], unique=False)
    op.create_index("ix_attempts_assessment_id", "attempts", ["assessment_id"], unique=False)
    op.create_index("ix_attempts_trace_id", "attempts", ["trace_id"], unique=False)

    op.create_table(
        "assessments",
        sa.Column("id", sa.String(length=32), primary_key=True),
        sa.Column("attempt_id", sa.String(length=32), nullable=False),
        sa.Column("session_id", sa.String(length=32), nullable=False),
        sa.Column("user_id", sa.String(length=32), nullable=False),
        sa.Column("workflow_id", sa.String(length=64), nullable=False),
        sa.Column("practice_type", sa.String(length=32), nullable=False),
        sa.Column("validation_status", sa.String(length=32), nullable=False),
        sa.Column("prompt_version", sa.String(length=64), nullable=False),
        sa.Column("rubric_id", sa.String(length=128), nullable=False),
        sa.Column("rubric_version", sa.String(length=32), nullable=False),
        sa.Column("schema_version", sa.String(length=64), nullable=False),
        sa.Column("config_version", sa.String(length=64), nullable=False),
        sa.Column("provider", sa.String(length=64), nullable=False),
        sa.Column("model_slug", sa.String(length=128), nullable=False),
        sa.Column("overall_score", sa.Integer(), nullable=True),
        sa.Column("skill_scores", sa.JSON(), nullable=False),
        sa.Column("evidence", sa.JSON(), nullable=False),
        sa.Column("rationale", sa.Text(), nullable=True),
        sa.Column("strengths", sa.JSON(), nullable=False),
        sa.Column("weaknesses", sa.JSON(), nullable=False),
        sa.Column("next_actions", sa.JSON(), nullable=False),
        sa.Column("raw_payload", sa.JSON(), nullable=False),
        sa.Column("rejection_code", sa.String(length=32), nullable=True),
        sa.Column("trace_id", sa.String(length=32), nullable=False),
        sa.Column("pipeline_run_id", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_assessments_attempt_id", "assessments", ["attempt_id"], unique=False)
    op.create_index("ix_assessments_session_id", "assessments", ["session_id"], unique=False)
    op.create_index("ix_assessments_user_id", "assessments", ["user_id"], unique=False)
    op.create_index("ix_assessments_workflow_id", "assessments", ["workflow_id"], unique=False)
    op.create_index("ix_assessments_practice_type", "assessments", ["practice_type"], unique=False)
    op.create_index(
        "ix_assessments_validation_status", "assessments", ["validation_status"], unique=False
    )
    op.create_index("ix_assessments_rubric_id", "assessments", ["rubric_id"], unique=False)
    op.create_index("ix_assessments_provider", "assessments", ["provider"], unique=False)
    op.create_index("ix_assessments_model_slug", "assessments", ["model_slug"], unique=False)
    op.create_index("ix_assessments_trace_id", "assessments", ["trace_id"], unique=False)
    op.create_index("ix_assessments_pipeline_run_id", "assessments", ["pipeline_run_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_assessments_pipeline_run_id", table_name="assessments")
    op.drop_index("ix_assessments_trace_id", table_name="assessments")
    op.drop_index("ix_assessments_model_slug", table_name="assessments")
    op.drop_index("ix_assessments_provider", table_name="assessments")
    op.drop_index("ix_assessments_rubric_id", table_name="assessments")
    op.drop_index("ix_assessments_validation_status", table_name="assessments")
    op.drop_index("ix_assessments_practice_type", table_name="assessments")
    op.drop_index("ix_assessments_workflow_id", table_name="assessments")
    op.drop_index("ix_assessments_user_id", table_name="assessments")
    op.drop_index("ix_assessments_session_id", table_name="assessments")
    op.drop_index("ix_assessments_attempt_id", table_name="assessments")
    op.drop_table("assessments")

    op.drop_index("ix_attempts_trace_id", table_name="attempts")
    op.drop_index("ix_attempts_assessment_id", table_name="attempts")
    op.drop_index("ix_attempts_rubric_id", table_name="attempts")
    op.drop_index("ix_attempts_status", table_name="attempts")
    op.drop_index("ix_attempts_content_item_id", table_name="attempts")
    op.drop_index("ix_attempts_practice_type", table_name="attempts")
    op.drop_index("ix_attempts_workflow_id", table_name="attempts")
    op.drop_index("ix_attempts_user_id", table_name="attempts")
    op.drop_index("ix_attempts_session_id", table_name="attempts")
    op.drop_table("attempts")

    op.drop_index("ix_practice_sessions_rubric_id", table_name="practice_sessions")
    op.drop_index("ix_practice_sessions_status", table_name="practice_sessions")
    op.drop_index("ix_practice_sessions_workflow_id", table_name="practice_sessions")
    op.drop_index("ix_practice_sessions_content_item_id", table_name="practice_sessions")
    op.drop_index("ix_practice_sessions_practice_type", table_name="practice_sessions")
    op.drop_index("ix_practice_sessions_user_id", table_name="practice_sessions")
    op.drop_table("practice_sessions")
