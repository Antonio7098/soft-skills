"""Assessment-marking smoke suites."""

from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from typing import SupportsInt, cast

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
from soft_skills_backend.smoke.support.models import PracticeFixtures

from .contracts import AssessmentMarkingSmokeResult

SMOKE_FLOW_TIMEOUT_SECONDS = 420.0


class _AssessmentMarkingSmoke(SmokeCase, ABC):
    """Base suite for a single practice-type marking flow."""

    def __init__(
        self,
        *,
        name: str,
        description: str,
        preflight: ProviderSmokePreflight | None = None,
        session_factory: SmokeApplicationSessionFactory | None = None,
        flow_timeout_seconds: float = SMOKE_FLOW_TIMEOUT_SECONDS,
    ) -> None:
        self.name = name
        self.description = description
        self._preflight = preflight or ProviderSmokePreflight()
        self._session_factory = session_factory or SmokeApplicationSessionFactory()
        self._flow_timeout_seconds = flow_timeout_seconds

    def run(self, context: SmokeContext) -> AssessmentMarkingSmokeResult:
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

    async def _run(self, settings: Settings) -> AssessmentMarkingSmokeResult:
        async with self._session_factory.open(settings) as backend:
            actors = await SmokeActorBootstrap(backend).prepare()
            fixtures = await PracticeFixtureSeeder(backend).seed(actors.learner_id)
            session_payload = await self._start_session(backend, actors.learner_id, fixtures)
            attempt_id = str(session_payload["attempt_id"])
            response = await backend.submit_attempt_response(
                user_id=actors.learner_id,
                attempt_id=attempt_id,
                response_text=self._response_text(),
            )
            if response.status_code not in {200, 422, 503}:
                SmokeBackendClient.require_ok(response, f"submit attempt {attempt_id}")

            attempt_payload = await backend.get_attempt(user_id=actors.learner_id, attempt_id=attempt_id)
            attempt_status = str(attempt_payload["status"])
            if attempt_status not in {
                AttemptStatus.ASSESSED.value,
                AttemptStatus.ASSESSMENT_REJECTED.value,
                AttemptStatus.ASSESSMENT_FAILED.value,
            }:
                raise provider_error(
                    "Smoke assessment did not reach a terminal attempt state",
                    code="SS-PROVIDER-019",
                    details={"attempt_id": attempt_id, "attempt_status": attempt_status},
                )

            assessment = cast(JsonObject | None, attempt_payload["assessment"])
            error_code = None
            if response.status_code != 200:
                error_payload = cast(dict[str, object], response.json()["error"])
                error_code = str(error_payload["code"])

            if assessment is None:
                return AssessmentMarkingSmokeResult(
                    status="ok",
                    practice_type=self.practice_type,
                    attempt_id=attempt_id,
                    attempt_status=attempt_status,
                    error_code=error_code,
                )

            return AssessmentMarkingSmokeResult(
                status="ok",
                practice_type=self.practice_type,
                attempt_id=attempt_id,
                attempt_status=attempt_status,
                provider=str(assessment["provider"]),
                model_slug=str(assessment["model_slug"]),
                assessment_id=str(assessment["assessment_id"]),
                overall_score=int(cast(str | SupportsInt, assessment["overall_score"])),
                error_code=error_code,
            )

    @property
    @abstractmethod
    def practice_type(self) -> str:
        """Practice type under test."""

    @abstractmethod
    async def _start_session(
        self,
        backend: SmokeBackendClient,
        user_id: str,
        fixtures: PracticeFixtures,
    ) -> JsonObject:
        """Start the concrete practice session."""

    @abstractmethod
    def _response_text(self) -> str:
        """Learner response submitted for marking."""


class QuickPracticeMarkingSmoke(_AssessmentMarkingSmoke):
    practice_type = "quick_practice"

    def __init__(
        self,
        *,
        preflight: ProviderSmokePreflight | None = None,
        session_factory: SmokeApplicationSessionFactory | None = None,
        flow_timeout_seconds: float = SMOKE_FLOW_TIMEOUT_SECONDS,
    ) -> None:
        super().__init__(
            name="marking-quick-practice",
            description="Run the quick-practice marking flow end to end.",
            preflight=preflight,
            session_factory=session_factory,
            flow_timeout_seconds=flow_timeout_seconds,
        )

    async def _start_session(
        self, backend: SmokeBackendClient, user_id: str, fixtures: PracticeFixtures
    ) -> JsonObject:
        return await backend.start_quick_practice_session(
            user_id=user_id,
            prompt_item_id=fixtures.quick_prompt_id,
        )

    def _response_text(self) -> str:
        return (
            "I hear why the date matters to you. The earliest realistic date is next Friday, "
            "and I can confirm any scope tradeoffs with the team by tomorrow afternoon."
        )


class InterviewMarkingSmoke(_AssessmentMarkingSmoke):
    practice_type = "interview"

    def __init__(
        self,
        *,
        preflight: ProviderSmokePreflight | None = None,
        session_factory: SmokeApplicationSessionFactory | None = None,
        flow_timeout_seconds: float = SMOKE_FLOW_TIMEOUT_SECONDS,
    ) -> None:
        super().__init__(
            name="marking-interview",
            description="Run the interview marking flow end to end.",
            preflight=preflight,
            session_factory=session_factory,
            flow_timeout_seconds=flow_timeout_seconds,
        )

    async def _start_session(
        self, backend: SmokeBackendClient, user_id: str, fixtures: PracticeFixtures
    ) -> JsonObject:
        return await backend.start_interview_session(
            user_id=user_id,
            prompt_item_id=fixtures.interview_prompt_id,
            competency_context="Assess structured communication, tradeoff handling, and ownership.",
            interviewer_perspective="You are responding to a consulting hiring manager.",
        )

    def _response_text(self) -> str:
        return (
            "I led the decision by surfacing the uncertainty clearly, aligning the team on "
            "the tradeoff, and setting a next-morning checkpoint with a named owner."
        )


class ScenarioMarkingSmoke(_AssessmentMarkingSmoke):
    practice_type = "scenario"

    def __init__(
        self,
        *,
        preflight: ProviderSmokePreflight | None = None,
        session_factory: SmokeApplicationSessionFactory | None = None,
        flow_timeout_seconds: float = SMOKE_FLOW_TIMEOUT_SECONDS,
    ) -> None:
        super().__init__(
            name="marking-scenario",
            description="Run the scenario marking flow end to end.",
            preflight=preflight,
            session_factory=session_factory,
            flow_timeout_seconds=flow_timeout_seconds,
        )

    async def _start_session(
        self, backend: SmokeBackendClient, user_id: str, fixtures: PracticeFixtures
    ) -> JsonObject:
        return await backend.start_scenario_session(
            user_id=user_id,
            scenario_id=fixtures.scenario_id,
            artifacts=[
                {
                    "artifact_type": "email",
                    "title": "Board escalation note",
                    "body": "The board expects a recommendation before 9am tomorrow.",
                }
            ],
        )

    def _response_text(self) -> str:
        return (
            "I would recommend a one-day delay, explain the legal risk directly, and "
            "propose a 7am checkpoint with sales and legal before the board meeting."
        )
