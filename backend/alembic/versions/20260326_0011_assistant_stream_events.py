"""Assistant stream event persistence."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "20260326_0011"
down_revision = "20260326_0010"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "assistant_stream_events",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("event_id", sa.String(length=32), nullable=False),
        sa.Column("session_id", sa.String(length=32), nullable=False),
        sa.Column("turn_id", sa.String(length=32), nullable=False),
        sa.Column("user_id", sa.String(length=32), nullable=False),
        sa.Column("sequence_number", sa.Integer(), nullable=False),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("emitted_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_assistant_stream_events_event_id",
        "assistant_stream_events",
        ["event_id"],
        unique=True,
    )
    op.create_index(
        "ix_assistant_stream_events_session_id",
        "assistant_stream_events",
        ["session_id"],
        unique=False,
    )
    op.create_index(
        "ix_assistant_stream_events_turn_id",
        "assistant_stream_events",
        ["turn_id"],
        unique=False,
    )
    op.create_index(
        "ix_assistant_stream_events_user_id",
        "assistant_stream_events",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        "ix_assistant_stream_events_event_type",
        "assistant_stream_events",
        ["event_type"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_assistant_stream_events_event_type", table_name="assistant_stream_events")
    op.drop_index("ix_assistant_stream_events_user_id", table_name="assistant_stream_events")
    op.drop_index("ix_assistant_stream_events_turn_id", table_name="assistant_stream_events")
    op.drop_index("ix_assistant_stream_events_session_id", table_name="assistant_stream_events")
    op.drop_index("ix_assistant_stream_events_event_id", table_name="assistant_stream_events")
    op.drop_table("assistant_stream_events")
