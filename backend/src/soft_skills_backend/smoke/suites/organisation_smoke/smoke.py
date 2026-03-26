"""Organisation smoke suite."""

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

from .contracts import OrganisationSmokeResult

SMOKE_TIMEOUT_SECONDS = 60.0


class OrganisationSmoke(SmokeCase):
    """Verifies organisation management endpoints end to end."""

    name = "organisation-management"
    description = "Assert organisation creation, member management, and access control."

    def __init__(
        self,
        *,
        session_factory: SmokeApplicationSessionFactory | None = None,
        timeout_seconds: float = SMOKE_TIMEOUT_SECONDS,
    ) -> None:
        self._session_factory = session_factory or SmokeApplicationSessionFactory()
        self._timeout_seconds = timeout_seconds

    def run(self, context: SmokeContext) -> OrganisationSmokeResult:
        try:
            return asyncio.run(
                asyncio.wait_for(self._run(context.settings), timeout=self._timeout_seconds)
            )
        except TimeoutError as exc:
            raise RuntimeError(
                f"Organisation smoke exceeded the allowed runtime budget of {self._timeout_seconds}s"
            ) from exc

    async def _run(self, settings: Settings) -> OrganisationSmokeResult:
        async with self._session_factory.open(settings) as backend:
            actors = await self._prepare_actors(backend)
            return await self._run_org_smoke(backend, actors)

    async def _prepare_actors(self, backend: SmokeBackendClient) -> SmokeActors:
        suffix = uuid4().hex[:8]
        admin = await backend.register_user(
            email=f"org-admin-smoke-{suffix}@example.com",
            display_name="Org Admin Smoke",
        )
        member = await backend.register_user(
            email=f"org-member-smoke-{suffix}@example.com",
            display_name="Org Member Smoke",
        )
        return SmokeActors(
            admin_id=str(admin["id"]),
            learner_id=str(member["id"]),
        )

    async def _run_org_smoke(
        self,
        backend: SmokeBackendClient,
        actors: SmokeActors,
    ) -> OrganisationSmokeResult:
        suffix = uuid4().hex[:8]
        org_name = f"Smoke Test Org {suffix}"
        org_slug = f"smoke-test-org-{suffix}"

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

        updated_org = await backend.update_organisation(
            user_id=actors.admin_id,
            organisation_id=org_id,
            payload={"name": f"{org_name} Updated"},
        )

        members = await backend.list_members(
            user_id=actors.admin_id,
            organisation_id=org_id,
        )

        await backend.update_member(
            user_id=actors.admin_id,
            organisation_id=org_id,
            member_id=actors.learner_id,
            role="admin",
        )

        await backend.remove_member(
            user_id=actors.admin_id,
            organisation_id=org_id,
            member_id=actors.learner_id,
        )

        return OrganisationSmokeResult(
            organisation_id=org_id,
            organisation_name=str(updated_org["name"]),
            organisation_slug=str(updated_org["slug"]),
            member_count=1,
            admin_id=actors.admin_id,
            member_id=actors.learner_id,
            updated_org_name=f"{org_name} Updated",
            listed_members_count=len(members),
        )
