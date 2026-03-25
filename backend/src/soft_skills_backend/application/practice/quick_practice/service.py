"""Practice runtime orchestration service."""

from __future__ import annotations

from typing import Any, cast
from uuid import uuid4

from stageflow.api import Pipeline, StageKind, stage

from soft_skills_backend.application._shared.stageflow import (
    StageflowPipelineSupport,
    StageflowStageResult,
    ok_output,
    payload_from_inputs,
    payload_from_results,
    run_logged_pipeline,
)
from soft_skills_backend.application.assessment.models import (
    AssessmentTransformPayload,
    InterviewContextView,
    LearnerContextPayload,
    PracticeArtifactView,
    ResolvedAttemptPayload,
)
from soft_skills_backend.application.assessment.quick_practice_marking import (
    QuickPracticeMarkingProvider,
    StructuredOutputRejectionError,
)
from soft_skills_backend.application.auth import Actor
from soft_skills_backend.application.practice.models import (
    AttemptGuardPayload,
    AttemptView,
    PracticeCorrelation,
    PromptContextPayload,
    QuickPracticeSessionView,
    SessionTransformPayload,
    StartInputPayload,
    StartInterviewSessionCommand,
    StartQuickPracticeSessionCommand,
    StartScenarioSessionCommand,
    SubmitAttemptCommand,
    ValidatedAssessmentPayload,
)
from soft_skills_backend.domain.errors import AppError, auth_error
from soft_skills_backend.domain.practice import PracticeType
from soft_skills_backend.orchestration.stageflow_runtime import StageflowRuntime

from .assessment_service import QuickPracticeAssessmentService
from .repository import QuickPracticeRepository


class QuickPracticeService:
    """Own the shared text-practice runtime workflow."""

    def __init__(
        self,
        *,
        stageflow_runtime: StageflowRuntime,
        store: QuickPracticeRepository,
        assessment_marker: QuickPracticeMarkingProvider,
    ) -> None:
        self._store = store
        self._assessment_marker = assessment_marker
        self._stageflow = StageflowPipelineSupport.from_runtime(stageflow_runtime)
        self._assessment = QuickPracticeAssessmentService(
            store=store,
            assessment_marker=assessment_marker,
        )

    async def start_session(
        self,
        actor: Actor,
        correlation: PracticeCorrelation,
        command: StartQuickPracticeSessionCommand,
    ) -> QuickPracticeSessionView:
        return await self._start_practice_session(
            actor=actor,
            correlation=correlation,
            start_input=StartInputPayload(
                practice_type=PracticeType.QUICK_PRACTICE,
                content_item_id=command.prompt_item_id,
            ),
        )

    async def start_interview_session(
        self,
        actor: Actor,
        correlation: PracticeCorrelation,
        command: StartInterviewSessionCommand,
    ) -> QuickPracticeSessionView:
        return await self._start_practice_session(
            actor=actor,
            correlation=correlation,
            start_input=StartInputPayload(
                practice_type=PracticeType.INTERVIEW,
                content_item_id=command.prompt_item_id,
                interview_context=InterviewContextView(
                    competency_context=command.competency_context,
                    interviewer_perspective=command.interviewer_perspective,
                ),
            ),
        )

    async def start_scenario_session(
        self,
        actor: Actor,
        correlation: PracticeCorrelation,
        command: StartScenarioSessionCommand,
    ) -> QuickPracticeSessionView:
        artifacts = [
            PracticeArtifactView(
                artifact_id=f"{command.scenario_id}-artifact-{index}",
                artifact_type=artifact.artifact_type,
                title=artifact.title,
                body=artifact.body,
            )
            for index, artifact in enumerate(command.artifacts, start=1)
        ]
        return await self._start_practice_session(
            actor=actor,
            correlation=correlation,
            start_input=StartInputPayload(
                practice_type=PracticeType.SCENARIO,
                content_item_id=command.scenario_id,
                artifacts=artifacts,
            ),
        )

    async def _start_practice_session(
        self,
        *,
        actor: Actor,
        correlation: PracticeCorrelation,
        start_input: StartInputPayload,
    ) -> QuickPracticeSessionView:
        session_id = uuid4().hex
        attempt_id = uuid4().hex
        workflow_id = session_id

        async def input_guard(_ctx) -> Any:
            return ok_output(
                StageflowStageResult(
                    payload=start_input,
                    summary={
                        "practice_type": start_input.practice_type.value,
                        "content_item_id": start_input.content_item_id,
                    },
                )
            )

        async def prompt_enrich(ctx) -> Any:
            return ok_output(
                self._store.load_start_prompt_context(
                    actor,
                    cast(StartInputPayload, payload_from_inputs(ctx, "input_guard")),
                )
            )

        async def learner_enrich(_ctx) -> Any:
            return ok_output(self._store.load_learner_context(actor.user_id))

        async def session_transform(ctx) -> Any:
            prompt_payload = cast(
                PromptContextPayload,
                payload_from_inputs(ctx, "prompt_enrich"),
            )
            return ok_output(
                StageflowStageResult(
                    payload=SessionTransformPayload(
                        session_id=session_id,
                        attempt_id=attempt_id,
                        workflow_id=workflow_id,
                        prompt=prompt_payload.prompt,
                    ),
                    summary={"session_id": session_id, "attempt_id": attempt_id},
                )
            )

        async def persistence_work(ctx) -> Any:
            return ok_output(
                self._store.persist_session_start(
                    ctx=ctx,
                    actor=actor,
                    transform_payload=cast(
                        SessionTransformPayload,
                        payload_from_inputs(ctx, "session_transform"),
                    ),
                )
            )

        pipeline = Pipeline.from_stages(
            stage("input_guard", cast(Any, input_guard), StageKind.GUARD),
            stage(
                "prompt_enrich",
                cast(Any, prompt_enrich),
                StageKind.ENRICH,
                dependencies=("input_guard",),
            ),
            stage(
                "learner_enrich",
                cast(Any, learner_enrich),
                StageKind.ENRICH,
                dependencies=("input_guard",),
            ),
            stage(
                "session_transform",
                cast(Any, session_transform),
                StageKind.TRANSFORM,
                dependencies=("prompt_enrich", "learner_enrich"),
            ),
            stage(
                "persistence_work",
                cast(Any, persistence_work),
                StageKind.WORK,
                dependencies=("session_transform",),
            ),
            name=f"{start_input.practice_type.value}_session_start",
        )

        pipeline_result = await run_logged_pipeline(
            self._stageflow,
            pipeline,
            request_id=correlation.request_id,
            trace_id=correlation.trace_id,
            workflow_id=workflow_id,
            user_id=actor.user_id,
            session_id=session_id,
            execution_mode="practice_runtime",
            service="soft_skills_backend.practice",
            idempotency_key=(
                f"{start_input.practice_type.value}_session_start:{actor.user_id}:{correlation.request_id}"
            ),
            idempotency_params={
                "practice_type": start_input.practice_type.value,
                "content_item_id": start_input.content_item_id,
                "interview_context": None
                if start_input.interview_context is None
                else start_input.interview_context.model_dump(mode="json"),
                "artifacts": [
                    artifact.model_dump(mode="json") for artifact in start_input.artifacts
                ],
            },
        )
        return payload_from_results(
            pipeline_result,
            "persistence_work",
            expected_type=QuickPracticeSessionView,
        )

    async def submit_attempt(
        self,
        actor: Actor,
        correlation: PracticeCorrelation,
        attempt_id: str,
        command: SubmitAttemptCommand,
    ) -> AttemptView:
        ownership = self._store.load_attempt_ownership(attempt_id)
        if ownership.user_id != actor.user_id and not actor.is_admin:
            raise auth_error(
                "Attempt is not visible to this actor",
                code="SS-AUTH-007",
                status_code=403,
                details={"attempt_id": attempt_id},
            )
        self._assessment.set_marker(self._assessment_marker)

        async def input_guard(_ctx) -> Any:
            return ok_output(
                self._store.load_submit_guard(
                    actor=actor,
                    attempt_id=attempt_id,
                    response_text=command.response_text,
                )
            )

        async def prompt_enrich(ctx) -> Any:
            return ok_output(
                self._store.load_resolved_attempt(
                    cast(AttemptGuardPayload, payload_from_inputs(ctx, "input_guard"))
                )
            )

        async def learner_enrich(_ctx) -> Any:
            return ok_output(self._store.load_learner_context(actor.user_id))

        async def submission_work(ctx) -> Any:
            return ok_output(
                self._store.persist_attempt_submission(
                    ctx=ctx,
                    guard=cast(AttemptGuardPayload, payload_from_inputs(ctx, "input_guard")),
                )
            )

        async def assessing_work(ctx) -> Any:
            return ok_output(
                self._store.mark_attempt_assessing(
                    cast(AttemptGuardPayload, payload_from_inputs(ctx, "submission_work"))
                )
            )

        async def assessment_transform(ctx) -> Any:
            return ok_output(
                await self._assessment.run_transform(
                    ctx=ctx,
                    prompt_payload=cast(
                        ResolvedAttemptPayload,
                        payload_from_inputs(ctx, "prompt_enrich"),
                    ),
                    learner_payload=cast(
                        LearnerContextPayload,
                        payload_from_inputs(ctx, "learner_enrich"),
                    ),
                )
            )

        async def output_guard(ctx) -> Any:
            return ok_output(
                self._assessment.validate_output(
                    prompt_payload=cast(
                        ResolvedAttemptPayload,
                        payload_from_inputs(ctx, "prompt_enrich"),
                    ),
                    transform_payload=cast(
                        AssessmentTransformPayload,
                        payload_from_inputs(ctx, "assessment_transform"),
                    ),
                )
            )

        async def persistence_work(ctx) -> Any:
            return ok_output(
                self._store.persist_assessment(
                    ctx=ctx,
                    guard=cast(AttemptGuardPayload, payload_from_inputs(ctx, "input_guard")),
                    assessment=cast(
                        ValidatedAssessmentPayload,
                        payload_from_inputs(ctx, "output_guard"),
                    ),
                )
            )

        pipeline = Pipeline.from_stages(
            stage("input_guard", cast(Any, input_guard), StageKind.GUARD),
            stage(
                "prompt_enrich",
                cast(Any, prompt_enrich),
                StageKind.ENRICH,
                dependencies=("input_guard",),
            ),
            stage(
                "learner_enrich",
                cast(Any, learner_enrich),
                StageKind.ENRICH,
                dependencies=("input_guard",),
            ),
            stage(
                "submission_work",
                cast(Any, submission_work),
                StageKind.WORK,
                dependencies=("input_guard",),
            ),
            stage(
                "assessing_work",
                cast(Any, assessing_work),
                StageKind.WORK,
                dependencies=("submission_work",),
            ),
            stage(
                "assessment_transform",
                cast(Any, assessment_transform),
                StageKind.TRANSFORM,
                dependencies=("prompt_enrich", "learner_enrich", "assessing_work"),
            ),
            stage(
                "output_guard",
                cast(Any, output_guard),
                StageKind.GUARD,
                dependencies=("prompt_enrich", "assessment_transform"),
            ),
            stage(
                "persistence_work",
                cast(Any, persistence_work),
                StageKind.WORK,
                dependencies=("input_guard", "output_guard"),
            ),
            name=f"{ownership.practice_type}_assessment",
        )

        try:
            pipeline_result = await run_logged_pipeline(
                self._stageflow,
                pipeline,
                request_id=correlation.request_id,
                trace_id=correlation.trace_id,
                workflow_id=ownership.workflow_id,
                user_id=actor.user_id,
                session_id=ownership.session_id,
                execution_mode="practice_runtime",
                service="soft_skills_backend.practice",
                idempotency_key=f"{ownership.practice_type}_assessment:{actor.user_id}:{correlation.request_id}:{attempt_id}",
                idempotency_params={
                    "attempt_id": attempt_id,
                    "response_text": command.response_text,
                },
            )
            return payload_from_results(
                pipeline_result,
                "persistence_work",
                expected_type=AttemptView,
            )
        except StructuredOutputRejectionError as exc:
            self._store.persist_rejected_assessment(
                attempt_id=attempt_id,
                request_id=correlation.request_id,
                trace_id=correlation.trace_id,
                provider_name=self._assessment_marker.provider_name,
                model_slug=self._assessment_marker.model_slug,
                rejection_code=exc.app_error.code,
                raw_payload=exc.raw_payload,
            )
            raise exc.app_error from exc
        except AppError as exc:
            if exc.category.value in {"provider", "persistence", "orchestration"}:
                self._store.mark_attempt_failed(
                    attempt_id=attempt_id,
                    request_id=correlation.request_id,
                    trace_id=correlation.trace_id,
                    error=exc,
                )
            raise

    def get_attempt(self, actor: Actor, attempt_id: str) -> AttemptView:
        return self._store.get_attempt(actor, attempt_id)
