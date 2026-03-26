"""Assistant runtime persistence."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "20260326_0010"
down_revision = "20260326_0009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "assistant_sessions",
        sa.Column("id", sa.String(length=32), primary_key=True),
        sa.Column("user_id", sa.String(length=32), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("metadata_payload", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_assistant_sessions_user_id", "assistant_sessions", ["user_id"], unique=False)
    op.create_index("ix_assistant_sessions_status", "assistant_sessions", ["status"], unique=False)

    op.create_table(
        "assistant_turns",
        sa.Column("id", sa.String(length=32), primary_key=True),
        sa.Column("session_id", sa.String(length=32), nullable=False),
        sa.Column("user_id", sa.String(length=32), nullable=False),
        sa.Column("request_id", sa.String(length=32), nullable=True),
        sa.Column("trace_id", sa.String(length=32), nullable=True),
        sa.Column("workflow_id", sa.String(length=64), nullable=False),
        sa.Column("pipeline_run_id", sa.String(length=32), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("stream_token", sa.String(length=64), nullable=False),
        sa.Column("user_message_id", sa.String(length=32), nullable=True),
        sa.Column("assistant_message_id", sa.String(length=32), nullable=True),
        sa.Column("last_error_code", sa.String(length=32), nullable=True),
        sa.Column("cancel_reason", sa.Text(), nullable=True),
        sa.Column("tool_call_count", sa.Integer(), nullable=False),
        sa.Column("metadata_payload", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_assistant_turns_session_id", "assistant_turns", ["session_id"], unique=False)
    op.create_index("ix_assistant_turns_user_id", "assistant_turns", ["user_id"], unique=False)
    op.create_index("ix_assistant_turns_request_id", "assistant_turns", ["request_id"], unique=False)
    op.create_index("ix_assistant_turns_trace_id", "assistant_turns", ["trace_id"], unique=False)
    op.create_index("ix_assistant_turns_workflow_id", "assistant_turns", ["workflow_id"], unique=False)
    op.create_index(
        "ix_assistant_turns_pipeline_run_id",
        "assistant_turns",
        ["pipeline_run_id"],
        unique=False,
    )
    op.create_index("ix_assistant_turns_status", "assistant_turns", ["status"], unique=False)
    op.create_index("ix_assistant_turns_stream_token", "assistant_turns", ["stream_token"], unique=True)

    op.create_table(
        "assistant_messages",
        sa.Column("id", sa.String(length=32), primary_key=True),
        sa.Column("session_id", sa.String(length=32), nullable=False),
        sa.Column("turn_id", sa.String(length=32), nullable=False),
        sa.Column("user_id", sa.String(length=32), nullable=False),
        sa.Column("role", sa.String(length=32), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("metadata_payload", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_assistant_messages_session_id", "assistant_messages", ["session_id"], unique=False)
    op.create_index("ix_assistant_messages_turn_id", "assistant_messages", ["turn_id"], unique=False)
    op.create_index("ix_assistant_messages_user_id", "assistant_messages", ["user_id"], unique=False)
    op.create_index("ix_assistant_messages_role", "assistant_messages", ["role"], unique=False)

    op.create_table(
        "assistant_tool_calls",
        sa.Column("id", sa.String(length=32), primary_key=True),
        sa.Column("session_id", sa.String(length=32), nullable=False),
        sa.Column("turn_id", sa.String(length=32), nullable=False),
        sa.Column("user_id", sa.String(length=32), nullable=False),
        sa.Column("tool_name", sa.String(length=128), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("args_payload", sa.JSON(), nullable=False),
        sa.Column("result_payload", sa.JSON(), nullable=True),
        sa.Column("error_code", sa.String(length=32), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("child_run_id", sa.String(length=32), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "ix_assistant_tool_calls_session_id",
        "assistant_tool_calls",
        ["session_id"],
        unique=False,
    )
    op.create_index("ix_assistant_tool_calls_turn_id", "assistant_tool_calls", ["turn_id"], unique=False)
    op.create_index("ix_assistant_tool_calls_user_id", "assistant_tool_calls", ["user_id"], unique=False)
    op.create_index(
        "ix_assistant_tool_calls_tool_name",
        "assistant_tool_calls",
        ["tool_name"],
        unique=False,
    )
    op.create_index("ix_assistant_tool_calls_status", "assistant_tool_calls", ["status"], unique=False)
    op.create_index(
        "ix_assistant_tool_calls_child_run_id",
        "assistant_tool_calls",
        ["child_run_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_assistant_tool_calls_child_run_id", table_name="assistant_tool_calls")
    op.drop_index("ix_assistant_tool_calls_status", table_name="assistant_tool_calls")
    op.drop_index("ix_assistant_tool_calls_tool_name", table_name="assistant_tool_calls")
    op.drop_index("ix_assistant_tool_calls_user_id", table_name="assistant_tool_calls")
    op.drop_index("ix_assistant_tool_calls_turn_id", table_name="assistant_tool_calls")
    op.drop_index("ix_assistant_tool_calls_session_id", table_name="assistant_tool_calls")
    op.drop_table("assistant_tool_calls")

    op.drop_index("ix_assistant_messages_role", table_name="assistant_messages")
    op.drop_index("ix_assistant_messages_user_id", table_name="assistant_messages")
    op.drop_index("ix_assistant_messages_turn_id", table_name="assistant_messages")
    op.drop_index("ix_assistant_messages_session_id", table_name="assistant_messages")
    op.drop_table("assistant_messages")

    op.drop_index("ix_assistant_turns_stream_token", table_name="assistant_turns")
    op.drop_index("ix_assistant_turns_status", table_name="assistant_turns")
    op.drop_index("ix_assistant_turns_pipeline_run_id", table_name="assistant_turns")
    op.drop_index("ix_assistant_turns_workflow_id", table_name="assistant_turns")
    op.drop_index("ix_assistant_turns_trace_id", table_name="assistant_turns")
    op.drop_index("ix_assistant_turns_request_id", table_name="assistant_turns")
    op.drop_index("ix_assistant_turns_user_id", table_name="assistant_turns")
    op.drop_index("ix_assistant_turns_session_id", table_name="assistant_turns")
    op.drop_table("assistant_turns")

    op.drop_index("ix_assistant_sessions_status", table_name="assistant_sessions")
    op.drop_index("ix_assistant_sessions_user_id", table_name="assistant_sessions")
    op.drop_table("assistant_sessions")
