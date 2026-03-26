"""Practice-session flow smoke suite."""

from __future__ import annotations

import asyncio
from typing import cast

from soft_skills_backend.config import Settings
from soft_skills_backend.modules.practice.domain.practice import AttemptStatus
from soft_skills_backend.shared.errors import provider_error
from soft_skills_backend.smoke.contracts import SmokeCase, SmokeContext
from soft_skills_backend.smoke.support.actors import SmokeActorBootstrap
from soft_skills_backend.smoke.support.backend import JsonObject, SmokeBackendClient
from soft_skills_backend.smoke.support.environment import (
    ProviderSmokePreflight,
    SmokeApplicationSessionFactory,
)
from soft_skills_backend.smoke.support.fixtures import PracticeFixtureSeeder

from .contracts import PracticeSessionAttemptSmokeResult, PracticeSessionFlowSmokeResult

SMOKE_FLOW_TIMEOUT_SECONDS = 420.0


class PracticeSessionFlowSmoke(SmokeCase):
    """Exercise the standalone session-start and submit flows."""

    name = "practice-session-flow"
    description = "Exercise quick-practice, interview, and scenario session flows end to end."

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

    def run(self, context: SmokeContext) -> PracticeSessionFlowSmokeResult:
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

    async def _run(self, settings: Settings) -> PracticeSessionFlowSmokeResult:
        async with self._session_factory.open(settings) as backend:
            actors = await SmokeActorBootstrap(backend).prepare()
            fixtures = await PracticeFixtureSeeder(backend).seed(actors.learner_id)
            results = [
                await self._run_quick_practice(backend, actors.learner_id, fixtures.quick_prompt_id),
                await self._run_interview(backend, actors.learner_id, fixtures.interview_prompt_id),
                await self._run_scenario(backend, actors.learner_id, fixtures.scenario_id),
            ]
            return PracticeSessionFlowSmokeResult(status="ok", results=results)

    async def _run_quick_practice(
        self, backend: SmokeBackendClient, user_id: str, prompt_item_id: str
    ) -> PracticeSessionAttemptSmokeResult:
        session = await backend.start_quick_practice_session(user_id=user_id, prompt_item_id=prompt_item_id)
        return await self._submit_and_assert(
            backend=backend,
            user_id=user_id,
            session_payload=session,
            practice_type="quick_practice",
            response_text=(
                "I hear why the date matters to you. The earliest realistic date is next Friday, "
                "and I can confirm any scope tradeoffs with the team by tomorrow afternoon."
            ),
        )

    async def _run_interview(
        self, backend: SmokeBackendClient, user_id: str, prompt_item_id: str
    ) -> PracticeSessionAttemptSmokeResult:
        session = await backend.start_interview_session(
            user_id=user_id,
            prompt_item_id=prompt_item_id,
            competency_context="Assess structured communication, tradeoff handling, and ownership.",
            interviewer_perspective="You are responding to a consulting hiring manager.",
        )
        return await self._submit_and_assert(
            backend=backend,
            user_id=user_id,
            session_payload=session,
            practice_type="interview",
            response_text=(
                "I led the decision by surfacing the uncertainty clearly, aligning the team on "
                "the tradeoff, and setting a next-morning checkpoint with a named owner."
            ),
        )

    async def _run_scenario(
        self, backend: SmokeBackendClient, user_id: str, scenario_id: str
    ) -> PracticeSessionAttemptSmokeResult:
        session = await backend.start_scenario_session(
            user_id=user_id,
            scenario_id=scenario_id,
            artifacts=[
                {
                    "artifact_type": "email",
                    "title": "Board escalation note",
                    "body": "The board expects a recommendation before 9am tomorrow.",
                }
            ],
        )
        return await self._submit_and_assert(
            backend=backend,
            user_id=user_id,
            session_payload=session,
            practice_type="scenario",
            response_text=(
                "I would recommend a one-day delay, explain the legal risk directly, and "
                "propose a 7am checkpoint with sales and legal before the board meeting."
            ),
        )

    async def _submit_and_assert(
        self,
        *,
        backend: SmokeBackendClient,
        user_id: str,
        session_payload: JsonObject,
        practice_type: str,
        response_text: str,
    ) -> PracticeSessionAttemptSmokeResult:
        session_id = str(session_payload["session_id"])
        attempt_id = str(session_payload["attempt_id"])
        response = await backend.submit_attempt_response(
            user_id=user_id,
            attempt_id=attempt_id,
            response_text=response_text,
        )
        if response.status_code not in {200, 422, 503}:
            SmokeBackendClient.require_ok(response, f"submit {practice_type} attempt {attempt_id}")
        complete_attempt = await backend.get_attempt(user_id=user_id, attempt_id=attempt_id)
        attempt_status = str(complete_attempt["status"])
        if attempt_status not in {
            AttemptStatus.ASSESSED.value,
            AttemptStatus.ASSESSMENT_REJECTED.value,
            AttemptStatus.ASSESSMENT_FAILED.value,
        }:
            raise provider_error(
                "Smoke practice session did not reach a terminal attempt state",
                code="SS-PROVIDER-020",
                details={"practice_type": practice_type, "attempt_id": attempt_id, "status": attempt_status},
            )
        assessment = cast(JsonObject | None, complete_attempt["assessment"])
        return PracticeSessionAttemptSmokeResult(
            practice_type=practice_type,
            session_id=session_id,
            attempt_id=attempt_id,
            attempt_status=attempt_status,
            assessment_id=None if assessment is None else str(assessment["assessment_id"]),
        )
