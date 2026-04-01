"""Persist generation websocket sessions and events.

Revision ID: 20260401_0032
Revises: 20260401_0031
Create Date: 2026-04-01 19:45:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260401_0032"
down_revision = "20260401_0031"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "generation_streams",
        sa.Column("generation_id", sa.String(length=32), primary_key=True),
        sa.Column("user_id", sa.String(length=32), nullable=False),
        sa.Column("request_id", sa.String(length=32), nullable=True),
        sa.Column("trace_id", sa.String(length=32), nullable=True),
        sa.Column("workflow_id", sa.String(length=64), nullable=True),
        sa.Column("mode", sa.String(length=32), nullable=False),
        sa.Column("stream_token", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("cancel_reason", sa.Text(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("collection_id", sa.String(length=32), nullable=True),
        sa.Column("generation_artifact_id", sa.String(length=32), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("stream_token"),
    )
    op.create_index("ix_generation_streams_user_id", "generation_streams", ["user_id"])
    op.create_index("ix_generation_streams_request_id", "generation_streams", ["request_id"])
    op.create_index("ix_generation_streams_trace_id", "generation_streams", ["trace_id"])
    op.create_index("ix_generation_streams_workflow_id", "generation_streams", ["workflow_id"])
    op.create_index("ix_generation_streams_mode", "generation_streams", ["mode"])
    op.create_index("ix_generation_streams_stream_token", "generation_streams", ["stream_token"])
    op.create_index("ix_generation_streams_status", "generation_streams", ["status"])

    op.create_table(
        "generation_stream_events",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("event_id", sa.String(length=32), nullable=False),
        sa.Column("generation_id", sa.String(length=32), nullable=False),
        sa.Column("user_id", sa.String(length=32), nullable=False),
        sa.Column("sequence_number", sa.Integer(), nullable=False),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column("stage", sa.String(length=64), nullable=False),
        sa.Column("progress_percent", sa.Float(), nullable=False, server_default="0"),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("emitted_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("event_id"),
    )
    op.create_index(
        "ix_generation_stream_events_event_id",
        "generation_stream_events",
        ["event_id"],
    )
    op.create_index(
        "ix_generation_stream_events_generation_id",
        "generation_stream_events",
        ["generation_id"],
    )
    op.create_index(
        "ix_generation_stream_events_user_id",
        "generation_stream_events",
        ["user_id"],
    )
    op.create_index(
        "ix_generation_stream_events_event_type",
        "generation_stream_events",
        ["event_type"],
    )
    op.create_index(
        "ix_generation_stream_events_stage",
        "generation_stream_events",
        ["stage"],
    )


def downgrade() -> None:
    op.drop_index("ix_generation_stream_events_stage", table_name="generation_stream_events")
    op.drop_index(
        "ix_generation_stream_events_event_type",
        table_name="generation_stream_events",
    )
    op.drop_index("ix_generation_stream_events_user_id", table_name="generation_stream_events")
    op.drop_index(
        "ix_generation_stream_events_generation_id",
        table_name="generation_stream_events",
    )
    op.drop_index("ix_generation_stream_events_event_id", table_name="generation_stream_events")
    op.drop_table("generation_stream_events")

    op.drop_index("ix_generation_streams_status", table_name="generation_streams")
    op.drop_index("ix_generation_streams_stream_token", table_name="generation_streams")
    op.drop_index("ix_generation_streams_mode", table_name="generation_streams")
    op.drop_index("ix_generation_streams_workflow_id", table_name="generation_streams")
    op.drop_index("ix_generation_streams_trace_id", table_name="generation_streams")
    op.drop_index("ix_generation_streams_request_id", table_name="generation_streams")
    op.drop_index("ix_generation_streams_user_id", table_name="generation_streams")
    op.drop_table("generation_streams")
