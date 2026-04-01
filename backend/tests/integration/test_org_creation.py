"""Integration tests for organisation creation and membership management."""

from __future__ import annotations

from pathlib import Path

import pytest
import pytest_asyncio
from alembic.config import Config

from alembic import command


def _migrate(test_settings) -> None:
    alembic_config = Config(str(Path(__file__).resolve().parents[2] / "alembic.ini"))
    alembic_config.set_main_option("sqlalchemy.url", test_settings.database_url)
    command.upgrade(alembic_config, "heads")


async def _register_user(client, *, email: str, display_name: str):
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


@pytest.mark.asyncio
async def test_create_organisation_makes_creator_admin(client, test_settings) -> None:
    _migrate(test_settings)
    user = await _register_user(client, email="org-creator@example.com", display_name="Org Creator")

    org_response = await client.post(
        "/api/organisations",
        headers={"X-User-ID": user["id"]},
        json={"name": "Acme Sales", "slug": "acme-sales"},
    )
    assert org_response.status_code == 200
    org = org_response.json()["data"]
    assert org["name"] == "Acme Sales"
    assert org["slug"] == "acme-sales"
    assert "id" in org
    assert "created_at" in org


@pytest.mark.asyncio
async def test_get_user_me_includes_org_memberships_after_creation(client, test_settings) -> None:
    _migrate(test_settings)
    user = await _register_user(
        client, email="membership-user@example.com", display_name="Membership User"
    )

    me_before = await client.get("/api/users/me", headers={"X-User-ID": user["id"]})
    assert me_before.status_code == 200
    data_before = me_before.json()["data"]
    assert data_before["org_memberships"] == []

    await client.post(
        "/api/organisations",
        headers={"X-User-ID": user["id"]},
        json={"name": "First Org", "slug": "first-org"},
    )

    me_after = await client.get("/api/users/me", headers={"X-User-ID": user["id"]})
    assert me_after.status_code == 200
    data_after = me_after.json()["data"]
    assert len(data_after["org_memberships"]) == 1
    membership = data_after["org_memberships"][0]
    assert membership["organisation_name"] == "First Org"
    assert membership["role"] == "admin"
    assert membership["permissions"] == [
        "collections:read",
        "practice:run",
        "admin:access",
        "org:read",
        "org:write",
    ]


@pytest.mark.asyncio
async def test_list_organisations_returns_all_users_orgs(client, test_settings) -> None:
    _migrate(test_settings)
    user = await _register_user(
        client, email="multi-org@example.com", display_name="Multi Org User"
    )

    await client.post(
        "/api/organisations",
        headers={"X-User-ID": user["id"]},
        json={"name": "Org One", "slug": "org-one"},
    )
    await client.post(
        "/api/organisations",
        headers={"X-User-ID": user["id"]},
        json={"name": "Org Two", "slug": "org-two"},
    )

    list_response = await client.get("/api/organisations", headers={"X-User-ID": user["id"]})
    assert list_response.status_code == 200
    orgs = list_response.json()["data"]
    assert len(orgs) == 2
    org_slugs = {org["slug"] for org in orgs}
    assert org_slugs == {"org-one", "org-two"}


@pytest.mark.asyncio
async def test_list_organisations_only_returns_users_own_orgs(client, test_settings) -> None:
    _migrate(test_settings)
    user_a = await _register_user(client, email="user-a@example.com", display_name="User A")
    user_b = await _register_user(client, email="user-b@example.com", display_name="User B")

    await client.post(
        "/api/organisations",
        headers={"X-User-ID": user_a["id"]},
        json={"name": "User A Org", "slug": "user-a-org"},
    )
    await client.post(
        "/api/organisations",
        headers={"X-User-ID": user_b["id"]},
        json={"name": "User B Org", "slug": "user-b-org"},
    )

    list_a = await client.get("/api/organisations", headers={"X-User-ID": user_a["id"]})
    assert len(list_a.json()["data"]) == 1
    assert list_a.json()["data"][0]["slug"] == "user-a-org"

    list_b = await client.get("/api/organisations", headers={"X-User-ID": user_b["id"]})
    assert len(list_b.json()["data"]) == 1
    assert list_b.json()["data"][0]["slug"] == "user-b-org"


@pytest.mark.asyncio
async def test_create_organisation_duplicate_slug_returns_error(client, test_settings) -> None:
    _migrate(test_settings)
    user = await _register_user(client, email="dup-slug@example.com", display_name="Dup Slug User")

    first_response = await client.post(
        "/api/organisations",
        headers={"X-User-ID": user["id"]},
        json={"name": "First Org", "slug": "duplicate-slug"},
    )
    print(f"First org response: {first_response.status_code} {first_response.json()}")

    dup_response = await client.post(
        "/api/organisations",
        headers={"X-User-ID": user["id"]},
        json={"name": "Second Org", "slug": "duplicate-slug"},
    )
    print(f"Duplicate org response: {dup_response.status_code} {dup_response.json()}")
    assert dup_response.status_code == 422
    assert dup_response.json()["error"]["code"] == "SS-VALIDATION-066"


@pytest.mark.asyncio
async def test_create_organisation_without_org_returns_empty_memberships(
    client, test_settings
) -> None:
    _migrate(test_settings)
    user = await _register_user(client, email="no-org@example.com", display_name="No Org User")

    me_response = await client.get("/api/users/me", headers={"X-User-ID": user["id"]})
    print(f"me_response: {me_response.status_code} {me_response.json()}")
    assert me_response.status_code == 200
    data = me_response.json()["data"]
    assert data["org_memberships"] == []


@pytest.mark.asyncio
async def test_org_membership_permissions_for_member_role(client, test_settings) -> None:
    _migrate(test_settings)
    creator = await _register_user(client, email="creator@example.com", display_name="Creator")
    org_response = await client.post(
        "/api/organisations",
        headers={"X-User-ID": creator["id"]},
        json={"name": "Permission Test Org", "slug": "perm-test-org"},
    )
    org_id = org_response.json()["data"]["id"]

    member = await _register_user(client, email="member@example.com", display_name="Member")

    invite_response = await client.post(
        f"/api/organisations/{org_id}/members",
        headers={"X-User-ID": creator["id"], "X-Organisation-ID": org_id},
        json={"user_id": member["id"], "role": "member"},
    )
    print(f"Invite response: {invite_response.status_code} {invite_response.json()}")
    assert invite_response.status_code == 200

    me_response = await client.get("/api/users/me", headers={"X-User-ID": member["id"]})
    memberships = me_response.json()["data"]["org_memberships"]
    member_membership = next(
        m for m in memberships if m["organisation_name"] == "Permission Test Org"
    )
    assert member_membership["role"] == "member"
    assert "admin:access" not in member_membership["permissions"]
    assert "org:write" not in member_membership["permissions"]
