"""Actor bootstrap helpers for smoke suites."""

from __future__ import annotations

from uuid import uuid4

from .backend import SmokeBackendClient
from .models import SmokeActors


class SmokeActorBootstrap:
    """Registers smoke actors and bootstraps canon data."""

    def __init__(self, backend: SmokeBackendClient) -> None:
        self._backend = backend

    async def prepare(self) -> SmokeActors:
        suffix = uuid4().hex[:8]
        admin = await self._backend.register_user(
            email=f"admin-smoke-{suffix}@example.com",
            display_name="Smoke Admin",
            role="admin",
        )
        await self._backend.bootstrap_canon(str(admin["id"]))

        learner = await self._backend.register_user(
            email=f"learner-smoke-{suffix}@example.com",
            display_name="Smoke Learner",
        )
        return SmokeActors(
            admin_id=str(admin["id"]),
            learner_id=str(learner["id"]),
        )
