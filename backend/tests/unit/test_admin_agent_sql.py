from __future__ import annotations

from soft_skills_backend.config import Settings
from soft_skills_backend.modules.admin_agent.contracts.commands import QueryAdminDataCommand
from soft_skills_backend.modules.admin_agent.domain.redactor import AdminAgentResultRedactor
from soft_skills_backend.modules.admin_agent.domain.schema_registry import AdminAgentSchemaRegistry
from soft_skills_backend.modules.admin_agent.infra.sql_guard import AdminAgentSqlGuard
from soft_skills_backend.shared.errors import AppError


def test_admin_agent_schema_registry_contains_allowlisted_views() -> None:
    registry = AdminAgentSchemaRegistry()

    assert "admin_agent_assistant_sessions_v" in registry.allowed_views()
    assert "session_status" in registry.get_view("admin_agent_assistant_sessions_v").columns
    assert registry.join_hints
    assert "Allowed admin-safe views" in registry.render_prompt_context()


def test_admin_agent_sql_guard_scopes_org_filter_and_limit() -> None:
    guard = AdminAgentSqlGuard(
        schema_registry=AdminAgentSchemaRegistry(),
        row_limit=25,
    )

    guarded = guard.validate_and_scope(
        QueryAdminDataCommand(
            sql=(
                "SELECT session_status, COUNT(*) AS session_count "
                "FROM admin_agent_assistant_sessions_v "
                "GROUP BY session_status"
            )
        )
    )

    assert guarded.source_views == ("admin_agent_assistant_sessions_v",)
    assert "WHERE organisation_id = :organisation_id" in guarded.scoped_sql
    assert "LIMIT :_admin_agent_row_limit" in guarded.scoped_sql


def test_admin_agent_sql_guard_rejects_disallowed_patterns() -> None:
    guard = AdminAgentSqlGuard(
        schema_registry=AdminAgentSchemaRegistry(),
        row_limit=25,
    )

    invalid_sql = (
        "SELECT * FROM admin_agent_assistant_sessions_v",
        "SELECT session_id FROM user_accounts",
        "SELECT session_id FROM admin_agent_assistant_sessions_v -- sneaky",
        "DELETE FROM admin_agent_assistant_sessions_v",
    )
    for sql in invalid_sql:
        try:
            guard.validate_and_scope(QueryAdminDataCommand(sql=sql))
        except AppError as exc:
            assert exc.code.startswith("SS-VALIDATION-")
        else:  # pragma: no cover - fail loudly if a bad query passes
            raise AssertionError(f"Expected validation failure for: {sql}")


def test_admin_agent_redactor_masks_residual_sensitive_values() -> None:
    redactor = AdminAgentResultRedactor()

    rows = redactor.redact_rows(
        [
            {
                "user_alias": "user_12345678",
                "contact_email": "learner@example.com",
                "metadata_payload": {"unsafe": True},
                "occurred_at": "2026-03-29T12:00:00Z",
            }
        ]
    )

    assert rows == [
        {
            "user_alias": "user_12345678",
            "contact_email": "[redacted]",
            "metadata_payload": "[redacted]",
            "occurred_at": "2026-03-29T12:00:00Z",
        }
    ]


def test_settings_auto_allow_includes_admin_agent_query_tool() -> None:
    settings = Settings()

    assert "query_admin_data" in settings.tool_approval_auto_allow
