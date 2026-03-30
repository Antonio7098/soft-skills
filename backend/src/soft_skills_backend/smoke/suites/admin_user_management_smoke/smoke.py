"""Admin user management smoke suite."""

from __future__ import annotations

import asyncio
from uuid import uuid4

from soft_skills_backend.config import Settings
from soft_skills_backend.smoke.contracts import SmokeCase, SmokeContext
from soft_skills_backend.smoke.support.backend import SmokeBackendClient
from soft_skills_backend.smoke.support.environment import (
    SmokeApplicationSessionFactory,
)
from soft_skills_backend.smoke.support.models import SmokeActors

from .contracts import AdminUserManagementSmokeResult

SMOKE_TIMEOUT_SECONDS = 120.0


class AdminUserManagementSmoke(SmokeCase):
    """Verifies admin user management endpoints end to end without LLM keys."""

    name = "admin-user-management"
    description = (
        "Assert admin user listing, role management, status toggle, "
        "bulk operations, and user activity APIs."
    )

    def __init__(
        self,
        *,
        session_factory: SmokeApplicationSessionFactory | None = None,
        timeout_seconds: float = SMOKE_TIMEOUT_SECONDS,
    ) -> None:
        self._session_factory = session_factory or SmokeApplicationSessionFactory()
        self._timeout_seconds = timeout_seconds

    def run(self, context: SmokeContext) -> AdminUserManagementSmokeResult:
        try:
            return asyncio.run(
                asyncio.wait_for(self._run(context.settings), timeout=self._timeout_seconds)
            )
        except TimeoutError as exc:
            raise RuntimeError(
                f"Admin user management smoke exceeded the allowed runtime budget of {self._timeout_seconds}s"
            ) from exc

    async def _run(self, settings: Settings) -> AdminUserManagementSmokeResult:
        async with self._session_factory.open(settings) as backend:
            actors = await self._prepare_actors(backend)
            return await self._run_user_management_smoke(backend, actors)

    async def _prepare_actors(self, backend: SmokeBackendClient) -> SmokeActors:
        suffix = uuid4().hex[:8]
        admin = await backend.register_user(
            email=f"admin-usermgmt-{suffix}@example.com",
            display_name="Admin UserMgmt Smoke",
        )
        member = await backend.register_user(
            email=f"member-usermgmt-{suffix}@example.com",
            display_name="Member UserMgmt Smoke",
        )
        return SmokeActors(
            admin_id=str(admin["id"]),
            learner_id=str(member["id"]),
        )

    async def _run_user_management_smoke(
        self,
        backend: SmokeBackendClient,
        actors: SmokeActors,
    ) -> AdminUserManagementSmokeResult:
        suffix = uuid4().hex[:8]
        org_name = f"UserMgmt Smoke Org {suffix}"
        org_slug = f"usermgmt-smoke-org-{suffix}"

        org = await backend.create_organisation(
            user_id=actors.admin_id,
            name=org_name,
            slug=org_slug,
        )
        org_id = str(org["id"])

        await backend.add_member(
            user_id=actors.admin_id,
            organisation_id=org_id,
            new_member_id=actors.learner_id,
            role="member",
        )

        list_result = await backend.admin_list_users(
            user_id=actors.admin_id,
            organisation_id=org_id,
        )
        listed_users_count = len(list_result["users"])
        listed_users_total = list_result["total"]

        get_result = await backend.admin_get_user(
            user_id=actors.admin_id,
            organisation_id=org_id,
            target_user_id=actors.learner_id,
        )
        get_user_email = str(get_result["email"])

        role_result = await backend.admin_update_user_role(
            user_id=actors.admin_id,
            organisation_id=org_id,
            target_user_id=actors.learner_id,
            role="admin",
        )
        updated_role = str(role_result["organisation_role"])

        suspend_result = await backend.admin_update_user_status(
            user_id=actors.admin_id,
            organisation_id=org_id,
            target_user_id=actors.learner_id,
            is_active=False,
        )
        suspended_user_id = str(suspend_result["user_id"])
        assert suspend_result["is_active"] is False

        activate_result = await backend.admin_update_user_status(
            user_id=actors.admin_id,
            organisation_id=org_id,
            target_user_id=actors.learner_id,
            is_active=True,
        )
        activated_user_id = str(activate_result["user_id"])
        assert activate_result["is_active"] is True

        new_user_email = f"new-usermgmt-{suffix}@example.com"
        add_result = await backend.admin_add_user(
            user_id=actors.admin_id,
            organisation_id=org_id,
            email=new_user_email,
            role="member",
        )
        added_user_email = str(add_result["email"])
        added_user_id = str(add_result["user_id"])

        bulk_suspend_result = await backend.admin_bulk_user_operation(
            user_id=actors.admin_id,
            organisation_id=org_id,
            user_ids=[actors.learner_id, added_user_id],
            operation="suspend",
        )
        bulk_suspend_count = bulk_suspend_result["success_count"]

        bulk_activate_result = await backend.admin_bulk_user_operation(
            user_id=actors.admin_id,
            organisation_id=org_id,
            user_ids=[actors.learner_id, added_user_id],
            operation="activate",
        )
        bulk_activate_count = bulk_activate_result["success_count"]

        activity_result = await backend.admin_get_user_activity(
            user_id=actors.admin_id,
            organisation_id=org_id,
            target_user_id=actors.learner_id,
        )
        user_activity_user_id = str(activity_result["user_id"])
        user_activity_total_sessions = int(activity_result["total_sessions"])

        return AdminUserManagementSmokeResult(
            organisation_id=org_id,
            admin_user_id=actors.admin_id,
            member_user_id=actors.learner_id,
            listed_users_count=listed_users_count,
            listed_users_total=listed_users_total,
            get_user_email=get_user_email,
            updated_role=updated_role,
            suspended_user_id=suspended_user_id,
            activated_user_id=activated_user_id,
            added_user_email=added_user_email,
            added_user_id=added_user_id,
            bulk_suspend_count=bulk_suspend_count,
            bulk_activate_count=bulk_activate_count,
            user_activity_user_id=user_activity_user_id,
            user_activity_total_sessions=user_activity_total_sessions,
        )
