"""Identity and content foundation tables."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "20260325_0002"
down_revision = "20260325_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "user_accounts",
        sa.Column("id", sa.String(length=32), primary_key=True),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("display_name", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=32), nullable=False),
        sa.Column("auth_provider", sa.String(length=64), nullable=False),
        sa.Column("auth_subject", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_user_accounts_email", "user_accounts", ["email"], unique=True)
    op.create_index("ix_user_accounts_role", "user_accounts", ["role"], unique=False)

    op.create_table(
        "learner_profiles",
        sa.Column("user_id", sa.String(length=32), primary_key=True),
        sa.Column("target_role", sa.String(length=255), nullable=True),
        sa.Column("goals", sa.JSON(), nullable=False),
        sa.Column("practice_preferences", sa.JSON(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "skills",
        sa.Column("slug", sa.String(length=64), primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
    )

    op.create_table(
        "competencies",
        sa.Column("slug", sa.String(length=64), primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
    )

    op.create_table(
        "competency_skill_map",
        sa.Column("competency_slug", sa.String(length=64), primary_key=True),
        sa.Column("skill_slug", sa.String(length=64), primary_key=True),
        sa.Column("weight", sa.Float(), nullable=False),
    )

    op.create_table(
        "rubrics",
        sa.Column("rubric_id", sa.String(length=128), primary_key=True),
        sa.Column("family", sa.String(length=64), nullable=False),
        sa.Column("version", sa.String(length=32), nullable=False),
        sa.Column("content_type", sa.String(length=64), nullable=False),
        sa.Column("schema_version", sa.String(length=32), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("criteria", sa.JSON(), nullable=False),
    )
    op.create_index("ix_rubrics_family", "rubrics", ["family"], unique=False)
    op.create_index("ix_rubrics_content_type", "rubrics", ["content_type"], unique=False)

    op.create_table(
        "collections",
        sa.Column("id", sa.String(length=32), primary_key=True),
        sa.Column("author_user_id", sa.String(length=32), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("target_audience", sa.String(length=255), nullable=False),
        sa.Column("difficulty", sa.String(length=32), nullable=False),
        sa.Column("lifecycle_state", sa.String(length=32), nullable=False),
        sa.Column("verification_state", sa.String(length=32), nullable=False),
        sa.Column("content_format_mix", sa.JSON(), nullable=False),
        sa.Column("target_skill_slugs", sa.JSON(), nullable=False),
        sa.Column("target_competency_slugs", sa.JSON(), nullable=False),
        sa.Column("rubric_ids", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_collections_author_user_id", "collections", ["author_user_id"], unique=False)
    op.create_index("ix_collections_difficulty", "collections", ["difficulty"], unique=False)
    op.create_index("ix_collections_lifecycle_state", "collections", ["lifecycle_state"], unique=False)
    op.create_index("ix_collections_verification_state", "collections", ["verification_state"], unique=False)

    op.create_table(
        "prompt_items",
        sa.Column("id", sa.String(length=32), primary_key=True),
        sa.Column("collection_id", sa.String(length=32), nullable=False),
        sa.Column("author_user_id", sa.String(length=32), nullable=False),
        sa.Column("prompt_type", sa.String(length=32), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("prompt_text", sa.Text(), nullable=False),
        sa.Column("difficulty", sa.String(length=32), nullable=False),
        sa.Column("lifecycle_state", sa.String(length=32), nullable=False),
        sa.Column("target_skill_slugs", sa.JSON(), nullable=False),
        sa.Column("rubric_id", sa.String(length=128), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_prompt_items_collection_id", "prompt_items", ["collection_id"], unique=False)
    op.create_index("ix_prompt_items_author_user_id", "prompt_items", ["author_user_id"], unique=False)
    op.create_index("ix_prompt_items_prompt_type", "prompt_items", ["prompt_type"], unique=False)
    op.create_index("ix_prompt_items_lifecycle_state", "prompt_items", ["lifecycle_state"], unique=False)
    op.create_index("ix_prompt_items_rubric_id", "prompt_items", ["rubric_id"], unique=False)

    op.create_table(
        "scenarios",
        sa.Column("id", sa.String(length=32), primary_key=True),
        sa.Column("collection_id", sa.String(length=32), nullable=False),
        sa.Column("author_user_id", sa.String(length=32), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("business_context", sa.Text(), nullable=False),
        sa.Column("learner_objective", sa.Text(), nullable=False),
        sa.Column("constraints", sa.JSON(), nullable=False),
        sa.Column("stakeholder_tensions", sa.JSON(), nullable=False),
        sa.Column("lifecycle_state", sa.String(length=32), nullable=False),
        sa.Column("target_skill_slugs", sa.JSON(), nullable=False),
        sa.Column("rubric_id", sa.String(length=128), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_scenarios_collection_id", "scenarios", ["collection_id"], unique=False)
    op.create_index("ix_scenarios_author_user_id", "scenarios", ["author_user_id"], unique=False)
    op.create_index("ix_scenarios_lifecycle_state", "scenarios", ["lifecycle_state"], unique=False)
    op.create_index("ix_scenarios_rubric_id", "scenarios", ["rubric_id"], unique=False)

    op.create_table(
        "mock_companies",
        sa.Column("id", sa.String(length=32), primary_key=True),
        sa.Column("scenario_id", sa.String(length=32), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("industry", sa.String(length=255), nullable=False),
        sa.Column("operating_context", sa.Text(), nullable=False),
    )
    op.create_index("ix_mock_companies_scenario_id", "mock_companies", ["scenario_id"], unique=False)

    op.create_table(
        "mock_people",
        sa.Column("id", sa.String(length=32), primary_key=True),
        sa.Column("scenario_id", sa.String(length=32), nullable=False),
        sa.Column("mock_company_id", sa.String(length=32), nullable=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=255), nullable=False),
        sa.Column("goals", sa.JSON(), nullable=False),
        sa.Column("communication_style", sa.Text(), nullable=False),
        sa.Column("relationship_to_scenario", sa.Text(), nullable=False),
    )
    op.create_index("ix_mock_people_scenario_id", "mock_people", ["scenario_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_mock_people_scenario_id", table_name="mock_people")
    op.drop_table("mock_people")

    op.drop_index("ix_mock_companies_scenario_id", table_name="mock_companies")
    op.drop_table("mock_companies")

    op.drop_index("ix_scenarios_rubric_id", table_name="scenarios")
    op.drop_index("ix_scenarios_lifecycle_state", table_name="scenarios")
    op.drop_index("ix_scenarios_author_user_id", table_name="scenarios")
    op.drop_index("ix_scenarios_collection_id", table_name="scenarios")
    op.drop_table("scenarios")

    op.drop_index("ix_prompt_items_rubric_id", table_name="prompt_items")
    op.drop_index("ix_prompt_items_lifecycle_state", table_name="prompt_items")
    op.drop_index("ix_prompt_items_prompt_type", table_name="prompt_items")
    op.drop_index("ix_prompt_items_author_user_id", table_name="prompt_items")
    op.drop_index("ix_prompt_items_collection_id", table_name="prompt_items")
    op.drop_table("prompt_items")

    op.drop_index("ix_collections_verification_state", table_name="collections")
    op.drop_index("ix_collections_lifecycle_state", table_name="collections")
    op.drop_index("ix_collections_difficulty", table_name="collections")
    op.drop_index("ix_collections_author_user_id", table_name="collections")
    op.drop_table("collections")

    op.drop_index("ix_rubrics_content_type", table_name="rubrics")
    op.drop_index("ix_rubrics_family", table_name="rubrics")
    op.drop_table("rubrics")

    op.drop_table("competency_skill_map")
    op.drop_table("competencies")
    op.drop_table("skills")
    op.drop_table("learner_profiles")

    op.drop_index("ix_user_accounts_role", table_name="user_accounts")
    op.drop_index("ix_user_accounts_email", table_name="user_accounts")
    op.drop_table("user_accounts")
