"""Add assistant human approval workflow persistence.

Revision ID: 20260329_0020
Revises: 20260329_0019
Create Date: 2026-03-29 00:30:00.000000

"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "20260329_0020"
down_revision = "20260329_0019"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "assistant_approval_requests",
        sa.Column("id", sa.String(length=32), primary_key=True),
        sa.Column("session_id", sa.String(length=32), nullable=False),
        sa.Column("turn_id", sa.String(length=32), nullable=False),
        sa.Column("tool_call_id", sa.String(length=32), nullable=False),
        sa.Column("user_id", sa.String(length=32), nullable=False),
        sa.Column("tool_name", sa.String(length=128), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("approval_message", sa.Text(), nullable=False),
        sa.Column("payload_summary", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("decision_reason", sa.Text(), nullable=True),
        sa.Column("decided_by_user_id", sa.String(length=32), nullable=True),
        sa.Column("requested_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "ix_assistant_approval_requests_session_id",
        "assistant_approval_requests",
        ["session_id"],
    )
    op.create_index(
        "ix_assistant_approval_requests_turn_id",
        "assistant_approval_requests",
        ["turn_id"],
    )
    op.create_index(
        "ix_assistant_approval_requests_tool_call_id",
        "assistant_approval_requests",
        ["tool_call_id"],
    )
    op.create_index(
        "ix_assistant_approval_requests_user_id",
        "assistant_approval_requests",
        ["user_id"],
    )
    op.create_index(
        "ix_assistant_approval_requests_tool_name",
        "assistant_approval_requests",
        ["tool_name"],
    )
    op.create_index(
        "ix_assistant_approval_requests_status",
        "assistant_approval_requests",
        ["status"],
    )
    op.create_index(
        "ix_assistant_approval_requests_decided_by_user_id",
        "assistant_approval_requests",
        ["decided_by_user_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_assistant_approval_requests_decided_by_user_id",
        table_name="assistant_approval_requests",
    )
    op.drop_index(
        "ix_assistant_approval_requests_status",
        table_name="assistant_approval_requests",
    )
    op.drop_index(
        "ix_assistant_approval_requests_tool_name",
        table_name="assistant_approval_requests",
    )
    op.drop_index(
        "ix_assistant_approval_requests_user_id",
        table_name="assistant_approval_requests",
    )
    op.drop_index(
        "ix_assistant_approval_requests_tool_call_id",
        table_name="assistant_approval_requests",
    )
    op.drop_index(
        "ix_assistant_approval_requests_turn_id",
        table_name="assistant_approval_requests",
    )
    op.drop_index(
        "ix_assistant_approval_requests_session_id",
        table_name="assistant_approval_requests",
    )
    op.drop_table("assistant_approval_requests")
