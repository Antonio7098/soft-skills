"""Practice runtime orchestration service."""

from __future__ import annotations

from typing import Any, cast
from uuid import uuid4

from stageflow.api import Pipeline, StageKind, stage
from stageflow.core import StageContext

from soft_skills_backend.engines.marking.domain.rubric_repository import RubricRepository
from soft_skills_backend.modules.practice.domain.practice import PracticeType
from soft_skills_backend.modules.practice.models import (
    AttemptHistoryItemView,
    AttemptGuardPayload,
    AttemptView,
    PracticeCorrelation,
    PracticeRunItemTransformPayload,
    PracticeRunListItemView,
    PracticeRunTransformPayload,
    PracticeRunView,
    PracticeSessionView,
    PromptContextPayload,
    ScenarioSessionView,
    SessionTransformPayload,
    StartInputPayload,
    StartInterviewRunItemCommand,
    StartInterviewSessionCommand,
    StartPracticeRunCommand,
    StartPracticeSessionCommand,
    StartQuickPracticeRunItemCommand,
    StartScenarioRunItemCommand,
    StartScenarioSessionCommand,
    SubmitAttemptCommand,
    ValidatedAssessmentPayload,
)
from soft_skills_backend.modules.practice.workflows.assessment.marking_provider import (
    AssessmentMarkingProvider,
    StructuredOutputRejectionError,
)
from soft_skills_backend.modules.practice.workflows.assessment.models import (
    AssessmentTransformPayload,
    InterviewContextView,
    LearnerContextPayload,
    PracticeArtifactView,
    ResolvedAttemptPayload,
)
from soft_skills_backend.modules.progression import ProgressionService
from soft_skills_backend.platform.workflows.stageflow import (
    StageflowPipelineSupport,
    StageflowStageResult,
    ok_output,
    payload_from_inputs,
    payload_from_results,
    run_logged_pipeline,
)
from soft_skills_backend.platform.workflows.stageflow_runtime import StageflowRuntime
from soft_skills_backend.shared.auth import Actor
from soft_skills_backend.shared.errors import AppError, auth_error

from ..infra.repository import PracticeRepository
from ..workflows.assessment_service import AssessmentService


class PracticeService:
    """Own the shared text-practice runtime workflow."""

    def __init__(
        self,
        *,
        stageflow_runtime: StageflowRuntime,
        store: PracticeRepository,
        assessment_marker: AssessmentMarkingProvider,
        rubric_repository: RubricRepository,
        progression_service: ProgressionService,
    ) -> None:
        self._store = store
        self._assessment_marker = assessment_marker
        self._progression = progression_service
        self._stageflow = StageflowPipelineSupport.from_runtime(stageflow_runtime)
        self._assessment = AssessmentService(
            store=store,
            assessment_marker=assessment_marker,
            rubric_repository=rubric_repository,
        )

    async def start_session(
        self,
        actor: Actor,
        correlation: PracticeCorrelation,
        command: StartPracticeSessionCommand,
    ) -> PracticeSessionView:
        return await self._start_practice_session(
            actor=actor,
            correlation=correlation,
            start_input=StartInputPayload(
                practice_type=PracticeType.QUICK_PRACTICE,
                content_item_id=command.prompt_item_id,
            ),
        )

    async def start_practice_run(
        self,
        actor: Actor,
        correlation: PracticeCorrelation,
        command: StartPracticeRunCommand,
    ) -> PracticeRunView:
        run_id = uuid4().hex
        workflow_id = run_id
        start_inputs = [self._start_input_from_run_item(item) for item in command.items]

        async def input_guard(_ctx: StageContext) -> Any:
            return ok_output(
                StageflowStageResult(
                    payload=start_inputs,
                    summary={"total_items": len(start_inputs)},
                )
            )

        async def prompt_enrich(ctx: StageContext) -> Any:
            inputs = cast(list[StartInputPayload], payload_from_inputs(ctx, "input_guard"))
            prompt_payloads = [
                cast(
                    PromptContextPayload,
                    self._store.load_start_prompt_context(actor, start_input).payload,
                )
                for start_input in inputs
            ]
            return ok_output(
                StageflowStageResult(
                    payload=prompt_payloads,
                    summary={"total_items": len(prompt_payloads)},
                )
            )

        async def run_transform(ctx: StageContext) -> Any:
            prompt_payloads = cast(
                list[PromptContextPayload],
                payload_from_inputs(ctx, "prompt_enrich"),
            )
            items = [
                PracticeRunItemTransformPayload(
                    position=index,
                    session_id=uuid4().hex,
                    attempt_id=uuid4().hex,
                    prompt=prompt_payload.prompt,
                )
                for index, prompt_payload in enumerate(prompt_payloads, start=1)
            ]
            return ok_output(
                StageflowStageResult(
                    payload=PracticeRunTransformPayload(
                        run_id=run_id,
                        workflow_id=workflow_id,
                        items=items,
                    ),
                    summary={"run_id": run_id, "total_items": len(items)},
                )
            )

        async def persistence_work(ctx: StageContext) -> Any:
            return ok_output(
                self._store.persist_practice_run_start(
                    ctx=ctx,
                    actor=actor,
                    transform_payload=cast(
                        PracticeRunTransformPayload,
                        payload_from_inputs(ctx, "run_transform"),
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
                "run_transform",
                cast(Any, run_transform),
                StageKind.TRANSFORM,
                dependencies=("prompt_enrich",),
            ),
            stage(
                "persistence_work",
                cast(Any, persistence_work),
                StageKind.WORK,
                dependencies=("run_transform",),
            ),
            name="practice_run_start",
        )

        pipeline_result = await run_logged_pipeline(
            self._stageflow,
            pipeline,
            request_id=correlation.request_id,
            trace_id=correlation.trace_id,
            workflow_id=workflow_id,
            user_id=actor.user_id,
            session_id=run_id,
            execution_mode="practice_runtime",
            service="soft_skills_backend.practice",
            idempotency_key=f"practice_run_start:{actor.user_id}:{correlation.request_id}",
            idempotency_params={
                "items": [item.model_dump(mode="json") for item in command.items],
            },
        )
        return payload_from_results(
            pipeline_result,
            "persistence_work",
            expected_type=PracticeRunView,
        )

    async def start_interview_session(
        self,
        actor: Actor,
        correlation: PracticeCorrelation,
        command: StartInterviewSessionCommand,
    ) -> PracticeSessionView:
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
    ) -> ScenarioSessionView:
        artifacts = [
            PracticeArtifactView(
                artifact_id=f"{command.scenario_id}-artifact-{index}",
                artifact_type=artifact.artifact_type,
                title=artifact.title,
                body=artifact.body,
            )
            for index, artifact in enumerate(command.artifacts, start=1)
        ]
        session = await self._start_practice_session(
            actor=actor,
            correlation=correlation,
            start_input=StartInputPayload(
                practice_type=PracticeType.SCENARIO,
                content_item_id=command.scenario_id,
                artifacts=artifacts,
            ),
        )
        return self._store.get_scenario_session(actor, session.session_id)

    async def submit_scenario_step(
        self,
        actor: Actor,
        correlation: PracticeCorrelation,
        session_id: str,
        command: SubmitAttemptCommand,
    ) -> ScenarioSessionView:
        session = self._store.get_scenario_session(actor, session_id)
        await self.submit_attempt(actor, correlation, session.attempt_id, command)
        return self._store.advance_scenario_session(
            actor=actor,
            request_id=correlation.request_id,
            trace_id=correlation.trace_id,
            workflow_id=correlation.workflow_id,
            session_id=session_id,
        )

    async def _start_practice_session(
        self,
        *,
        actor: Actor,
        correlation: PracticeCorrelation,
        start_input: StartInputPayload,
    ) -> PracticeSessionView:
        session_id = uuid4().hex
        attempt_id = uuid4().hex
        workflow_id = session_id

        async def input_guard(_ctx: StageContext) -> Any:
            return ok_output(
                StageflowStageResult(
                    payload=start_input,
                    summary={
                        "practice_type": start_input.practice_type.value,
                        "content_item_id": start_input.content_item_id,
                    },
                )
            )

        async def prompt_enrich(ctx: StageContext) -> Any:
            return ok_output(
                self._store.load_start_prompt_context(
                    actor,
                    cast(StartInputPayload, payload_from_inputs(ctx, "input_guard")),
                )
            )

        async def learner_enrich(_ctx: StageContext) -> Any:
            return ok_output(self._store.load_learner_context(actor.user_id))

        async def session_transform(ctx: StageContext) -> Any:
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

        async def persistence_work(ctx: StageContext) -> Any:
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
            expected_type=PracticeSessionView,
        )

    async def submit_attempt(
        self,
        actor: Actor,
        correlation: PracticeCorrelation,
        attempt_id: str,
        command: SubmitAttemptCommand,
    ) -> AttemptView:
        ownership = self._store.load_attempt_ownership(attempt_id)
        if ownership.user_id != actor.user_id:
            raise auth_error(
                "Attempt submission is only allowed for the owning learner",
                code="SS-AUTH-012",
                status_code=403,
                details={"attempt_id": attempt_id},
            )
        self._assessment.set_marker(self._assessment_marker)

        async def input_guard(_ctx: StageContext) -> Any:
            return ok_output(
                self._store.load_submit_guard(
                    actor=actor,
                    attempt_id=attempt_id,
                    response_text=command.response_text,
                )
            )

        async def prompt_enrich(ctx: StageContext) -> Any:
            return ok_output(
                self._store.load_resolved_attempt(
                    cast(AttemptGuardPayload, payload_from_inputs(ctx, "input_guard"))
                )
            )

        async def learner_enrich(_ctx: StageContext) -> Any:
            return ok_output(self._store.load_learner_context(actor.user_id))

        async def submission_work(ctx: StageContext) -> Any:
            return ok_output(
                self._store.persist_attempt_submission(
                    ctx=ctx,
                    guard=cast(AttemptGuardPayload, payload_from_inputs(ctx, "input_guard")),
                )
            )

        async def assessing_work(ctx: StageContext) -> Any:
            return ok_output(
                self._store.mark_attempt_assessing(
                    cast(AttemptGuardPayload, payload_from_inputs(ctx, "submission_work"))
                )
            )

        async def assessment_transform(ctx: StageContext) -> Any:
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

        async def output_guard(ctx: StageContext) -> Any:
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

        async def persistence_work(ctx: StageContext) -> Any:
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
            payload = payload_from_results(
                pipeline_result,
                "persistence_work",
                expected_type=AttemptView,
            )
            assessment_view = payload.assessment
            if (
                assessment_view is not None
                and assessment_view.validation_status.value == "validated"
                and ownership.practice_type != "quick_practice"
            ):
                await self._progression.refresh_from_assessment(
                    request_id=correlation.request_id,
                    trace_id=correlation.trace_id,
                    workflow_id=ownership.workflow_id,
                    learner_id=ownership.user_id,
                    assessment_id=assessment_view.assessment_id,
                )
            return payload
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

    def list_attempt_history(self, actor: Actor) -> list[AttemptHistoryItemView]:
        return self._store.list_attempt_history(actor)

    def get_practice_run(self, actor: Actor, run_id: str) -> PracticeRunView:
        return self._store.get_practice_run(actor, run_id)

    def list_practice_runs(self, actor: Actor) -> list[PracticeRunListItemView]:
        return self._store.list_practice_runs(actor)

    def get_practice_run_sessions(self, actor: Actor, run_id: str) -> list[dict]:
        return self._store.get_practice_run_sessions(actor, run_id)

    @staticmethod
    def _start_input_from_run_item(
        item: StartQuickPracticeRunItemCommand
        | StartInterviewRunItemCommand
        | StartScenarioRunItemCommand,
    ) -> StartInputPayload:
        if isinstance(item, StartQuickPracticeRunItemCommand):
            return StartInputPayload(
                practice_type=PracticeType.QUICK_PRACTICE,
                content_item_id=item.prompt_item_id,
            )
        if isinstance(item, StartInterviewRunItemCommand):
            return StartInputPayload(
                practice_type=PracticeType.INTERVIEW,
                content_item_id=item.prompt_item_id,
                interview_context=InterviewContextView(
                    competency_context=item.competency_context,
                    interviewer_perspective=item.interviewer_perspective,
                ),
            )
        return StartInputPayload(
            practice_type=PracticeType.SCENARIO,
            content_item_id=item.scenario_id,
            artifacts=[
                PracticeArtifactView(
                    artifact_id=f"{item.scenario_id}-artifact-{index}",
                    artifact_type=artifact.artifact_type,
                    title=artifact.title,
                    body=artifact.body,
                )
                for index, artifact in enumerate(item.artifacts, start=1)
            ],
        )
