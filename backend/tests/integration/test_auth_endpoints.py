from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config

from soft_skills_backend.platform.db.models import UserAccountRecord


def _migrate(test_settings) -> None:
    alembic_config = Config(str(Path(__file__).resolve().parents[2] / "alembic.ini"))
    alembic_config.set_main_option("sqlalchemy.url", test_settings.database_url)
    command.upgrade(alembic_config, "heads")


async def _register_user(
    client,
    *,
    email: str,
    display_name: str,
    password: str = "password123",
) -> dict[str, object]:
    response = await client.post(
        "/api/auth/register",
        json={
            "email": email,
            "display_name": display_name,
            "password": password,
        },
    )
    assert response.status_code == 200
    return response.json()["data"]


@pytest.mark.asyncio
async def test_login_returns_existing_user_with_valid_credentials(client, test_settings) -> None:
    _migrate(test_settings)
    created_user = await _register_user(
        client,
        email="login@example.com",
        display_name="Login User",
        password="password123",
    )

    response = await client.post(
        "/api/auth/login",
        json={"email": "login@example.com", "password": "password123"},
    )

    assert response.status_code == 200
    payload = response.json()["data"]
    assert payload["id"] == created_user["id"]
    assert payload["email"] == "login@example.com"


@pytest.mark.asyncio
async def test_login_rejects_invalid_password(client, test_settings) -> None:
    _migrate(test_settings)
    await _register_user(
        client,
        email="wrong-password@example.com",
        display_name="Wrong Password",
        password="password123",
    )

    response = await client.post(
        "/api/auth/login",
        json={"email": "wrong-password@example.com", "password": "incorrect1"},
    )

    assert response.status_code == 401
    assert response.json()["error"]["message"] == "Invalid email or password"


@pytest.mark.asyncio
async def test_delete_me_removes_current_account(client, test_settings) -> None:
    _migrate(test_settings)
    created_user = await _register_user(
        client,
        email="delete-me@example.com",
        display_name="Delete Me",
        password="password123",
    )

    delete_response = await client.delete(
        "/api/users/me",
        headers={"X-User-ID": str(created_user["id"])},
    )

    assert delete_response.status_code == 200
    assert delete_response.json()["data"] == {
        "deleted_user_id": created_user["id"],
        "status": "deleted",
    }

    me_response = await client.get(
        "/api/users/me",
        headers={"X-User-ID": str(created_user["id"])},
    )
    assert me_response.status_code == 401


@pytest.mark.asyncio
async def test_login_claims_legacy_backfilled_password(app, client, test_settings) -> None:
    _migrate(test_settings)
    created_user = await _register_user(
        client,
        email="legacy@example.com",
        display_name="Legacy User",
        password="password123",
    )
    with app.state.container.session_factory() as session:
        user = session.get(UserAccountRecord, str(created_user["id"]))
        assert user is not None
        user.created_at = datetime(2026, 3, 29, 10, 0, tzinfo=UTC)
        session.commit()

    response = await client.post(
        "/api/auth/login",
        json={"email": "legacy@example.com", "password": "new-password1"},
    )

    assert response.status_code == 200

    retry_response = await client.post(
        "/api/auth/login",
        json={"email": "legacy@example.com", "password": "new-password1"},
    )
    assert retry_response.status_code == 200
