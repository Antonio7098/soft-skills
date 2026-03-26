"""Practice-run lifecycle smoke suite."""

from __future__ import annotations

import asyncio

from soft_skills_backend.config import Settings
from soft_skills_backend.shared.errors import provider_error
from soft_skills_backend.smoke.contracts import SmokeCase, SmokeContext
from soft_skills_backend.smoke.support.actors import SmokeActorBootstrap
from soft_skills_backend.smoke.support.environment import (
    ProviderSmokePreflight,
    SmokeApplicationSessionFactory,
)
from soft_skills_backend.smoke.support.fixtures import PracticeFixtureSeeder
from soft_skills_backend.smoke.support.practice_run_flow import PracticeRunSmokeFlow

from .contracts import PracticeRunLifecycleSmokeResult

SMOKE_FLOW_TIMEOUT_SECONDS = 420.0


class PracticeRunLifecycleSmoke(SmokeCase):
    """Verifies aggregate practice-run lifecycle behavior end to end."""

    name = "practice-run-lifecycle"
    description = "Assert aggregate practice-run start, progress refresh, completion, and history."

    def __init__(
        self,
        *,
        preflight: ProviderSmokePreflight | None = None,
        session_factory: SmokeApplicationSessionFactory | None = None,
        flow_timeout_seconds: float = SMOKE_FLOW_TIMEOUT_SECONDS,
    ) -> None:
        self._preflight = preflight or ProviderSmokePreflight()
        self._session_factory = session_factory or SmokeApplicationSessionFactory()
        self._flow_timeout_seconds = flow_timeout_seconds

    def run(self, context: SmokeContext) -> PracticeRunLifecycleSmokeResult:
        self._preflight.assert_ready(context.settings)
        try:
            return asyncio.run(
                asyncio.wait_for(self._run(context.settings), timeout=self._flow_timeout_seconds)
            )
        except TimeoutError as exc:
            raise provider_error(
                "Smoke flow exceeded the allowed runtime budget",
                code="SS-PROVIDER-012",
                details={"timeout_seconds": self._flow_timeout_seconds},
            ) from exc

    async def _run(self, settings: Settings) -> PracticeRunLifecycleSmokeResult:
        async with self._session_factory.open(settings) as backend:
            actors = await SmokeActorBootstrap(backend).prepare()
            fixtures = await PracticeFixtureSeeder(backend).seed(actors.learner_id)
            return await PracticeRunSmokeFlow(backend).run_lifecycle_smoke(
                actors.learner_id,
                fixtures,
            )
