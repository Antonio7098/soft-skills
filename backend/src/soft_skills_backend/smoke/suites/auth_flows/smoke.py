"""Auth flows smoke suite."""

from __future__ import annotations

import asyncio
from typing import Any, cast
from uuid import uuid4

import httpx

from soft_skills_backend.config import Settings
from soft_skills_backend.shared.errors import provider_error
from soft_skills_backend.smoke.contracts import SmokeCase, SmokeContext
from soft_skills_backend.smoke.support.backend import SmokeBackendClient
from soft_skills_backend.smoke.support.environment import (
    SmokeApplicationSessionFactory,
)

from .contracts import AuthFlowsSmokeResult

SMOKE_TIMEOUT_SECONDS = 60.0


class AuthFlowsSmoke(SmokeCase):
    """Verifies registration, profile, and auth error handling end to end."""

    name = "auth-flows"
    description = (
        "Assert user registration, profile read/write, and auth/authorization error codes."
    )

    def __init__(
        self,
        *,
        session_factory: SmokeApplicationSessionFactory | None = None,
        timeout_seconds: float = SMOKE_TIMEOUT_SECONDS,
    ) -> None:
        self._session_factory = session_factory or SmokeApplicationSessionFactory()
        self._timeout_seconds = timeout_seconds

    def run(self, context: SmokeContext) -> AuthFlowsSmokeResult:
        try:
            return asyncio.run(
                asyncio.wait_for(self._run(context.settings), timeout=self._timeout_seconds)
            )
        except TimeoutError as exc:
            raise RuntimeError(
                f"Auth flows smoke exceeded the allowed runtime budget of {self._timeout_seconds}s"
            ) from exc

    async def _run(self, settings: Settings) -> AuthFlowsSmokeResult:
        async with self._session_factory.open(settings) as backend:
            return await self._run_auth_flows(backend)

    async def _run_auth_flows(self, backend: SmokeBackendClient) -> AuthFlowsSmokeResult:
        suffix = uuid4().hex[:8]
        email = f"auth-smoke-{suffix}@example.com"
        display_name = "Auth Smoke User"

        # --- Happy path: registration ---
        user = await backend.register_user(email=email, display_name=display_name)
        user_id = str(user["id"])

        if user["email"] != email:
            raise provider_error(
                "Registered user email mismatch",
                code="SS-PROVIDER-017",
                details={"expected": email, "actual": user["email"]},
            )

        # --- Happy path: get user profile ---
        profile = await backend.get_user_me(user_id=user_id)
        profile_display_name = str(profile["display_name"])
        profile_data = cast(dict[str, object], profile["profile"])
        profile_goals = [str(g) for g in cast(list[object], profile_data["goals"])]

        if profile_display_name != display_name:
            raise provider_error(
                "Profile display name mismatch",
                code="SS-PROVIDER-017",
                details={"expected": display_name, "actual": profile_display_name},
            )

        # --- Happy path: update profile ---
        new_role = "Senior Consultant"
        updated = await backend.update_profile(user_id=user_id, target_role=new_role)
        updated_profile = cast(dict[str, object], updated["profile"])
        updated_role = cast("str | None", updated_profile.get("target_role"))

        if updated_role != new_role:
            raise provider_error(
                "Profile update target_role mismatch",
                code="SS-PROVIDER-017",
                details={"expected": new_role, "actual": updated_role},
            )

        # --- Error path: missing X-User-ID header ---
        missing_resp = await backend._client.get("/api/users/me")
        if missing_resp.status_code != 401:
            raise provider_error(
                "Missing auth header should return 401",
                code="SS-PROVIDER-017",
                details={
                    "expected_status": 401,
                    "actual_status": missing_resp.status_code,
                    "body": missing_resp.text,
                },
            )
        missing_body = _extract_error(missing_resp)
        missing_code = str(missing_body.get("code", ""))
        if missing_code != "SS-AUTH-001":
            raise provider_error(
                "Missing auth header error code mismatch",
                code="SS-PROVIDER-017",
                details={"expected": "SS-AUTH-001", "actual": missing_code},
            )

        # --- Error path: invalid X-User-ID ---
        bogus_resp = await backend._client.get(
            "/api/users/me",
            headers={"X-User-ID": "nonexistent-user-id"},
        )
        if bogus_resp.status_code != 401:
            raise provider_error(
                "Invalid user ID should return 401",
                code="SS-PROVIDER-017",
                details={
                    "expected_status": 401,
                    "actual_status": bogus_resp.status_code,
                    "body": bogus_resp.text,
                },
            )
        bogus_body = _extract_error(bogus_resp)
        bogus_code = str(bogus_body.get("code", ""))
        if bogus_code != "SS-AUTH-002":
            raise provider_error(
                "Invalid user ID error code mismatch",
                code="SS-PROVIDER-017",
                details={"expected": "SS-AUTH-002", "actual": bogus_code},
            )

        # --- Error path: duplicate email registration ---
        dup_resp = await backend._client.post(
            "/api/auth/register",
            json={
                "email": email,
                "display_name": display_name,
                "target_role": "Consultant",
                "goals": ["Duplicate check"],
                "practice_preferences": {},
            },
        )
        if dup_resp.status_code != 409:
            raise provider_error(
                "Duplicate email should return 409",
                code="SS-PROVIDER-017",
                details={
                    "expected_status": 409,
                    "actual_status": dup_resp.status_code,
                    "body": dup_resp.text,
                },
            )
        dup_body = _extract_error(dup_resp)
        dup_code = str(dup_body.get("code", ""))
        if dup_code != "SS-DOMAIN-002":
            raise provider_error(
                "Duplicate email error code mismatch",
                code="SS-PROVIDER-017",
                details={"expected": "SS-DOMAIN-002", "actual": dup_code},
            )

        # --- Error path: non-admin org member on admin endpoint ---
        admin_user = await backend.register_user(
            email=f"auth-admin-smoke-{suffix}@example.com",
            display_name="Auth Admin Smoke",
        )
        admin_id = str(admin_user["id"])

        member_user = await backend.register_user(
            email=f"auth-member-smoke-{suffix}@example.com",
            display_name="Auth Member Smoke",
        )
        member_id = str(member_user["id"])

        org = await backend.create_organisation(
            user_id=admin_id,
            name=f"Auth Smoke Org {suffix}",
            slug=f"auth-smoke-org-{suffix}",
        )
        org_id = str(org["id"])

        await backend.add_member(
            user_id=admin_id,
            organisation_id=org_id,
            new_member_id=member_id,
            role="member",
        )

        # Member tries to update org (requires admin)
        non_admin_resp = await backend._client.patch(
            f"/api/organisations/{org_id}",
            headers={"X-User-ID": member_id, "X-Organisation-ID": org_id},
            json={"name": "Should Not Work"},
        )
        if non_admin_resp.status_code != 403:
            raise provider_error(
                "Non-admin org member should return 403",
                code="SS-PROVIDER-017",
                details={
                    "expected_status": 403,
                    "actual_status": non_admin_resp.status_code,
                    "body": non_admin_resp.text,
                },
            )
        non_admin_body = _extract_error(non_admin_resp)
        non_admin_code = str(non_admin_body.get("code", ""))
        if non_admin_code != "SS-AUTH-004":
            raise provider_error(
                "Non-admin org member error code mismatch",
                code="SS-PROVIDER-017",
                details={"expected": "SS-AUTH-004", "actual": non_admin_code},
            )

        return AuthFlowsSmokeResult(
            registered_user_id=user_id,
            registered_email=email,
            profile_display_name=profile_display_name,
            profile_goals=profile_goals,
            updated_target_role=updated_role,
            missing_header_status=401,
            missing_header_error_code=missing_code,
            invalid_user_status=401,
            invalid_user_error_code=bogus_code,
            duplicate_email_status=409,
            duplicate_email_error_code=dup_code,
            org_non_admin_status=403,
            org_non_admin_error_code=non_admin_code,
        )


def _extract_error(response: httpx.Response) -> dict[str, Any]:
    """Extract the error body from an error envelope response."""
    body = cast(dict[str, Any], response.json())
    if "error" in body:
        return cast(dict[str, Any], body["error"])
    return body
