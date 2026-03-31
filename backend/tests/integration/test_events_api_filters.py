"""Integration tests for events API advanced filtering params."""

from __future__ import annotations

from pathlib import Path

import pytest
from alembic.config import Config
from httpx import AsyncClient

from alembic import command as alembic_command
from soft_skills_backend.platform.db.models import WorkflowEventRecord


def _migrate(test_settings) -> None:
    alembic_config = Config(str(Path(__file__).resolve().parents[2] / "alembic.ini"))
    alembic_config.set_main_option(
        "script_location",
        str(Path(__file__).resolve().parents[2] / "alembic"),
    )
    alembic_config.set_main_option("sqlalchemy.url", test_settings.database_url)
    alembic_command.upgrade(alembic_config, "heads")


async def _register_user(client: AsyncClient, *, email: str, display_name: str) -> dict:
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


async def _create_org(client: AsyncClient, *, user_id: str, name: str, slug: str) -> dict:
    response = await client.post(
        "/api/organisations",
        headers={"X-User-ID": user_id},
        json={"name": name, "slug": slug},
    )
    assert response.status_code == 200
    return response.json()["data"]


def _seed_events(app, *, org_id: str) -> None:
    container = app.state.container
    with container.session_factory() as session:
        session.add_all(
            [
                WorkflowEventRecord(
                    event_id="evt-filter-001",
                    event_type="session.started",
                    trace_id="trace-aaa",
                    workflow_id="wf-001",
                    error_code=None,
                    organisation_id=org_id,
                    payload={"user": "alice"},
                ),
                WorkflowEventRecord(
                    event_id="evt-filter-002",
                    event_type="attempt.submitted",
                    trace_id="trace-bbb",
                    workflow_id="wf-002",
                    error_code="SS-ERR-001",
                    organisation_id=org_id,
                    payload={"user": "bob"},
                ),
                WorkflowEventRecord(
                    event_id="evt-filter-003",
                    event_type="pipeline.failed",
                    trace_id="trace-ccc",
                    workflow_id="wf-003",
                    error_code="SS-PIPE-002",
                    organisation_id=org_id,
                    payload={"user": "carol"},
                ),
                WorkflowEventRecord(
                    event_id="evt-filter-004",
                    event_type="auth.login.success",
                    trace_id="trace-aaa",
                    workflow_id="wf-001",
                    error_code=None,
                    organisation_id=org_id,
                    payload={"user": "dave"},
                ),
            ]
        )
        session.commit()


@pytest.mark.asyncio
async def test_events_list_filter_by_event_type(app, client, test_settings) -> None:
    _migrate(test_settings)
    admin = await _register_user(
        client, email="filter-type@example.com", display_name="Filter Type"
    )
    await client.post("/api/skills/bootstrap-canon", headers={"X-User-ID": admin["id"]})
    org = await _create_org(client, user_id=admin["id"], name="Filter Org", slug="filter-org")
    org_id = org["id"]
    _seed_events(app, org_id=org_id)

    response = await client.get(
        "/api/events?event_type=session.started",
        headers={"X-User-ID": admin["id"], "X-Organisation-ID": org_id},
    )
    assert response.status_code == 200
    items = response.json()["data"]["items"]
    assert all(item["event_type"] == "session.started" for item in items)


@pytest.mark.asyncio
async def test_events_list_filter_by_error_code(app, client, test_settings) -> None:
    _migrate(test_settings)
    admin = await _register_user(client, email="filter-err@example.com", display_name="Filter Err")
    await client.post("/api/skills/bootstrap-canon", headers={"X-User-ID": admin["id"]})
    org = await _create_org(
        client, user_id=admin["id"], name="Filter Err Org", slug="filter-err-org"
    )
    org_id = org["id"]
    _seed_events(app, org_id=org_id)

    response = await client.get(
        "/api/events?error_code=SS-ERR-001",
        headers={"X-User-ID": admin["id"], "X-Organisation-ID": org_id},
    )
    assert response.status_code == 200
    items = response.json()["data"]["items"]
    assert all(item["error_code"] == "SS-ERR-001" for item in items)


@pytest.mark.asyncio
async def test_events_list_filter_by_trace_id(app, client, test_settings) -> None:
    _migrate(test_settings)
    admin = await _register_user(
        client, email="filter-trace@example.com", display_name="Filter Trace"
    )
    await client.post("/api/skills/bootstrap-canon", headers={"X-User-ID": admin["id"]})
    org = await _create_org(
        client, user_id=admin["id"], name="Filter Trace Org", slug="filter-trace-org"
    )
    org_id = org["id"]
    _seed_events(app, org_id=org_id)

    response = await client.get(
        "/api/events?trace_id=trace-aaa",
        headers={"X-User-ID": admin["id"], "X-Organisation-ID": org_id},
    )
    assert response.status_code == 200
    items = response.json()["data"]["items"]
    assert all(item["trace_id"] == "trace-aaa" for item in items)


@pytest.mark.asyncio
async def test_events_list_filter_by_workflow_id(app, client, test_settings) -> None:
    _migrate(test_settings)
    admin = await _register_user(client, email="filter-wf@example.com", display_name="Filter WF")
    await client.post("/api/skills/bootstrap-canon", headers={"X-User-ID": admin["id"]})
    org = await _create_org(client, user_id=admin["id"], name="Filter WF Org", slug="filter-wf-org")
    org_id = org["id"]
    _seed_events(app, org_id=org_id)

    response = await client.get(
        "/api/events?workflow_id=wf-002",
        headers={"X-User-ID": admin["id"], "X-Organisation-ID": org_id},
    )
    assert response.status_code == 200
    items = response.json()["data"]["items"]
    assert all(item["workflow_id"] == "wf-002" for item in items)


@pytest.mark.asyncio
async def test_events_list_search_regex(app, client, test_settings) -> None:
    _migrate(test_settings)
    admin = await _register_user(
        client, email="filter-search@example.com", display_name="Filter Search"
    )
    await client.post("/api/skills/bootstrap-canon", headers={"X-User-ID": admin["id"]})
    org = await _create_org(
        client, user_id=admin["id"], name="Filter Search Org", slug="filter-search-org"
    )
    org_id = org["id"]
    _seed_events(app, org_id=org_id)

    response = await client.get(
        "/api/events?search=session",
        headers={"X-User-ID": admin["id"], "X-Organisation-ID": org_id},
    )
    assert response.status_code == 200
    items = response.json()["data"]["items"]
    assert len(items) > 0
    assert any("session" in item["event_type"] for item in items)


@pytest.mark.asyncio
async def test_events_list_sort_by_event_type(app, client, test_settings) -> None:
    _migrate(test_settings)
    admin = await _register_user(
        client, email="filter-sort@example.com", display_name="Filter Sort"
    )
    await client.post("/api/skills/bootstrap-canon", headers={"X-User-ID": admin["id"]})
    org = await _create_org(
        client, user_id=admin["id"], name="Filter Sort Org", slug="filter-sort-org"
    )
    org_id = org["id"]
    _seed_events(app, org_id=org_id)

    response = await client.get(
        "/api/events?sort_by=event_type&sort_order=asc",
        headers={"X-User-ID": admin["id"], "X-Organisation-ID": org_id},
    )
    assert response.status_code == 200
    items = response.json()["data"]["items"]
    types = [item["event_type"] for item in items]
    assert types == sorted(types)


@pytest.mark.asyncio
async def test_events_list_sort_by_occurred_at_desc(app, client, test_settings) -> None:
    _migrate(test_settings)
    admin = await _register_user(
        client, email="filter-sort-desc@example.com", display_name="Filter Sort Desc"
    )
    await client.post("/api/skills/bootstrap-canon", headers={"X-User-ID": admin["id"]})
    org = await _create_org(
        client, user_id=admin["id"], name="Filter Sort Desc Org", slug="filter-sort-desc-org"
    )
    org_id = org["id"]
    _seed_events(app, org_id=org_id)

    response = await client.get(
        "/api/events?sort_by=occurred_at&sort_order=desc",
        headers={"X-User-ID": admin["id"], "X-Organisation-ID": org_id},
    )
    assert response.status_code == 200
    items = response.json()["data"]["items"]
    times = [item["occurred_at"] for item in items]
    assert times == sorted(times, reverse=True)


@pytest.mark.asyncio
async def test_events_list_pagination(app, client, test_settings) -> None:
    _migrate(test_settings)
    admin = await _register_user(
        client, email="filter-page@example.com", display_name="Filter Page"
    )
    await client.post("/api/skills/bootstrap-canon", headers={"X-User-ID": admin["id"]})
    org = await _create_org(
        client, user_id=admin["id"], name="Filter Page Org", slug="filter-page-org"
    )
    org_id = org["id"]
    _seed_events(app, org_id=org_id)

    # Verify pagination params are accepted and return valid metadata
    response = await client.get(
        "/api/events?limit=2&offset=0",
        headers={"X-User-ID": admin["id"], "X-Organisation-ID": org_id},
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data["items"]) <= 2
    assert data["total"] >= 4
    assert data["offset"] == 0
    assert data["limit"] == 2

    response2 = await client.get(
        "/api/events?limit=2&offset=2",
        headers={"X-User-ID": admin["id"], "X-Organisation-ID": org_id},
    )
    assert response2.status_code == 200
    data2 = response2.json()["data"]
    assert len(data2["items"]) <= 2
    assert data2["offset"] == 2
