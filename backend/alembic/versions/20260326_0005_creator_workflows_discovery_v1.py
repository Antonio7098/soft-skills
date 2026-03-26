"""Creator workflows, generation artifacts, and discovery semantics."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "20260326_0005"
down_revision = "20260325_0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "collections",
        sa.Column("source_type", sa.String(length=32), nullable=False, server_default="manual"),
    )
    op.add_column(
        "collections",
        sa.Column("last_generation_artifact_id", sa.String(length=32), nullable=True),
    )
    op.create_index("ix_collections_source_type", "collections", ["source_type"], unique=False)
    op.create_index(
        "ix_collections_last_generation_artifact_id",
        "collections",
        ["last_generation_artifact_id"],
        unique=False,
    )

    op.add_column(
        "prompt_items",
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
    )
    op.add_column(
        "scenarios",
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
    )

    op.create_table(
        "scenario_supporting_artifacts",
        sa.Column("id", sa.String(length=32), primary_key=True),
        sa.Column("scenario_id", sa.String(length=32), nullable=False),
        sa.Column("artifact_type", sa.String(length=32), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_scenario_supporting_artifacts_scenario_id",
        "scenario_supporting_artifacts",
        ["scenario_id"],
        unique=False,
    )
    op.create_index(
        "ix_scenario_supporting_artifacts_artifact_type",
        "scenario_supporting_artifacts",
        ["artifact_type"],
        unique=False,
    )

    op.create_table(
        "collection_saves",
        sa.Column("user_id", sa.String(length=32), primary_key=True),
        sa.Column("collection_id", sa.String(length=32), primary_key=True),
        sa.Column("saved_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_collection_saves_collection_id",
        "collection_saves",
        ["collection_id"],
        unique=False,
    )

    op.create_table(
        "content_generation_artifacts",
        sa.Column("id", sa.String(length=32), primary_key=True),
        sa.Column("collection_id", sa.String(length=32), nullable=False),
        sa.Column("author_user_id", sa.String(length=32), nullable=False),
        sa.Column("generation_mode", sa.String(length=32), nullable=False),
        sa.Column("prompt_version", sa.String(length=64), nullable=False),
        sa.Column("schema_version", sa.String(length=64), nullable=False),
        sa.Column("config_version", sa.String(length=64), nullable=False),
        sa.Column("provider", sa.String(length=64), nullable=False),
        sa.Column("model_slug", sa.String(length=128), nullable=False),
        sa.Column("request_id", sa.String(length=32), nullable=True),
        sa.Column("trace_id", sa.String(length=32), nullable=True),
        sa.Column("workflow_id", sa.String(length=64), nullable=True),
        sa.Column("input_payload", sa.JSON(), nullable=False),
        sa.Column("output_payload", sa.JSON(), nullable=False),
        sa.Column("raw_payload", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_content_generation_artifacts_collection_id",
        "content_generation_artifacts",
        ["collection_id"],
        unique=False,
    )
    op.create_index(
        "ix_content_generation_artifacts_author_user_id",
        "content_generation_artifacts",
        ["author_user_id"],
        unique=False,
    )
    op.create_index(
        "ix_content_generation_artifacts_generation_mode",
        "content_generation_artifacts",
        ["generation_mode"],
        unique=False,
    )
    op.create_index(
        "ix_content_generation_artifacts_prompt_version",
        "content_generation_artifacts",
        ["prompt_version"],
        unique=False,
    )
    op.create_index(
        "ix_content_generation_artifacts_config_version",
        "content_generation_artifacts",
        ["config_version"],
        unique=False,
    )
    op.create_index(
        "ix_content_generation_artifacts_provider",
        "content_generation_artifacts",
        ["provider"],
        unique=False,
    )
    op.create_index(
        "ix_content_generation_artifacts_request_id",
        "content_generation_artifacts",
        ["request_id"],
        unique=False,
    )
    op.create_index(
        "ix_content_generation_artifacts_trace_id",
        "content_generation_artifacts",
        ["trace_id"],
        unique=False,
    )
    op.create_index(
        "ix_content_generation_artifacts_workflow_id",
        "content_generation_artifacts",
        ["workflow_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_content_generation_artifacts_workflow_id",
        table_name="content_generation_artifacts",
    )
    op.drop_index(
        "ix_content_generation_artifacts_trace_id",
        table_name="content_generation_artifacts",
    )
    op.drop_index(
        "ix_content_generation_artifacts_request_id",
        table_name="content_generation_artifacts",
    )
    op.drop_index(
        "ix_content_generation_artifacts_provider",
        table_name="content_generation_artifacts",
    )
    op.drop_index(
        "ix_content_generation_artifacts_config_version",
        table_name="content_generation_artifacts",
    )
    op.drop_index(
        "ix_content_generation_artifacts_prompt_version",
        table_name="content_generation_artifacts",
    )
    op.drop_index(
        "ix_content_generation_artifacts_generation_mode",
        table_name="content_generation_artifacts",
    )
    op.drop_index(
        "ix_content_generation_artifacts_author_user_id",
        table_name="content_generation_artifacts",
    )
    op.drop_index(
        "ix_content_generation_artifacts_collection_id",
        table_name="content_generation_artifacts",
    )
    op.drop_table("content_generation_artifacts")

    op.drop_index("ix_collection_saves_collection_id", table_name="collection_saves")
    op.drop_table("collection_saves")

    op.drop_index(
        "ix_scenario_supporting_artifacts_artifact_type",
        table_name="scenario_supporting_artifacts",
    )
    op.drop_index(
        "ix_scenario_supporting_artifacts_scenario_id",
        table_name="scenario_supporting_artifacts",
    )
    op.drop_table("scenario_supporting_artifacts")

    op.drop_column("scenarios", "updated_at")
    op.drop_column("prompt_items", "updated_at")

    op.drop_index(
        "ix_collections_last_generation_artifact_id",
        table_name="collections",
    )
    op.drop_index("ix_collections_source_type", table_name="collections")
    op.drop_column("collections", "last_generation_artifact_id")
    op.drop_column("collections", "source_type")
