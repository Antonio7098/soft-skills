"""Admin analytics smoke suite."""

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

from .contracts import AdminAnalyticsSmokeResult

SMOKE_TIMEOUT_SECONDS = 120.0


class AdminAnalyticsSmoke(SmokeCase):
    """Verifies admin analytics endpoints end to end without LLM keys."""

    name = "admin-analytics"
    description = (
        "Assert analytics overview, cohort analytics, cohort comparison, and analytics export APIs."
    )

    def __init__(
        self,
        *,
        session_factory: SmokeApplicationSessionFactory | None = None,
        timeout_seconds: float = SMOKE_TIMEOUT_SECONDS,
    ) -> None:
        self._session_factory = session_factory or SmokeApplicationSessionFactory()
        self._timeout_seconds = timeout_seconds

    def run(self, context: SmokeContext) -> AdminAnalyticsSmokeResult:
        try:
            return asyncio.run(
                asyncio.wait_for(self._run(context.settings), timeout=self._timeout_seconds)
            )
        except TimeoutError as exc:
            raise RuntimeError(
                f"Admin analytics smoke exceeded the allowed runtime budget of {self._timeout_seconds}s"
            ) from exc

    async def _run(self, settings: Settings) -> AdminAnalyticsSmokeResult:
        async with self._session_factory.open(settings) as backend:
            actors = await self._prepare_actors(backend)
            return await self._run_analytics_smoke(backend, actors)

    async def _prepare_actors(self, backend: SmokeBackendClient) -> SmokeActors:
        suffix = uuid4().hex[:8]
        admin = await backend.register_user(
            email=f"admin-analytics-{suffix}@example.com",
            display_name="Admin Analytics Smoke",
        )
        member = await backend.register_user(
            email=f"member-analytics-{suffix}@example.com",
            display_name="Member Analytics Smoke",
        )
        return SmokeActors(
            admin_id=str(admin["id"]),
            learner_id=str(member["id"]),
        )

    async def _run_analytics_smoke(
        self,
        backend: SmokeBackendClient,
        actors: SmokeActors,
    ) -> AdminAnalyticsSmokeResult:
        suffix = uuid4().hex[:8]
        org_name = f"Analytics Smoke Org {suffix}"
        org_slug = f"analytics-smoke-org-{suffix}"

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

        await backend.admin_get_learner_analytics(
            user_id=actors.admin_id,
            organisation_id=org_id,
            learner_id=actors.learner_id,
        )

        await backend.admin_get_cohort_analytics(
            user_id=actors.admin_id,
            organisation_id=org_id,
        )

        overview_result = await backend.admin_get_analytics_overview(
            user_id=actors.admin_id,
            organisation_id=org_id,
        )
        overview_total_learners = int(overview_result.get("total_learners", 0) or 0)

        comparison_result = await backend.admin_get_cohort_comparison(
            user_id=actors.admin_id,
            organisation_id=org_id,
            cohort_keys="Consultant,Engineer",
        )
        cohorts_list = comparison_result.get("cohorts")
        comparison_cohorts_count = len(cohorts_list) if cohorts_list else 0

        export_json_result = await backend.admin_export_analytics(
            user_id=actors.admin_id,
            organisation_id=org_id,
            format="json",
        )
        export_json_status = str(export_json_result.get("status", "unknown"))

        export_csv_result = await backend.admin_export_analytics(
            user_id=actors.admin_id,
            organisation_id=org_id,
            format="csv",
        )
        export_csv_status = str(export_csv_result.get("status", "unknown"))

        return AdminAnalyticsSmokeResult(
            organisation_id=org_id,
            admin_user_id=actors.admin_id,
            member_user_id=actors.learner_id,
            overview_total_learners=overview_total_learners,
            comparison_cohorts_count=comparison_cohorts_count,
            export_json_status=export_json_status,
            export_csv_status=export_csv_status,
        )
