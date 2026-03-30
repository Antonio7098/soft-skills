"""Integration tests for admin user management APIs."""

from __future__ import annotations

from pathlib import Path

import pytest
import pytest_asyncio
from alembic.config import Config
from alembic import command

from soft_skills_backend.platform.db.models import WorkflowEventRecord


def _migrate(test_settings) -> None:
    alembic_config = Config(str(Path(__file__).resolve().parents[2] / "alembic.ini"))
    alembic_config.set_main_option("sqlalchemy.url", test_settings.database_url)
    command.upgrade(alembic_config, "head")


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


async def _create_org_and_make_admin(
    client, *, email: str, display_name: str, org_name: str, org_slug: str
):
    user = await _register_user(client, email=email, display_name=display_name)
    org_response = await client.post(
        "/api/organisations",
        headers={"X-User-ID": user["id"]},
        json={"name": org_name, "slug": org_slug},
    )
    assert org_response.status_code == 200
    org = org_response.json()["data"]
    return user, org


async def _add_member_to_org(
    client, *, admin_id: str, org_id: str, member_id: str, role: str = "member"
):
    response = await client.post(
        f"/api/organisations/{org_id}/members",
        headers={"X-User-ID": admin_id, "X-Organisation-ID": org_id},
        json={"user_id": member_id, "role": role},
    )
    assert response.status_code == 200
    return response.json()["data"]


@pytest.mark.asyncio
async def test_list_users_returns_org_members_only(app, client, test_settings) -> None:
    """GET /admin/users returns org members (admin who created org is auto-added)."""
    _migrate(test_settings)
    admin, org = await _create_org_and_make_admin(
        client,
        email="admin-list@example.com",
        display_name="Admin List",
        org_name="List Test Org",
        org_slug="list-test-org",
    )

    response = await client.get(
        "/api/admin/users",
        headers={"X-User-ID": admin["id"], "X-Organisation-ID": org["id"]},
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["total"] == 1
    assert len(data["users"]) == 1
    assert data["users"][0]["user_id"] == admin["id"]
    assert data["users"][0]["organisation_role"] == "admin"


@pytest.mark.asyncio
async def test_list_users_returns_org_members(app, client, test_settings) -> None:
    """GET /admin/users returns org members."""
    _migrate(test_settings)
    admin, org = await _create_org_and_make_admin(
        client,
        email="admin-list2@example.com",
        display_name="Admin List 2",
        org_name="List Test Org 2",
        org_slug="list-test-org-2",
    )
    org_id = org["id"]

    member = await _register_user(
        client, email="member-list@example.com", display_name="Member List"
    )
    await _add_member_to_org(client, admin_id=admin["id"], org_id=org_id, member_id=member["id"])

    response = await client.get(
        "/api/admin/users",
        headers={"X-User-ID": admin["id"], "X-Organisation-ID": org_id},
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["total"] == 2
    user_ids = [u["user_id"] for u in data["users"]]
    assert admin["id"] in user_ids
    assert member["id"] in user_ids


@pytest.mark.asyncio
async def test_list_users_pagination(app, client, test_settings) -> None:
    """GET /admin/users supports offset and limit."""
    _migrate(test_settings)
    admin, org = await _create_org_and_make_admin(
        client,
        email="admin-page@example.com",
        display_name="Admin Page",
        org_name="Page Test Org",
        org_slug="page-test-org",
    )
    org_id = org["id"]

    for i in range(5):
        member = await _register_user(
            client, email=f"member-page{i}@example.com", display_name=f"Member Page {i}"
        )
        await _add_member_to_org(
            client, admin_id=admin["id"], org_id=org_id, member_id=member["id"]
        )

    response = await client.get(
        "/api/admin/users",
        headers={"X-User-ID": admin["id"], "X-Organisation-ID": org_id},
        params={"offset": 1, "limit": 2},
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data["users"]) == 2
    assert data["total"] == 6
    assert data["offset"] == 1
    assert data["limit"] == 2


@pytest.mark.asyncio
async def test_list_users_search_by_email(app, client, test_settings) -> None:
    """GET /admin/users supports search by email."""
    _migrate(test_settings)
    admin, org = await _create_org_and_make_admin(
        client,
        email="admin-search@example.com",
        display_name="Admin Search",
        org_name="Search Test Org",
        org_slug="search-test-org",
    )
    org_id = org["id"]

    unique_user = await _register_user(
        client, email="unique-user-123@example.com", display_name="Unique User"
    )
    await _register_user(client, email="other-user-456@example.com", display_name="Other User")
    await _add_member_to_org(
        client, admin_id=admin["id"], org_id=org_id, member_id=unique_user["id"]
    )

    response = await client.get(
        "/api/admin/users",
        headers={"X-User-ID": admin["id"], "X-Organisation-ID": org_id},
        params={"search": "unique-user-123"},
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["total"] >= 1
    user_emails = [u["email"] for u in data["users"]]
    assert "unique-user-123@example.com" in user_emails


@pytest.mark.asyncio
async def test_list_users_filter_by_role(app, client, test_settings) -> None:
    """GET /admin/users supports filter by role."""
    _migrate(test_settings)
    admin, org = await _create_org_and_make_admin(
        client,
        email="admin-filter@example.com",
        display_name="Admin Filter",
        org_name="Filter Test Org",
        org_slug="filter-test-org",
    )
    org_id = org["id"]

    member = await _register_user(
        client, email="member-filter@example.com", display_name="Member Filter"
    )
    await _add_member_to_org(
        client, admin_id=admin["id"], org_id=org_id, member_id=member["id"], role="member"
    )

    response = await client.get(
        "/api/admin/users",
        headers={"X-User-ID": admin["id"], "X-Organisation-ID": org_id},
        params={"role": "admin"},
    )
    assert response.status_code == 200
    data = response.json()["data"]
    for user in data["users"]:
        assert user["organisation_role"] == "admin"

    response = await client.get(
        "/api/admin/users",
        headers={"X-User-ID": admin["id"], "X-Organisation-ID": org_id},
        params={"role": "member"},
    )
    assert response.status_code == 200
    data = response.json()["data"]
    for user in data["users"]:
        assert user["organisation_role"] == "member"


@pytest.mark.asyncio
async def test_list_users_filter_by_is_active(app, client, test_settings) -> None:
    """GET /admin/users supports filter by is_active status."""
    _migrate(test_settings)
    admin, org = await _create_org_and_make_admin(
        client,
        email="admin-active@example.com",
        display_name="Admin Active",
        org_name="Active Test Org",
        org_slug="active-test-org",
    )
    org_id = org["id"]

    member = await _register_user(
        client, email="member-active@example.com", display_name="Member Active"
    )
    await _add_member_to_org(client, admin_id=admin["id"], org_id=org_id, member_id=member["id"])

    response = await client.get(
        "/api/admin/users",
        headers={"X-User-ID": admin["id"], "X-Organisation-ID": org_id},
        params={"is_active": "true"},
    )
    assert response.status_code == 200
    data = response.json()["data"]
    for user in data["users"]:
        assert user["is_active"] is True


@pytest.mark.asyncio
async def test_list_users_requires_authentication(client, test_settings) -> None:
    """GET /admin/users returns 401 without authentication."""
    _migrate(test_settings)
    response = await client.get("/api/admin/users")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_list_users_requires_org_admin(client, test_settings) -> None:
    """GET /admin/users returns 403 for non-admin org member."""
    _migrate(test_settings)
    admin, org = await _create_org_and_make_admin(
        client,
        email="admin-nonauthadmin@example.com",
        display_name="Admin NoAuth",
        org_name="NoAuth Test Org",
        org_slug="noauthtest-org",
    )
    org_id = org["id"]

    member = await _register_user(
        client, email="member-noauth@example.com", display_name="Member NoAuth"
    )
    await _add_member_to_org(
        client, admin_id=admin["id"], org_id=org_id, member_id=member["id"], role="member"
    )

    response = await client.get(
        "/api/admin/users",
        headers={"X-User-ID": member["id"], "X-Organisation-ID": org_id},
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_get_user_returns_user_details(app, client, test_settings) -> None:
    """GET /admin/users/{user_id} returns user details."""
    _migrate(test_settings)
    admin, org = await _create_org_and_make_admin(
        client,
        email="admin-get@example.com",
        display_name="Admin Get",
        org_name="Get Test Org",
        org_slug="get-test-org",
    )
    org_id = org["id"]

    member = await _register_user(client, email="member-get@example.com", display_name="Member Get")
    await _add_member_to_org(client, admin_id=admin["id"], org_id=org_id, member_id=member["id"])

    response = await client.get(
        f"/api/admin/users/{member['id']}",
        headers={"X-User-ID": admin["id"], "X-Organisation-ID": org_id},
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["user_id"] == member["id"]
    assert data["email"] == "member-get@example.com"
    assert data["display_name"] == "Member Get"


@pytest.mark.asyncio
async def test_get_user_returns_none_for_nonexistent_user(app, client, test_settings) -> None:
    """GET /admin/users/{user_id} returns 200 with null for nonexistent user."""
    _migrate(test_settings)
    admin, org = await _create_org_and_make_admin(
        client,
        email="admin-get404@example.com",
        display_name="Admin Get 404",
        org_name="Get 404 Test Org",
        org_slug="get404-test-org",
    )

    response = await client.get(
        "/api/admin/users/nonexistent-user-id",
        headers={"X-User-ID": admin["id"], "X-Organisation-ID": org["id"]},
    )
    assert response.status_code == 200
    assert response.json()["data"] is None


@pytest.mark.asyncio
async def test_update_user_role(app, client, test_settings) -> None:
    """PUT /admin/users/{user_id}/role changes user role."""
    _migrate(test_settings)
    admin, org = await _create_org_and_make_admin(
        client,
        email="admin-role@example.com",
        display_name="Admin Role",
        org_name="Role Test Org",
        org_slug="role-test-org",
    )
    org_id = org["id"]

    member = await _register_user(
        client, email="member-role@example.com", display_name="Member Role"
    )
    await _add_member_to_org(
        client, admin_id=admin["id"], org_id=org_id, member_id=member["id"], role="member"
    )

    response = await client.put(
        f"/api/admin/users/{member['id']}/role",
        headers={"X-User-ID": admin["id"], "X-Organisation-ID": org_id},
        json={"role": "admin"},
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["organisation_role"] == "admin"

    events = _get_workflow_events(app, "admin.user.role_changed.v1")
    role_change_events = [e for e in events if e.payload.get("target_user_id") == member["id"]]
    assert len(role_change_events) == 1
    assert role_change_events[0].payload["old_role"] == "member"
    assert role_change_events[0].payload["new_role"] == "admin"


@pytest.mark.asyncio
async def test_update_user_role_invalid_role(app, client, test_settings) -> None:
    """PUT /admin/users/{user_id}/role rejects invalid role."""
    _migrate(test_settings)
    admin, org = await _create_org_and_make_admin(
        client,
        email="admin-roleinv@example.com",
        display_name="Admin Role Inv",
        org_name="Role Inv Test Org",
        org_slug="roleinv-test-org",
    )
    org_id = org["id"]

    member = await _register_user(
        client, email="member-roleinv@example.com", display_name="Member Role Inv"
    )
    await _add_member_to_org(
        client, admin_id=admin["id"], org_id=org_id, member_id=member["id"], role="member"
    )

    response = await client.put(
        f"/api/admin/users/{member['id']}/role",
        headers={"X-User-ID": admin["id"], "X-Organisation-ID": org_id},
        json={"role": "superadmin"},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_update_user_role_user_not_in_org(app, client, test_settings) -> None:
    """PUT /admin/users/{user_id}/role returns 404 when user not in org."""
    _migrate(test_settings)
    admin, org = await _create_org_and_make_admin(
        client,
        email="admin-rolenotinorg@example.com",
        display_name="Admin Role NotInOrg",
        org_name="Role NotInOrg Test Org",
        org_slug="rolenotinorg-test-org",
    )

    other_user = await _register_user(
        client, email="other-rolenotinorg@example.com", display_name="Other Role NotInOrg"
    )

    response = await client.put(
        f"/api/admin/users/{other_user['id']}/role",
        headers={"X-User-ID": admin["id"], "X-Organisation-ID": org["id"]},
        json={"role": "admin"},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_user_status_suspend(app, client, test_settings) -> None:
    """PATCH /admin/users/{user_id}/status suspends a user."""
    _migrate(test_settings)
    admin, org = await _create_org_and_make_admin(
        client,
        email="admin-suspend@example.com",
        display_name="Admin Suspend",
        org_name="Suspend Test Org",
        org_slug="suspend-test-org",
    )
    org_id = org["id"]

    member = await _register_user(
        client, email="member-suspend@example.com", display_name="Member Suspend"
    )
    await _add_member_to_org(
        client, admin_id=admin["id"], org_id=org_id, member_id=member["id"], role="member"
    )

    response = await client.patch(
        f"/api/admin/users/{member['id']}/status",
        headers={"X-User-ID": admin["id"], "X-Organisation-ID": org_id},
        json={"is_active": False},
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["is_active"] is False

    events = _get_workflow_events(app, "admin.user.suspended.v1")
    suspend_events = [e for e in events if e.payload.get("target_user_id") == member["id"]]
    assert len(suspend_events) == 1
    assert suspend_events[0].payload["is_active"] is False


@pytest.mark.asyncio
async def test_update_user_status_activate(app, client, test_settings) -> None:
    """PATCH /admin/users/{user_id}/status activates a user."""
    _migrate(test_settings)
    admin, org = await _create_org_and_make_admin(
        client,
        email="admin-activate@example.com",
        display_name="Admin Activate",
        org_name="Activate Test Org",
        org_slug="activate-test-org",
    )
    org_id = org["id"]

    member = await _register_user(
        client, email="member-activate@example.com", display_name="Member Activate"
    )
    await _add_member_to_org(
        client, admin_id=admin["id"], org_id=org_id, member_id=member["id"], role="member"
    )

    await client.patch(
        f"/api/admin/users/{member['id']}/status",
        headers={"X-User-ID": admin["id"], "X-Organisation-ID": org_id},
        json={"is_active": False},
    )

    response = await client.patch(
        f"/api/admin/users/{member['id']}/status",
        headers={"X-User-ID": admin["id"], "X-Organisation-ID": org_id},
        json={"is_active": True},
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["is_active"] is True

    events = _get_workflow_events(app, "admin.user.activated.v1")
    activate_events = [e for e in events if e.payload.get("target_user_id") == member["id"]]
    assert len(activate_events) == 1
    assert activate_events[0].payload["is_active"] is True


@pytest.mark.asyncio
async def test_add_user_to_org_creates_new_user(app, client, test_settings) -> None:
    """POST /admin/users adds a new user to org."""
    _migrate(test_settings)
    admin, org = await _create_org_and_make_admin(
        client,
        email="admin-add@example.com",
        display_name="Admin Add",
        org_name="Add Test Org",
        org_slug="add-test-org",
    )
    org_id = org["id"]

    response = await client.post(
        "/api/admin/users",
        headers={"X-User-ID": admin["id"], "X-Organisation-ID": org_id},
        json={"email": "newuser-add@example.com", "role": "member"},
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["email"] == "newuser-add@example.com"
    assert data["organisation_id"] == org_id
    assert data["organisation_role"] == "member"

    events = _get_workflow_events(app, "admin.user.added_to_org.v1")
    assert len(events) == 1
    assert events[0].payload["organisation_id"] == org_id


@pytest.mark.asyncio
async def test_add_user_to_org_existing_user(app, client, test_settings) -> None:
    """POST /admin/users adds existing user to org."""
    _migrate(test_settings)
    admin, org = await _create_org_and_make_admin(
        client,
        email="admin-addexist@example.com",
        display_name="Admin Add Exist",
        org_name="Add Exist Test Org",
        org_slug="addexist-test-org",
    )
    org_id = org["id"]

    existing_user = await _register_user(
        client, email="existing-add@example.com", display_name="Existing Add"
    )

    response = await client.post(
        "/api/admin/users",
        headers={"X-User-ID": admin["id"], "X-Organisation-ID": org_id},
        json={"email": "existing-add@example.com", "role": "admin"},
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["user_id"] == existing_user["id"]
    assert data["organisation_role"] == "admin"


@pytest.mark.asyncio
async def test_add_user_to_org_already_member(app, client, test_settings) -> None:
    """POST /admin/users returns 409 when user already in org."""
    _migrate(test_settings)
    admin, org = await _create_org_and_make_admin(
        client,
        email="admin-addalready@example.com",
        display_name="Admin Add Already",
        org_name="Add Already Test Org",
        org_slug="addalready-test-org",
    )
    org_id = org["id"]

    member = await _register_user(
        client, email="member-addalready@example.com", display_name="Member Add Already"
    )
    await _add_member_to_org(
        client, admin_id=admin["id"], org_id=org_id, member_id=member["id"], role="member"
    )

    response = await client.post(
        "/api/admin/users",
        headers={"X-User-ID": admin["id"], "X-Organisation-ID": org_id},
        json={"email": member["email"], "role": "admin"},
    )
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "SS-DOMAIN-007"


@pytest.mark.asyncio
async def test_add_user_to_org_invalid_email(app, client, test_settings) -> None:
    """POST /admin/users returns 422 for invalid email."""
    _migrate(test_settings)
    admin, org = await _create_org_and_make_admin(
        client,
        email="admin-addinv@example.com",
        display_name="Admin Add Inv",
        org_name="Add Inv Test Org",
        org_slug="addinv-test-org",
    )

    response = await client.post(
        "/api/admin/users",
        headers={"X-User-ID": admin["id"], "X-Organisation-ID": org["id"]},
        json={"email": "not-an-email", "role": "member"},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_bulk_user_operation_suspend(app, client, test_settings) -> None:
    """POST /admin/users/bulk suspends multiple users."""
    _migrate(test_settings)
    admin, org = await _create_org_and_make_admin(
        client,
        email="admin-bulk@example.com",
        display_name="Admin Bulk",
        org_name="Bulk Test Org",
        org_slug="bulk-test-org",
    )
    org_id = org["id"]

    member1 = await _register_user(
        client, email="member-bulk1@example.com", display_name="Member Bulk 1"
    )
    member2 = await _register_user(
        client, email="member-bulk2@example.com", display_name="Member Bulk 2"
    )
    await _add_member_to_org(client, admin_id=admin["id"], org_id=org_id, member_id=member1["id"])
    await _add_member_to_org(client, admin_id=admin["id"], org_id=org_id, member_id=member2["id"])

    response = await client.post(
        "/api/admin/users/bulk",
        headers={"X-User-ID": admin["id"], "X-Organisation-ID": org_id},
        json={
            "user_ids": [member1["id"], member2["id"]],
            "operation": "suspend",
        },
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["operation"] == "suspend"
    assert data["requested_count"] == 2
    assert data["success_count"] == 2
    assert data["failure_count"] == 0


@pytest.mark.asyncio
async def test_bulk_user_operation_activate(app, client, test_settings) -> None:
    """POST /admin/users/bulk activates multiple users."""
    _migrate(test_settings)
    admin, org = await _create_org_and_make_admin(
        client,
        email="admin-bulkact@example.com",
        display_name="Admin Bulk Act",
        org_name="Bulk Act Test Org",
        org_slug="bulkact-test-org",
    )
    org_id = org["id"]

    member1 = await _register_user(
        client, email="member-bulkact1@example.com", display_name="Member Bulk Act 1"
    )
    member2 = await _register_user(
        client, email="member-bulkact2@example.com", display_name="Member Bulk Act 2"
    )
    await _add_member_to_org(client, admin_id=admin["id"], org_id=org_id, member_id=member1["id"])
    await _add_member_to_org(client, admin_id=admin["id"], org_id=org_id, member_id=member2["id"])

    await client.post(
        "/api/admin/users/bulk",
        headers={"X-User-ID": admin["id"], "X-Organisation-ID": org_id},
        json={
            "user_ids": [member1["id"], member2["id"]],
            "operation": "suspend",
        },
    )

    response = await client.post(
        "/api/admin/users/bulk",
        headers={"X-User-ID": admin["id"], "X-Organisation-ID": org_id},
        json={
            "user_ids": [member1["id"], member2["id"]],
            "operation": "activate",
        },
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["operation"] == "activate"
    assert data["success_count"] == 2


@pytest.mark.asyncio
async def test_bulk_user_operation_change_role(app, client, test_settings) -> None:
    """POST /admin/users/bulk changes role for multiple users."""
    _migrate(test_settings)
    admin, org = await _create_org_and_make_admin(
        client,
        email="admin-bulkrole@example.com",
        display_name="Admin Bulk Role",
        org_name="Bulk Role Test Org",
        org_slug="bulkrole-test-org",
    )
    org_id = org["id"]

    member1 = await _register_user(
        client, email="member-bulkrole1@example.com", display_name="Member Bulk Role 1"
    )
    member2 = await _register_user(
        client, email="member-bulkrole2@example.com", display_name="Member Bulk Role 2"
    )
    await _add_member_to_org(
        client, admin_id=admin["id"], org_id=org_id, member_id=member1["id"], role="member"
    )
    await _add_member_to_org(
        client, admin_id=admin["id"], org_id=org_id, member_id=member2["id"], role="member"
    )

    response = await client.post(
        "/api/admin/users/bulk",
        headers={"X-User-ID": admin["id"], "X-Organisation-ID": org_id},
        json={
            "user_ids": [member1["id"], member2["id"]],
            "operation": "change_role",
            "payload": {"role": "admin"},
        },
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["operation"] == "change_role"
    assert data["success_count"] == 2


@pytest.mark.asyncio
async def test_bulk_user_operation_partial_failure(app, client, test_settings) -> None:
    """POST /admin/users/bulk handles partial failures."""
    _migrate(test_settings)
    admin, org = await _create_org_and_make_admin(
        client,
        email="admin-bulkfail@example.com",
        display_name="Admin Bulk Fail",
        org_name="Bulk Fail Test Org",
        org_slug="bulkfail-test-org",
    )
    org_id = org["id"]

    member = await _register_user(
        client, email="member-bulkfail@example.com", display_name="Member Bulk Fail"
    )
    await _add_member_to_org(
        client, admin_id=admin["id"], org_id=org_id, member_id=member["id"], role="member"
    )

    response = await client.post(
        "/api/admin/users/bulk",
        headers={"X-User-ID": admin["id"], "X-Organisation-ID": org_id},
        json={
            "user_ids": [member["id"], "nonexistent-user-id"],
            "operation": "suspend",
        },
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["requested_count"] == 2
    assert data["success_count"] == 1
    assert data["failure_count"] == 1
    assert "nonexistent-user-id" in data["failed_user_ids"]


@pytest.mark.asyncio
async def test_bulk_user_operation_empty_user_ids(app, client, test_settings) -> None:
    """POST /admin/users/bulk returns 422 for empty user_ids."""
    _migrate(test_settings)
    admin, org = await _create_org_and_make_admin(
        client,
        email="admin-bulkempty@example.com",
        display_name="Admin Bulk Empty",
        org_name="Bulk Empty Test Org",
        org_slug="bulkempty-test-org",
    )

    response = await client.post(
        "/api/admin/users/bulk",
        headers={"X-User-ID": admin["id"], "X-Organisation-ID": org["id"]},
        json={
            "user_ids": [],
            "operation": "suspend",
        },
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_get_user_activity_returns_activity(app, client, test_settings) -> None:
    """GET /admin/users/{user_id}/activity returns user activity summary."""
    _migrate(test_settings)
    admin, org = await _create_org_and_make_admin(
        client,
        email="admin-activity@example.com",
        display_name="Admin Activity",
        org_name="Activity Test Org",
        org_slug="activity-test-org",
    )
    org_id = org["id"]

    member = await _register_user(
        client, email="member-activity@example.com", display_name="Member Activity"
    )
    await _add_member_to_org(
        client, admin_id=admin["id"], org_id=org_id, member_id=member["id"], role="member"
    )

    response = await client.get(
        f"/api/admin/users/{member['id']}/activity",
        headers={"X-User-ID": admin["id"], "X-Organisation-ID": org_id},
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["user_id"] == member["id"]
    assert data["email"] == "member-activity@example.com"
    assert "total_sessions" in data
    assert "total_attempts" in data
    assert "recent_sessions" in data
    assert "recent_attempts" in data
    assert "recent_logins" in data


@pytest.mark.asyncio
async def test_get_user_returns_none_for_nonexistent_user(app, client, test_settings) -> None:
    """GET /admin/users/{user_id} returns 200 with null data for nonexistent user."""
    _migrate(test_settings)
    admin, org = await _create_org_and_make_admin(
        client,
        email="admin-get404@example.com",
        display_name="Admin Get 404",
        org_name="Get 404 Test Org",
        org_slug="get404-test-org",
    )

    response = await client.get(
        "/api/admin/users/nonexistent-user-id",
        headers={"X-User-ID": admin["id"], "X-Organisation-ID": org["id"]},
    )
    assert response.status_code == 200
    assert response.json()["data"] is None


def _get_workflow_events(app, event_type: str | None = None):
    """Helper to get workflow events from the database."""
    with app.state.container.session_factory() as session:
        query = session.query(WorkflowEventRecord)
        if event_type:
            query = query.filter(WorkflowEventRecord.event_type == event_type)
        return query.all()
