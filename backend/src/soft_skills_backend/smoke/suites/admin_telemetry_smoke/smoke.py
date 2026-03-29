"""Admin telemetry smoke suite."""

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

from .contracts import AdminTelemetrySmokeResult

SMOKE_TIMEOUT_SECONDS = 120.0


class AdminTelemetrySmoke(SmokeCase):
    """Verifies admin telemetry endpoints end to end without LLM keys."""

    name = "admin-telemetry"
    description = (
        "Assert telemetry overview, telemetry traces list, and telemetry trace detail APIs."
    )

    def __init__(
        self,
        *,
        session_factory: SmokeApplicationSessionFactory | None = None,
        timeout_seconds: float = SMOKE_TIMEOUT_SECONDS,
    ) -> None:
        self._session_factory = session_factory or SmokeApplicationSessionFactory()
        self._timeout_seconds = timeout_seconds

    def run(self, context: SmokeContext) -> AdminTelemetrySmokeResult:
        try:
            return asyncio.run(
                asyncio.wait_for(self._run(context.settings), timeout=self._timeout_seconds)
            )
        except TimeoutError as exc:
            raise RuntimeError(
                f"Admin telemetry smoke exceeded the allowed runtime budget of {self._timeout_seconds}s"
            ) from exc

    async def _run(self, settings: Settings) -> AdminTelemetrySmokeResult:
        async with self._session_factory.open(settings) as backend:
            actors = await self._prepare_actors(backend)
            return await self._run_telemetry_smoke(backend, actors)

    async def _prepare_actors(self, backend: SmokeBackendClient) -> SmokeActors:
        suffix = uuid4().hex[:8]
        admin = await backend.register_user(
            email=f"admin-telemetry-{suffix}@example.com",
            display_name="Admin Telemetry Smoke",
        )
        member = await backend.register_user(
            email=f"member-telemetry-{suffix}@example.com",
            display_name="Member Telemetry Smoke",
        )
        return SmokeActors(
            admin_id=str(admin["id"]),
            learner_id=str(member["id"]),
        )

    async def _run_telemetry_smoke(
        self,
        backend: SmokeBackendClient,
        actors: SmokeActors,
    ) -> AdminTelemetrySmokeResult:
        suffix = uuid4().hex[:8]
        org_name = f"Telemetry Smoke Org {suffix}"
        org_slug = f"telemetry-smoke-org-{suffix}"

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

        overview_result = await backend.admin_get_telemetry_overview(
            user_id=actors.admin_id,
            organisation_id=org_id,
        )
        overview_status = str(overview_result.get("total_provider_calls", "unknown"))

        traces_result = await backend.admin_list_telemetry_traces(
            user_id=actors.admin_id,
            organisation_id=org_id,
        )
        traces_list = traces_result.get("traces", [])
        traces_count = len(traces_list) if traces_list else 0

        trace_id = traces_list[0].get("id") if traces_list else None
        trace_detail_status = "not_found"
        if trace_id:
            trace_detail_result = await backend.admin_get_telemetry_trace(
                user_id=actors.admin_id,
                organisation_id=org_id,
                trace_id=str(trace_id),
            )
            trace_detail_status = str(trace_detail_result.get("trace_id", "unknown"))

        return AdminTelemetrySmokeResult(
            organisation_id=org_id,
            admin_user_id=actors.admin_id,
            member_user_id=actors.learner_id,
            overview_status=overview_status,
            traces_count=traces_count,
            trace_detail_status=trace_detail_status,
        )
