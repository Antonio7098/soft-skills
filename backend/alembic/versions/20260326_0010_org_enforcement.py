"""Organisation enforcement - tenant isolation models."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "20260326_0010"
down_revision = "20260326_0009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "organisations",
        sa.Column("id", sa.String(length=32), primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("slug", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_organisations_slug", "organisations", ["slug"], unique=True)

    op.create_table(
        "organisation_memberships",
        sa.Column("organisation_id", sa.String(length=32), primary_key=True),
        sa.Column("user_id", sa.String(length=32), primary_key=True),
        sa.Column("role", sa.String(length=32), nullable=False),
        sa.Column("joined_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_organisation_memberships_user_id", "organisation_memberships", ["user_id"], unique=False
    )

    with op.batch_alter_table("collections") as batch_op:
        batch_op.add_column(sa.Column("organisation_id", sa.String(length=32), nullable=True))
        batch_op.create_index("ix_collections_organisation_id", ["organisation_id"], unique=False)

    with op.batch_alter_table("user_accounts") as batch_op:
        batch_op.drop_index("ix_user_accounts_role")
        batch_op.drop_column("role")


def downgrade() -> None:
    with op.batch_alter_table("user_accounts") as batch_op:
        batch_op.add_column(sa.Column("role", sa.String(length=32), nullable=False))
        batch_op.create_index("ix_user_accounts_role", ["role"], unique=False)

    with op.batch_alter_table("collections") as batch_op:
        batch_op.drop_index("ix_collections_organisation_id")
        batch_op.drop_column("organisation_id")

    op.drop_index("ix_organisation_memberships_user_id", "organisation_memberships")
    op.drop_table("organisation_memberships")

    op.drop_index("ix_organisations_slug", "organisations")
    op.drop_table("organisations")
