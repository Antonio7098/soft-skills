"""Add organisation_id to workflow_events.

Revision ID: 20260326_0013
Revises: 20260326_0012
Create Date: 2026-03-26 22:00:00.000000

"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "20260326_0013"
down_revision = "20260326_0012"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("workflow_events") as batch_op:
        batch_op.add_column(sa.Column("organisation_id", sa.String(32), nullable=True))
        batch_op.create_index("ix_workflow_events_organisation_id", ["organisation_id"])


def downgrade() -> None:
    with op.batch_alter_table("workflow_events") as batch_op:
        batch_op.drop_index("ix_workflow_events_organisation_id")
        batch_op.drop_column("organisation_id")
