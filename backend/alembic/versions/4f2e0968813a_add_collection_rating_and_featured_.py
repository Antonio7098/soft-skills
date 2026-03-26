"""add_collection_rating_and_featured_fields"""

revision = "4f2e0968813a"
down_revision = "20260326_0013"
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade() -> None:
    op.create_table(
        "collection_ratings",
        sa.Column("user_id", sa.String(length=32), nullable=False),
        sa.Column("collection_id", sa.String(length=32), nullable=False),
        sa.Column("rating", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("user_id", "collection_id"),
    )
    op.create_index(
        op.f("ix_collection_ratings_rating"), "collection_ratings", ["rating"], unique=False
    )
    op.add_column("collections", sa.Column("avg_rating", sa.Float(), nullable=True))
    op.add_column(
        "collections", sa.Column("rating_count", sa.Integer(), nullable=False, server_default="0")
    )
    op.add_column(
        "collections", sa.Column("featured", sa.Boolean(), nullable=False, server_default="0")
    )


def downgrade() -> None:
    op.drop_column("collections", "featured")
    op.drop_column("collections", "rating_count")
    op.drop_column("collections", "avg_rating")
    op.drop_index(op.f("ix_collection_ratings_rating"), table_name="collection_ratings")
    op.drop_table("collection_ratings")
