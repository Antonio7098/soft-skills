from __future__ import annotations

from soft_skills_backend.config import Settings
from soft_skills_backend.modules.assistant.contracts.sql import QueryUserContextCommand
from soft_skills_backend.modules.assistant.domain.redactor import AssistantResultRedactor
from soft_skills_backend.modules.assistant.domain.schema_registry import AssistantSchemaRegistry
from soft_skills_backend.modules.assistant.infra.sql_guard import AssistantSqlGuard
from soft_skills_backend.shared.errors import AppError


def test_assistant_schema_registry_contains_allowlisted_views() -> None:
    registry = AssistantSchemaRegistry()

    assert "assistant_safe_attempt_summaries_v" in registry.allowed_views()
    assert "overall_score" in registry.get_view("assistant_safe_attempt_summaries_v").columns
    assert registry.join_hints
    assert "Allowed learner-safe views" in registry.render_prompt_context()


def test_assistant_sql_guard_scopes_user_and_org_filters_and_limit() -> None:
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
    assert "organisation_id = :organisation_id" in guarded.scoped_sql
    assert "user_id = :user_id" in guarded.scoped_sql
    assert "LIMIT :_assistant_row_limit" in guarded.scoped_sql


def test_assistant_sql_guard_rejects_disallowed_patterns() -> None:
    guard = AssistantSqlGuard(
        schema_registry=AssistantSchemaRegistry(),
        row_limit=25,
    )

    invalid_sql = (
        "SELECT * FROM assistant_safe_attempt_summaries_v",
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
