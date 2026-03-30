from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

import httpx
import pytest
from alembic.config import Config
from sqlalchemy import select

from alembic import command as alembic_command
from soft_skills_backend.app import create_app
from soft_skills_backend.platform.db.models import WorkflowEventRecord
from soft_skills_backend.shared.ports.models import ProviderCompletion, ProviderTextChunk


def _migrate(test_settings: Any) -> None:
    alembic_config = Config(str(Path(__file__).resolve().parents[2] / "alembic.ini"))
    alembic_config.set_main_option(
        "script_location",
        str(Path(__file__).resolve().parents[2] / "alembic"),
    )
    alembic_config.set_main_option("sqlalchemy.url", test_settings.database_url)
    alembic_command.upgrade(alembic_config, "heads")


@asynccontextmanager
async def _open_test_client(test_settings: Any) -> AsyncIterator[tuple[Any, httpx.AsyncClient]]:
    app = create_app(test_settings)
    app.state.container.background_tasks.attach(asyncio.get_running_loop())
    transport = httpx.ASGITransport(app=app)
    try:
        async with httpx.AsyncClient(
            transport=transport,
            base_url="http://testserver",
        ) as client:
            yield app, client
    finally:
        await app.state.container.background_tasks.shutdown()
        await app.state.container.shutdown()
        app.state.container.dispose()


async def _register_user(
    client: Any,
    *,
    email: str,
    display_name: str,
) -> dict[str, object]:
    response = await client.post(
        "/api/auth/register",
        json={
            "email": email,
            "display_name": display_name,
            "target_role": "Consultant",
            "goals": ["Improve stakeholder handling"],
            "practice_preferences": {"session_length": "short"},
        },
    )
    assert response.status_code == 200
    return response.json()["data"]


class _AdminAgentProviderStub:
    provider_name = "test-provider"
    model_slug = "test-model"

    def __init__(self, payloads: list[dict[str, object]]) -> None:
        self._payloads = payloads

    async def complete_json(
        self,
        *,
        messages: object,
        call_context: object,
        response_schema: object = None,
        timeout_seconds: object = None,
    ) -> ProviderCompletion:
        del messages, call_context, response_schema, timeout_seconds
        payload = self._payloads.pop(0)
        return ProviderCompletion(
            content=payload,
            model_slug=self.model_slug,
            usage={"total_tokens": 42},
            raw_response={"provider": self.provider_name},
        )

    async def stream_text(self, *, messages: object, call_context: object):
        del messages, call_context
        if False:  # pragma: no cover
            yield ProviderTextChunk(delta="", done=True)


@pytest.mark.asyncio
async def test_admin_agent_chat_executes_org_scoped_query_and_audits(test_settings) -> None:
    _migrate(test_settings)

    async with _open_test_client(test_settings) as (app, client):
        admin = await _register_user(
            client,
            email="admin-agent-admin@example.com",
            display_name="Admin Agent Admin",
        )
        member = await _register_user(
            client,
            email="admin-agent-member@example.com",
            display_name="Admin Agent Member",
        )
        org_response = await client.post(
            "/api/organisations",
            headers={"X-User-ID": str(admin["id"])},
            json={"name": "Admin Agent Org", "slug": "admin-agent-org"},
        )
        assert org_response.status_code == 200
        org = org_response.json()["data"]
        org_id = str(org["id"])

        add_member_response = await client.post(
            f"/api/organisations/{org_id}/members",
            headers={"X-User-ID": str(admin["id"]), "X-Organisation-ID": org_id},
            json={"user_id": str(member["id"]), "role": "member"},
        )
        assert add_member_response.status_code == 200

        session_response = await client.post(
            "/api/assistant/sessions",
            headers={"X-User-ID": str(member["id"])},
            json={"title": "Investigate me"},
        )
        assert session_response.status_code == 200

        app.state.container.admin_agent_service._workflows._llm_provider = _AdminAgentProviderStub(  # type: ignore[attr-defined]
            [
                {
                    "intent_summary": "Assistant session counts by status",
                    "sql": (
                        "SELECT session_status, COUNT(*) AS session_count "
                        "FROM admin_agent_assistant_sessions_v "
                        "GROUP BY session_status ORDER BY session_count DESC"
                    ),
                    "params": {},
                }
            ]
        )

        response = await client.post(
            "/api/admin-agent/chat",
            headers={"X-User-ID": str(admin["id"]), "X-Organisation-ID": org_id},
            json={"message": "How many assistant sessions do we have by status?"},
        )

        assert response.status_code == 200, response.json()
        payload = response.json()["data"]
        assert payload["conversation_id"]
        assert payload["tool_results"][0]["source_views"] == ["admin_agent_assistant_sessions_v"]
        assert payload["tool_results"][0]["row_count"] == 1
        assert payload["tool_results"][0]["rows"][0]["session_status"] == "active"
        assert payload["metadata"]["provider"] == "test-provider"
        assert payload["metadata"]["prompt_version"] == "admin-agent.plan.v1"

        with app.state.container.session_factory() as session:
            events = session.execute(
                select(WorkflowEventRecord).where(
                    WorkflowEventRecord.workflow_id == payload["conversation_id"],
                    WorkflowEventRecord.event_type.like("admin.agent.%"),
                )
            ).scalars().all()

        event_types = {event.event_type for event in events}
        assert "admin.agent.request.received.v1" in event_types
        assert "admin.agent.query.executed.v1" in event_types
        assert "admin.agent.response.completed.v1" in event_types
        assert all(event.organisation_id == org_id for event in events)


@pytest.mark.asyncio
async def test_admin_agent_chat_denies_non_allowlisted_sql(test_settings) -> None:
    _migrate(test_settings)

    async with _open_test_client(test_settings) as (app, client):
        admin = await _register_user(
            client,
            email="admin-agent-admin-denied@example.com",
            display_name="Admin Agent Admin Denied",
        )
        org_response = await client.post(
            "/api/organisations",
            headers={"X-User-ID": str(admin["id"])},
            json={"name": "Admin Agent Denied Org", "slug": "admin-agent-denied-org"},
        )
        assert org_response.status_code == 200
        org_id = str(org_response.json()["data"]["id"])

        app.state.container.admin_agent_service._workflows._llm_provider = _AdminAgentProviderStub(  # type: ignore[attr-defined]
            [
                {
                    "intent_summary": "Unsafe raw table access",
                    "sql": "SELECT COUNT(*) AS user_count FROM user_accounts",
                    "params": {},
                }
            ]
        )

        response = await client.post(
            "/api/admin-agent/chat",
            headers={"X-User-ID": str(admin["id"]), "X-Organisation-ID": org_id},
            json={"message": "How many users exist globally?"},
        )

        assert response.status_code == 422
        error = response.json()["error"]
        assert error["code"] == "SS-VALIDATION-307"

        with app.state.container.session_factory() as session:
            denied_events = session.execute(
                select(WorkflowEventRecord).where(
                    WorkflowEventRecord.organisation_id == org_id,
                    WorkflowEventRecord.event_type == "admin.agent.query.denied.v1",
                )
            ).scalars().all()

        assert denied_events
