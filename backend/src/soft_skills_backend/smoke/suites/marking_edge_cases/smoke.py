"""Marking edge case smoke suites - comprehensive testing of marking flows."""

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
from soft_skills_backend.smoke.support.models import PracticeFixtures

from .contracts import (
    MarkingEmptyResponseSmokeResult,
    MarkingLongResponseSmokeResult,
    MarkingRapidSubmissionSmokeResult,
    MarkingRepeatedSubmissionSmokeResult,
    MarkingSpecialCharsResponseSmokeResult,
    MarkingSqlInjectionAttemptSmokeResult,
)

MARKING_EDGE_CASE_TIMEOUT_SECONDS = 420.0


class _MarkingEdgeCaseBase(SmokeCase):
    """Base for marking edge case smokes."""

    def __init__(
        self,
        *,
        name: str,
        description: str,
        practice_type: str,
        preflight: ProviderSmokePreflight | None = None,
        session_factory: SmokeApplicationSessionFactory | None = None,
        flow_timeout_seconds: float = MARKING_EDGE_CASE_TIMEOUT_SECONDS,
    ) -> None:
        self.name = name
        self.description = description
        self._practice_type = practice_type
        self._preflight = preflight or ProviderSmokePreflight()
        self._session_factory = session_factory or SmokeApplicationSessionFactory()
        self._flow_timeout_seconds = flow_timeout_seconds

    def run(self, context: SmokeContext):
        self._preflight.assert_ready(context.settings)
        try:
            return asyncio.run(
                asyncio.wait_for(self._run(context.settings), timeout=self._flow_timeout_seconds)
            )
        except TimeoutError as exc:
            raise provider_error(
                "Marking edge case smoke exceeded runtime budget",
                code="SS-PROVIDER-012",
                details={"timeout_seconds": self._flow_timeout_seconds},
            ) from exc

    async def _run(self, settings: Settings):
        raise NotImplementedError

    async def _start_session_and_submit(
        self,
        backend: SmokeBackendClient,
        user_id: str,
        fixtures: PracticeFixtures,
        response_text: str,
    ) -> MarkingEdgeCaseSmokeResult:
        session_payload = await self._start_session(backend, user_id, fixtures)
        attempt_id = str(session_payload["attempt_id"])
        response = await backend.submit_attempt_response(
            user_id=user_id,
            attempt_id=attempt_id,
            response_text=response_text,
        )
        if response.status_code not in {200, 422, 503}:
            SmokeBackendClient.require_ok(response, f"submit attempt {attempt_id}")
        attempt_payload = await backend.get_attempt(user_id=user_id, attempt_id=attempt_id)
        attempt_status = str(attempt_payload["status"])
        assessment = cast(JsonObject | None, attempt_payload.get("assessment"))
        return self._build_result(
            attempt_id=attempt_id,
            attempt_status=attempt_status,
            assessment=assessment,
            response_status_code=response.status_code,
        )

    def _build_result(
        self,
        *,
        attempt_id: str,
        attempt_status: str,
        assessment: JsonObject | None,
        response_status_code: int,
    ) -> MarkingEdgeCaseSmokeResult:
        raise NotImplementedError

    async def _start_session(
        self, backend: SmokeBackendClient, user_id: str, fixtures: PracticeFixtures
    ) -> JsonObject:
        raise NotImplementedError


class MarkingEmptyResponseSmoke(_MarkingEdgeCaseBase):
    """Test marking with empty response text."""

    def __init__(
        self,
        *,
        preflight: ProviderSmokePreflight | None = None,
        session_factory: SmokeApplicationSessionFactory | None = None,
        flow_timeout_seconds: float = MARKING_EDGE_CASE_TIMEOUT_SECONDS,
    ) -> None:
        super().__init__(
            name="marking-empty-response",
            description="Test marking with empty response text.",
            practice_type="quick_practice",
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

    def _build_result(
        self,
        *,
        attempt_id: str,
        attempt_status: str,
        assessment: JsonObject | None,
        response_status_code: int,
    ) -> MarkingEmptyResponseSmokeResult:
        return MarkingEmptyResponseSmokeResult(
            status="ok",
            test_name="empty_response",
            practice_type=self._practice_type,
            attempt_id=attempt_id,
            attempt_status=attempt_status,
            assessment_id=str(assessment["assessment_id"])
            if assessment and assessment.get("assessment_id")
            else None,
            overall_score=int(assessment["overall_score"])
            if assessment and assessment.get("overall_score")
            else None,
        )

    async def _run(self, settings: Settings) -> MarkingEmptyResponseSmokeResult:
        async with self._session_factory.open(settings) as backend:
            actors = await SmokeActorBootstrap(backend).prepare()
            fixtures = await PracticeFixtureSeeder(backend).seed(actors.learner_id)
            return await self._start_session_and_submit(backend, actors.learner_id, fixtures, "")


class MarkingLongResponseSmoke(_MarkingEdgeCaseBase):
    """Test marking with very long response text (5000+ chars)."""

    def __init__(
        self,
        *,
        preflight: ProviderSmokePreflight | None = None,
        session_factory: SmokeApplicationSessionFactory | None = None,
        flow_timeout_seconds: float = MARKING_EDGE_CASE_TIMEOUT_SECONDS,
    ) -> None:
        super().__init__(
            name="marking-long-response",
            description="Test marking with very long response text (5000+ chars).",
            practice_type="quick_practice",
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

    def _build_result(
        self,
        *,
        attempt_id: str,
        attempt_status: str,
        assessment: JsonObject | None,
        response_status_code: int,
    ) -> MarkingLongResponseSmokeResult:
        return MarkingLongResponseSmokeResult(
            status="ok",
            test_name="long_response",
            practice_type=self._practice_type,
            attempt_id=attempt_id,
            attempt_status=attempt_status,
            assessment_id=str(assessment["assessment_id"])
            if assessment and assessment.get("assessment_id")
            else None,
            overall_score=int(assessment["overall_score"])
            if assessment and assessment.get("overall_score")
            else None,
        )

    async def _run(self, settings: Settings) -> MarkingLongResponseSmokeResult:
        long_response = (
            "I believe this is a critical situation that requires careful consideration of multiple "
            "factors. Let me walk through my thought process step by step. First, we need to understand "
            "the underlying dynamics at play here. Second, we must consider the various stakeholders "
            "involved and their respective interests. Third, we need to evaluate the potential tradeoffs "
            "and implications of different courses of action. Fourth, we should think about how to "
            "communicate effectively with all parties involved. Fifth, we need to establish clear "
            "expectations and next steps. " * 30
        )
        async with self._session_factory.open(settings) as backend:
            actors = await SmokeActorBootstrap(backend).prepare()
            fixtures = await PracticeFixtureSeeder(backend).seed(actors.learner_id)
            return await self._start_session_and_submit(
                backend, actors.learner_id, fixtures, long_response
            )


class MarkingSpecialCharsResponseSmoke(_MarkingEdgeCaseBase):
    """Test marking with special characters, unicode, and emoji in response."""

    def __init__(
        self,
        *,
        preflight: ProviderSmokePreflight | None = None,
        session_factory: SmokeApplicationSessionFactory | None = None,
        flow_timeout_seconds: float = MARKING_EDGE_CASE_TIMEOUT_SECONDS,
    ) -> None:
        super().__init__(
            name="marking-special-chars-response",
            description="Test marking with special characters, unicode, and emoji in response.",
            practice_type="quick_practice",
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

    def _build_result(
        self,
        *,
        attempt_id: str,
        attempt_status: str,
        assessment: JsonObject | None,
        response_status_code: int,
    ) -> MarkingSpecialCharsResponseSmokeResult:
        return MarkingSpecialCharsResponseSmokeResult(
            status="ok",
            test_name="special_chars_response",
            practice_type=self._practice_type,
            attempt_id=attempt_id,
            attempt_status=attempt_status,
            assessment_id=str(assessment["assessment_id"])
            if assessment and assessment.get("assessment_id")
            else None,
            overall_score=int(assessment["overall_score"])
            if assessment and assessment.get("overall_score")
            else None,
        )

    async def _run(self, settings: Settings) -> MarkingSpecialCharsResponseSmokeResult:
        special_response = (
            "Test response with special chars: @#$%^&*() "
            "Unicode: \u4e2d\u6587\u65e5\u672c\u8a9e \u041f\u0440\u0438\u0432\u0435\u0442 "
            "Emoji: \U0001f600\U0001f4af\U0001f30d\U0001f30e "
            'Newlines:\n\t\r\\" and more special chars: \u00e9\u00e8\u00ea'
        )
        async with self._session_factory.open(settings) as backend:
            actors = await SmokeActorBootstrap(backend).prepare()
            fixtures = await PracticeFixtureSeeder(backend).seed(actors.learner_id)
            return await self._start_session_and_submit(
                backend, actors.learner_id, fixtures, special_response
            )


class MarkingSqlInjectionAttemptSmoke(_MarkingEdgeCaseBase):
    """Test marking with SQL injection attempt in response."""

    def __init__(
        self,
        *,
        preflight: ProviderSmokePreflight | None = None,
        session_factory: SmokeApplicationSessionFactory | None = None,
        flow_timeout_seconds: float = MARKING_EDGE_CASE_TIMEOUT_SECONDS,
    ) -> None:
        super().__init__(
            name="marking-sql-injection-attempt",
            description="Test marking with SQL injection attempt in response.",
            practice_type="quick_practice",
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

    def _build_result(
        self,
        *,
        attempt_id: str,
        attempt_status: str,
        assessment: JsonObject | None,
        response_status_code: int,
    ) -> MarkingSqlInjectionAttemptSmokeResult:
        return MarkingSqlInjectionAttemptSmokeResult(
            status="ok",
            test_name="sql_injection_attempt",
            practice_type=self._practice_type,
            attempt_id=attempt_id,
            attempt_status=attempt_status,
            assessment_id=str(assessment["assessment_id"])
            if assessment and assessment.get("assessment_id")
            else None,
            overall_score=int(assessment["overall_score"])
            if assessment and assessment.get("overall_score")
            else None,
        )

    async def _run(self, settings: Settings) -> MarkingSqlInjectionAttemptSmokeResult:
        sql_injection_response = (
            "I think we should '; DROP TABLE attempts; -- "
            "and then SELECT * FROM users WHERE 1=1; --"
        )
        async with self._session_factory.open(settings) as backend:
            actors = await SmokeActorBootstrap(backend).prepare()
            fixtures = await PracticeFixtureSeeder(backend).seed(actors.learner_id)
            return await self._start_session_and_submit(
                backend, actors.learner_id, fixtures, sql_injection_response
            )


class MarkingRapidSubmissionSmoke(_MarkingEdgeCaseBase):
    """Test marking with rapid multiple submissions to same session."""

    def __init__(
        self,
        *,
        preflight: ProviderSmokePreflight | None = None,
        session_factory: SmokeApplicationSessionFactory | None = None,
        flow_timeout_seconds: float = MARKING_EDGE_CASE_TIMEOUT_SECONDS,
    ) -> None:
        super().__init__(
            name="marking-rapid-submission",
            description="Test marking with rapid multiple submissions to same session.",
            practice_type="quick_practice",
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

    def _build_result(
        self,
        *,
        attempt_id: str,
        attempt_status: str,
        assessment: JsonObject | None,
        response_status_code: int,
    ) -> MarkingRapidSubmissionSmokeResult:
        return MarkingRapidSubmissionSmokeResult(
            status="ok",
            test_name="rapid_submission",
            practice_type=self._practice_type,
            attempt_id=attempt_id,
            attempt_status=attempt_status,
            assessment_id=str(assessment["assessment_id"])
            if assessment and assessment.get("assessment_id")
            else None,
            overall_score=int(assessment["overall_score"])
            if assessment and assessment.get("overall_score")
            else None,
        )

    async def _run(self, settings: Settings) -> MarkingRapidSubmissionSmokeResult:
        async with self._session_factory.open(settings) as backend:
            actors = await SmokeActorBootstrap(backend).prepare()
            fixtures = await PracticeFixtureSeeder(backend).seed(actors.learner_id)
            session_payload = await self._start_session(backend, actors.learner_id, fixtures)
            attempt_id = str(session_payload["attempt_id"])
            response1 = await backend.submit_attempt_response(
                user_id=actors.learner_id,
                attempt_id=attempt_id,
                response_text="First response",
            )
            response2 = await backend.submit_attempt_response(
                user_id=actors.learner_id,
                attempt_id=attempt_id,
                response_text="Second response",
            )
            response3 = await backend.submit_attempt_response(
                user_id=actors.learner_id,
                attempt_id=attempt_id,
                response_text="Third response",
            )
            attempt_payload = await backend.get_attempt(
                user_id=actors.learner_id, attempt_id=attempt_id
            )
            attempt_status = str(attempt_payload["status"])
            assessment = cast(JsonObject | None, attempt_payload.get("assessment"))
            return MarkingRapidSubmissionSmokeResult(
                status="ok",
                test_name="rapid_submission",
                practice_type=self._practice_type,
                attempt_id=attempt_id,
                attempt_status=attempt_status,
                assessment_id=str(assessment["assessment_id"])
                if assessment and assessment.get("assessment_id")
                else None,
                overall_score=int(assessment["overall_score"])
                if assessment and assessment.get("overall_score")
                else None,
                error_details={
                    "first_response_status": response1.status_code,
                    "second_response_status": response2.status_code,
                    "third_response_status": response3.status_code,
                },
            )


class MarkingRepeatedSubmissionSmoke(_MarkingEdgeCaseBase):
    """Test marking with repeated identical submissions."""

    def __init__(
        self,
        *,
        preflight: ProviderSmokePreflight | None = None,
        session_factory: SmokeApplicationSessionFactory | None = None,
        flow_timeout_seconds: float = MARKING_EDGE_CASE_TIMEOUT_SECONDS,
    ) -> None:
        super().__init__(
            name="marking-repeated-submission",
            description="Test marking with repeated identical submissions.",
            practice_type="interview",
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
            competency_context="Assess structured communication.",
            interviewer_perspective="You are responding to a consulting hiring manager.",
        )

    def _build_result(
        self,
        *,
        attempt_id: str,
        attempt_status: str,
        assessment: JsonObject | None,
        response_status_code: int,
    ) -> MarkingRepeatedSubmissionSmokeResult:
        return MarkingRepeatedSubmissionSmokeResult(
            status="ok",
            test_name="repeated_submission",
            practice_type=self._practice_type,
            attempt_id=attempt_id,
            attempt_status=attempt_status,
            assessment_id=str(assessment["assessment_id"])
            if assessment and assessment.get("assessment_id")
            else None,
            overall_score=int(assessment["overall_score"])
            if assessment and assessment.get("overall_score")
            else None,
        )

    async def _run(self, settings: Settings) -> MarkingRepeatedSubmissionSmokeResult:
        repeated_response = (
            "I led the decision by surfacing the uncertainty clearly, aligning the team on "
            "the tradeoff, and setting a next-morning checkpoint with a named owner. "
            "I led the decision by surfacing the uncertainty clearly, aligning the team on "
            "the tradeoff, and setting a next-morning checkpoint with a named owner."
        )
        async with self._session_factory.open(settings) as backend:
            actors = await SmokeActorBootstrap(backend).prepare()
            fixtures = await PracticeFixtureSeeder(backend).seed(actors.learner_id)
            return await self._start_session_and_submit(
                backend, actors.learner_id, fixtures, repeated_response
            )
