from __future__ import annotations

from soft_skills_backend.config import Settings
from soft_skills_backend.modules.assistant.contracts.sql import QueryUserContextCommand
from soft_skills_backend.modules.assistant.domain.redactor import AssistantResultRedactor
from soft_skills_backend.modules.assistant.domain.schema_registry import AssistantSchemaRegistry
from soft_skills_backend.modules.assistant.infra.sql_guard import AssistantSqlGuard
from soft_skills_backend.shared.errors import AppError


def test_assistant_schema_registry_contains_allowlisted_views() -> None:
    registry = AssistantSchemaRegistry()

    assert "assistant_safe_skills_v" in registry.allowed_views()
    assert "assistant_safe_competencies_v" in registry.allowed_views()
    assert "assistant_safe_attempt_summaries_v" in registry.allowed_views()
    assert "overall_score" in registry.get_view("assistant_safe_attempt_summaries_v").columns
    assert registry.join_hints
    assert registry.resolve_view_name("assistant_safe_collections_v1") == "assistant_safe_collections_v"
    assert registry.resolve_column_name("assistant_safe_collections_v", "collection_name") == "title"
    assert registry.resolve_column_name("assistant_safe_skills_v", "slug") == "skill_slug"
    assert "Allowed learner-safe views" in registry.render_prompt_context()


def test_assistant_sql_guard_scopes_attempt_reads_by_user_and_limit() -> None:
    guard = AssistantSqlGuard(
        schema_registry=AssistantSchemaRegistry(),
        row_limit=25,
    )

    guarded = guard.validate_and_scope(
        QueryUserContextCommand(
            sql=(
                "SELECT attempt_id, overall_score "
                "FROM assistant_safe_attempt_summaries_v "
                "ORDER BY created_at DESC"
            )
        )
    )

    assert guarded.source_views == ("assistant_safe_attempt_summaries_v",)
    assert "user_id = :user_id" in guarded.scoped_sql
    assert "LIMIT :_assistant_row_limit" in guarded.scoped_sql


def test_assistant_sql_guard_canonicalizes_safe_view_suffix_and_wildcard() -> None:
    guard = AssistantSqlGuard(
        schema_registry=AssistantSchemaRegistry(),
        row_limit=25,
    )

    guarded = guard.validate_and_scope(
        QueryUserContextCommand(
            sql="SELECT * FROM assistant_safe_collections ORDER BY updated_at DESC"
        )
    )

    assert guarded.source_views == ("assistant_safe_collections_v",)
    assert "assistant_safe_collections_v" in guarded.sql
    assert "SELECT *" not in guarded.sql
    assert "title" in guarded.sql
    assert "updated_at" in guarded.sql


def test_assistant_sql_guard_canonicalizes_collection_aliases() -> None:
    guard = AssistantSqlGuard(
        schema_registry=AssistantSchemaRegistry(),
        row_limit=25,
    )

    guarded = guard.validate_and_scope(
        QueryUserContextCommand(
            sql="SELECT collection_id, collection_name FROM assistant_safe_collections_v1"
        )
    )

    assert guarded.source_views == ("assistant_safe_collections_v",)
    assert "assistant_safe_collections_v" in guarded.sql
    assert "title AS collection_name" in guarded.sql


def test_assistant_sql_guard_does_not_reference_missing_collection_view_columns() -> None:
    guard = AssistantSqlGuard(
        schema_registry=AssistantSchemaRegistry(),
        row_limit=25,
    )

    guarded = guard.validate_and_scope(
        QueryUserContextCommand(
            sql="SELECT title, difficulty, rating_count FROM assistant_safe_collections_v ORDER BY updated_at DESC"
        )
    )

    assert "author_user_id = :user_id" in guarded.scoped_sql
    assert "lifecycle_state" not in guarded.scoped_sql


def test_assistant_sql_guard_accepts_taxonomy_skill_view() -> None:
    guard = AssistantSqlGuard(
        schema_registry=AssistantSchemaRegistry(),
        row_limit=25,
    )

    guarded = guard.validate_and_scope(
        QueryUserContextCommand(
            sql="SELECT slug, skill_name FROM assistant_safe_skills_v ORDER BY name ASC"
        )
    )

    assert guarded.source_views == ("assistant_safe_skills_v",)
    assert "skill_slug AS slug" in guarded.sql
    assert "name AS skill_name" in guarded.sql
    assert "organisation_id = :organisation_id" in guarded.scoped_sql


def test_assistant_sql_guard_rejects_disallowed_patterns() -> None:
    guard = AssistantSqlGuard(
        schema_registry=AssistantSchemaRegistry(),
        row_limit=25,
    )

    invalid_sql = (
        "SELECT attempt_id FROM attempts",
        "SELECT attempt_id FROM assistant_safe_attempt_summaries_v -- sneaky",
        "DELETE FROM assistant_safe_attempt_summaries_v",
    )
    for sql in invalid_sql:
        try:
            guard.validate_and_scope(QueryUserContextCommand(sql=sql))
        except AppError as exc:
            assert exc.code.startswith("SS-VALIDATION-")
        else:
            raise AssertionError(f"Expected validation failure for: {sql}")


def test_assistant_redactor_masks_residual_sensitive_values() -> None:
    redactor = AssistantResultRedactor()

    rows = redactor.redact_rows(
        [
            {
                "attempt_id": "attempt-123",
                "top_pick_reason": "Talk to learner@example.com before retrying.",
                "response_text": "unsafe",
                "created_at": "2026-03-30T12:00:00Z",
            }
        ]
    )

    assert rows == [
        {
            "attempt_id": "attempt-123",
            "top_pick_reason": "Talk to ***@example.com before retrying.",
            "response_text": "[redacted]",
            "created_at": "2026-03-30T12:00:00Z",
        }
    ]


def test_settings_auto_allow_includes_assistant_query_tool() -> None:
    settings = Settings()

    assert "query_user_context" in settings.tool_approval_auto_allow
