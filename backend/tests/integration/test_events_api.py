"""Events integration tests for org scoping."""

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


async def _add_member(
    client: AsyncClient,
    *,
    admin_id: str,
    org_id: str,
    user_id: str,
    role: str = "member",
) -> dict:
    response = await client.post(
        f"/api/organisations/{org_id}/members",
        headers={"X-User-ID": admin_id, "X-Organisation-ID": org_id},
        json={"user_id": user_id, "role": role},
    )
    assert response.status_code == 200
    return response.json()["data"]


def _seed_events(app, *, org_id_a: str, org_id_b: str | None = None):
    """Seed test events into the database."""
    container = app.state.container
    with container.session_factory() as session:
        # Events for org A
        session.add(
            WorkflowEventRecord(
                event_id="event-a1",
                event_type="test.event",
                organisation_id=org_id_a,
                payload={"org": "a", "index": 1},
            )
        )
        session.add(
            WorkflowEventRecord(
                event_id="event-a2",
                event_type="test.event",
                organisation_id=org_id_a,
                payload={"org": "a", "index": 2},
            )
        )
        # Events for org B (if provided)
        if org_id_b:
            session.add(
                WorkflowEventRecord(
                    event_id="event-b1",
                    event_type="test.event",
                    organisation_id=org_id_b,
                    payload={"org": "b", "index": 1},
                )
            )
        # Global event (no org)
        session.add(
            WorkflowEventRecord(
                event_id="event-global",
                event_type="test.event",
                organisation_id=None,
                payload={"org": "global"},
            )
        )
        session.commit()


@pytest.mark.asyncio
async def test_events_list_filters_by_organisation(app, client, test_settings) -> None:
    _migrate(test_settings)

    # Create admin for org A
    admin_a = await _register_user(client, email="admin-org-a@example.com", display_name="Admin A")
    await client.post("/api/skills/bootstrap-canon", headers={"X-User-ID": admin_a["id"]})
    org_a = await _create_org(client, user_id=admin_a["id"], name="Org A", slug="org-a")
    org_id_a = org_a["id"]

    # Create admin for org B
    admin_b = await _register_user(client, email="admin-org-b@example.com", display_name="Admin B")
    await client.post("/api/skills/bootstrap-canon", headers={"X-User-ID": admin_b["id"]})
    org_b = await _create_org(client, user_id=admin_b["id"], name="Org B", slug="org-b")
    org_id_b = org_b["id"]

    # Seed events
    _seed_events(app, org_id_a=org_id_a, org_id_b=org_id_b)

    # Admin A should only see events for org A
    response_a = await client.get(
        "/api/events",
        headers={"X-User-ID": admin_a["id"], "X-Organisation-ID": org_id_a},
    )
    assert response_a.status_code == 200
    events_a = response_a.json()["data"]["items"]
    event_ids_a = [e["event_id"] for e in events_a]
    assert "event-a1" in event_ids_a
    assert "event-a2" in event_ids_a
    assert "event-b1" not in event_ids_a
    assert "event-global" in event_ids_a  # Global events visible to all

    # Admin B should only see events for org B
    response_b = await client.get(
        "/api/events",
        headers={"X-User-ID": admin_b["id"], "X-Organisation-ID": org_id_b},
    )
    assert response_b.status_code == 200
    events_b = response_b.json()["data"]["items"]
    event_ids_b = [e["event_id"] for e in events_b]
    assert "event-b1" in event_ids_b
    assert "event-a1" not in event_ids_b
    assert "event-a2" not in event_ids_b
    assert "event-global" in event_ids_b  # Global events visible to all


@pytest.mark.asyncio
async def test_events_get_rejects_cross_org_access(app, client, test_settings) -> None:
    _migrate(test_settings)

    # Create two orgs
    admin_a = await _register_user(
        client, email="admin-cross-a@example.com", display_name="Admin A"
    )
    await client.post("/api/skills/bootstrap-canon", headers={"X-User-ID": admin_a["id"]})
    org_a = await _create_org(client, user_id=admin_a["id"], name="Org A Cross", slug="org-a-cross")
    org_id_a = org_a["id"]

    admin_b = await _register_user(
        client, email="admin-cross-b@example.com", display_name="Admin B"
    )
    await client.post("/api/skills/bootstrap-canon", headers={"X-User-ID": admin_b["id"]})
    org_b = await _create_org(client, user_id=admin_b["id"], name="Org B Cross", slug="org-b-cross")
    org_id_b = org_b["id"]

    # Seed events
    _seed_events(app, org_id_a=org_id_a, org_id_b=org_id_b)

    # Admin A tries to get org B's event
    response = await client.get(
        "/api/events/event-b1",
        headers={"X-User-ID": admin_a["id"], "X-Organisation-ID": org_id_a},
    )
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "SS-AUTH-004"

    # Admin A can get their own event
    response = await client.get(
        "/api/events/event-a1",
        headers={"X-User-ID": admin_a["id"], "X-Organisation-ID": org_id_a},
    )
    assert response.status_code == 200
    assert response.json()["data"]["event_id"] == "event-a1"


@pytest.mark.asyncio
async def test_events_update_rejects_cross_org_access(app, client, test_settings) -> None:
    _migrate(test_settings)

    admin_a = await _register_user(
        client, email="admin-update-a@example.com", display_name="Admin A"
    )
    await client.post("/api/skills/bootstrap-canon", headers={"X-User-ID": admin_a["id"]})
    org_a = await _create_org(
        client, user_id=admin_a["id"], name="Org A Update", slug="org-a-update"
    )
    org_id_a = org_a["id"]

    admin_b = await _register_user(
        client, email="admin-update-b@example.com", display_name="Admin B"
    )
    await client.post("/api/skills/bootstrap-canon", headers={"X-User-ID": admin_b["id"]})
    org_b = await _create_org(
        client, user_id=admin_b["id"], name="Org B Update", slug="org-b-update"
    )
    org_id_b = org_b["id"]

    _seed_events(app, org_id_a=org_id_a, org_id_b=org_id_b)

    # Admin A tries to update org B's event
    response = await client.patch(
        "/api/events/event-b1",
        headers={"X-User-ID": admin_a["id"], "X-Organisation-ID": org_id_a},
        json={"error_code": "SS-HACK-001"},
    )
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "SS-AUTH-004"

    # Admin A can update their own event
    response = await client.patch(
        "/api/events/event-a1",
        headers={"X-User-ID": admin_a["id"], "X-Organisation-ID": org_id_a},
        json={"error_code": "SS-TEST-001"},
    )
    assert response.status_code == 200
    assert response.json()["data"]["error_code"] == "SS-TEST-001"


@pytest.mark.asyncio
async def test_events_delete_rejects_cross_org_access(app, client, test_settings) -> None:
    _migrate(test_settings)

    admin_a = await _register_user(
        client, email="admin-delete-a@example.com", display_name="Admin A"
    )
    await client.post("/api/skills/bootstrap-canon", headers={"X-User-ID": admin_a["id"]})
    org_a = await _create_org(
        client, user_id=admin_a["id"], name="Org A Delete", slug="org-a-delete"
    )
    org_id_a = org_a["id"]

    admin_b = await _register_user(
        client, email="admin-delete-b@example.com", display_name="Admin B"
    )
    await client.post("/api/skills/bootstrap-canon", headers={"X-User-ID": admin_b["id"]})
    org_b = await _create_org(
        client, user_id=admin_b["id"], name="Org B Delete", slug="org-b-delete"
    )
    org_id_b = org_b["id"]

    _seed_events(app, org_id_a=org_id_a, org_id_b=org_id_b)

    # Admin A tries to delete org B's event
    response = await client.delete(
        "/api/events/event-b1",
        headers={"X-User-ID": admin_a["id"], "X-Organisation-ID": org_id_a},
    )
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "SS-AUTH-004"

    # Admin A can delete their own event
    response = await client.delete(
        "/api/events/event-a1",
        headers={"X-User-ID": admin_a["id"], "X-Organisation-ID": org_id_a},
    )
    assert response.status_code == 200
    assert response.json()["data"]["status"] == "deleted"
