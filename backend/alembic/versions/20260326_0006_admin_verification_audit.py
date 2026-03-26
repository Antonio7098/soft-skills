"""Admin verification audit persistence."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "20260326_0006"
down_revision = "20260326_0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "collection_verification_reviews",
        sa.Column("id", sa.String(length=32), primary_key=True),
        sa.Column("collection_id", sa.String(length=32), nullable=False),
        sa.Column("reviewer_user_id", sa.String(length=32), nullable=False),
        sa.Column("previous_verification_state", sa.String(length=32), nullable=False),
        sa.Column("next_verification_state", sa.String(length=32), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("request_id", sa.String(length=32), nullable=True),
        sa.Column("trace_id", sa.String(length=32), nullable=True),
        sa.Column("workflow_id", sa.String(length=64), nullable=True),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_collection_verification_reviews_collection_id",
        "collection_verification_reviews",
        ["collection_id"],
        unique=False,
    )
    op.create_index(
        "ix_collection_verification_reviews_reviewer_user_id",
        "collection_verification_reviews",
        ["reviewer_user_id"],
        unique=False,
    )
    op.create_index(
        "ix_collection_verification_reviews_next_verification_state",
        "collection_verification_reviews",
        ["next_verification_state"],
        unique=False,
    )
    op.create_index(
        "ix_collection_verification_reviews_request_id",
        "collection_verification_reviews",
        ["request_id"],
        unique=False,
    )
    op.create_index(
        "ix_collection_verification_reviews_trace_id",
        "collection_verification_reviews",
        ["trace_id"],
        unique=False,
    )
    op.create_index(
        "ix_collection_verification_reviews_workflow_id",
        "collection_verification_reviews",
        ["workflow_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_collection_verification_reviews_workflow_id",
        table_name="collection_verification_reviews",
    )
    op.drop_index(
        "ix_collection_verification_reviews_trace_id",
        table_name="collection_verification_reviews",
    )
    op.drop_index(
        "ix_collection_verification_reviews_request_id",
        table_name="collection_verification_reviews",
    )
    op.drop_index(
        "ix_collection_verification_reviews_next_verification_state",
        table_name="collection_verification_reviews",
    )
    op.drop_index(
        "ix_collection_verification_reviews_reviewer_user_id",
        table_name="collection_verification_reviews",
    )
    op.drop_index(
        "ix_collection_verification_reviews_collection_id",
        table_name="collection_verification_reviews",
    )
    op.drop_table("collection_verification_reviews")
