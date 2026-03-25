"""Quick-practice orchestration service."""

from __future__ import annotations

import re
from typing import cast
from uuid import uuid4

from soft_skills_backend.application.assessment.models import (
    AssessmentTransformPayload,
    LearnerContextPayload,
    QuickPracticePromptView,
    ResolvedAttemptPayload,
)
from soft_skills_backend.application.assessment.quick_practice_marking import (
    QuickPracticeMarkingProvider,
    StructuredOutputRejectionError,
)
from soft_skills_backend.application.auth import Actor
from soft_skills_backend.application.ports.telemetry import ProviderCallContext
from soft_skills_backend.application.practice.models import (
    AttemptView,
    PracticeCorrelation,
    QuickPracticeSessionView,
    SessionTransformPayload,
    StartInputPayload,
    StartQuickPracticeSessionCommand,
    SubmitAttemptCommand,
    ValidatedAssessmentPayload,
)
from soft_skills_backend.application.practice.quick_practice.repository import (
    DELIVERY_VERSION,
    QuickPracticeRepository,
)
from soft_skills_backend.domain.errors import AppError, auth_error, scoring_error
from soft_skills_backend.domain.practice import validate_assessment_draft
from soft_skills_backend.orchestration.quick_practice import (
    PipelineDefinition,
    PipelineExecutionContext,
    PipelineStage,
    QuickPracticePipelineExecutor,
    StageExecutionResult,
)
from soft_skills_backend.orchestration.stageflow_runtime import SoftSkillsStageKind


class QuickPracticeService:
    """Own the Sprint 3 quick-practice vertical slice."""

    def __init__(
        self,
        *,
        pipeline_executor: QuickPracticePipelineExecutor,
        store: QuickPracticeRepository,
        assessment_marker: QuickPracticeMarkingProvider,
    ) -> None:
        self._pipeline_executor = pipeline_executor
        self._store = store
        self._assessment_marker = assessment_marker

    async def start_session(
        self,
        actor: Actor,
        correlation: PracticeCorrelation,
        command: StartQuickPracticeSessionCommand,
    ) -> QuickPracticeSessionView:
        session_id = uuid4().hex
        attempt_id = uuid4().hex
        workflow_id = session_id

        definition = PipelineDefinition(
            name="quick_practice_session_start",
            stages=(
                PipelineStage(
                    name="input_guard",
                    kind=SoftSkillsStageKind.GUARD.value,
                    handler=lambda _ctx, _deps: StageExecutionResult(
                        payload=StartInputPayload(prompt_item_id=command.prompt_item_id),
                        summary={"prompt_item_id": command.prompt_item_id},
                    ),
                ),
                PipelineStage(
                    name="prompt_enrich",
                    kind=SoftSkillsStageKind.ENRICH.value,
                    dependencies=("input_guard",),
                    handler=lambda _ctx, deps: self._store.load_start_prompt_context(
                        actor,
                        deps["input_guard"],
                    ),
                ),
                PipelineStage(
                    name="learner_enrich",
                    kind=SoftSkillsStageKind.ENRICH.value,
                    dependencies=("input_guard",),
                    handler=lambda _ctx, _deps: self._store.load_learner_context(actor.user_id),
                ),
                PipelineStage(
                    name="session_transform",
                    kind=SoftSkillsStageKind.TRANSFORM.value,
                    dependencies=("prompt_enrich", "learner_enrich"),
                    handler=lambda _ctx, deps: StageExecutionResult(
                        payload=SessionTransformPayload(
                            session_id=session_id,
                            attempt_id=attempt_id,
                            workflow_id=workflow_id,
                            prompt=QuickPracticePromptView(
                                content_item_id=deps["prompt_enrich"].content_item_id,
                                prompt_type=deps["prompt_enrich"].prompt_type,
                                title=deps["prompt_enrich"].title,
                                prompt_text=deps["prompt_enrich"].prompt_text,
                                difficulty=deps["prompt_enrich"].difficulty,
                                delivery_version=DELIVERY_VERSION,
                                target_skill_slugs=deps["prompt_enrich"].target_skill_slugs,
                                rubric_id=deps["prompt_enrich"].rubric_id,
                                rubric_version=deps["prompt_enrich"].rubric_version,
                            ),
                        ),
                        summary={"session_id": session_id, "attempt_id": attempt_id},
                    ),
                ),
                PipelineStage(
                    name="persistence_work",
                    kind=SoftSkillsStageKind.WORK.value,
                    dependencies=("session_transform",),
                    handler=lambda ctx, deps: self._store.persist_session_start(
                        ctx=ctx,
                        actor=actor,
                        transform_payload=deps["session_transform"],
                    ),
                ),
            ),
        )

        pipeline_result = await self._pipeline_executor.run(
            definition,
            request_id=correlation.request_id,
            trace_id=correlation.trace_id,
            workflow_id=workflow_id,
            user_id=actor.user_id,
        )
        return cast(QuickPracticeSessionView, pipeline_result.payload_for("persistence_work"))

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

        definition = PipelineDefinition(
            name="quick_practice_assessment",
            stages=(
                PipelineStage(
                    name="input_guard",
                    kind=SoftSkillsStageKind.GUARD.value,
                    handler=lambda _ctx, _deps: self._store.load_submit_guard(
                        actor=actor,
                        attempt_id=attempt_id,
                        response_text=command.response_text,
                    ),
                ),
                PipelineStage(
                    name="prompt_enrich",
                    kind=SoftSkillsStageKind.ENRICH.value,
                    dependencies=("input_guard",),
                    handler=lambda _ctx, deps: self._store.load_resolved_attempt(
                        deps["input_guard"]
                    ),
                ),
                PipelineStage(
                    name="learner_enrich",
                    kind=SoftSkillsStageKind.ENRICH.value,
                    dependencies=("input_guard",),
                    handler=lambda _ctx, _deps: self._store.load_learner_context(actor.user_id),
                ),
                PipelineStage(
                    name="submission_work",
                    kind=SoftSkillsStageKind.WORK.value,
                    dependencies=("input_guard",),
                    handler=lambda ctx, deps: self._store.persist_attempt_submission(
                        ctx=ctx,
                        guard=deps["input_guard"],
                    ),
                ),
                PipelineStage(
                    name="assessing_work",
                    kind=SoftSkillsStageKind.WORK.value,
                    dependencies=("submission_work",),
                    handler=lambda _ctx, deps: self._store.mark_attempt_assessing(
                        deps["submission_work"],
                    ),
                ),
                PipelineStage(
                    name="assessment_transform",
                    kind=SoftSkillsStageKind.TRANSFORM.value,
                    dependencies=("prompt_enrich", "learner_enrich", "assessing_work"),
                    handler=lambda ctx, deps: self._run_assessment_transform(
                        ctx=ctx,
                        prompt_payload=deps["prompt_enrich"],
                        learner_payload=deps["learner_enrich"],
                    ),
                ),
                PipelineStage(
                    name="output_guard",
                    kind=SoftSkillsStageKind.GUARD.value,
                    dependencies=("prompt_enrich", "assessment_transform"),
                    handler=lambda _ctx, deps: self._validate_assessment_output(
                        prompt_payload=deps["prompt_enrich"],
                        transform_payload=deps["assessment_transform"],
                    ),
                ),
                PipelineStage(
                    name="persistence_work",
                    kind=SoftSkillsStageKind.WORK.value,
                    dependencies=("input_guard", "output_guard"),
                    handler=lambda ctx, deps: self._store.persist_assessment(
                        ctx=ctx,
                        guard=deps["input_guard"],
                        assessment=deps["output_guard"],
                    ),
                ),
            ),
        )

        try:
            pipeline_result = await self._pipeline_executor.run(
                definition,
                request_id=correlation.request_id,
                trace_id=correlation.trace_id,
                workflow_id=ownership.workflow_id,
                user_id=actor.user_id,
            )
            return cast(AttemptView, pipeline_result.payload_for("persistence_work"))
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

    async def _run_assessment_transform(
        self,
        *,
        ctx: PipelineExecutionContext,
        prompt_payload: ResolvedAttemptPayload,
        learner_payload: LearnerContextPayload,
    ) -> StageExecutionResult:
        self._store.record_event(
            event_type="assessment.started.v1",
            request_id=ctx.request_id,
            trace_id=ctx.trace_id,
            workflow_id=ctx.workflow_id,
            payload={
                "attempt_id": prompt_payload.attempt_id,
                "session_id": prompt_payload.session_id,
                "prompt_version": self._store.settings.assessment_prompt_version,
                "rubric_version": prompt_payload.prompt.rubric_version,
                "provider": self._assessment_marker.provider_name,
                "model_slug": self._assessment_marker.model_slug,
            },
        )
        call_context = ProviderCallContext(
            operation="quick_practice_assessment",
            request_id=ctx.request_id,
            trace_id=ctx.trace_id,
            pipeline_run_id=ctx.pipeline_run_id,
            workflow_id=ctx.workflow_id,
            user_id=ctx.user_id,
        )
        payload = await self._assessment_marker.mark_attempt(
            prompt_payload=prompt_payload,
            learner_payload=learner_payload,
            call_context=call_context,
        )
        return StageExecutionResult(
            payload=payload,
            summary={
                "model_slug": payload.model_slug,
                "schema_version": payload.schema_version,
            },
        )

    def _validate_assessment_output(
        self,
        *,
        prompt_payload: ResolvedAttemptPayload,
        transform_payload: AssessmentTransformPayload,
    ) -> StageExecutionResult:
        draft = transform_payload.draft
        settings = self._store.settings
        if draft.prompt_version != settings.assessment_prompt_version:
            raise StructuredOutputRejectionError(
                app_error=scoring_error(
                    "Assessment output prompt version did not match the active contract",
                    code="SS-SCORING-007",
                    details={
                        "expected_prompt_version": settings.assessment_prompt_version,
                        "observed_prompt_version": draft.prompt_version,
                    },
                ),
                raw_payload=transform_payload.raw_payload,
            )
        if draft.rubric_version != prompt_payload.prompt.rubric_version:
            raise StructuredOutputRejectionError(
                app_error=scoring_error(
                    "Assessment output rubric version did not match the active rubric",
                    code="SS-SCORING-008",
                    details={
                        "expected_rubric_version": prompt_payload.prompt.rubric_version,
                        "observed_rubric_version": draft.rubric_version,
                    },
                ),
                raw_payload=transform_payload.raw_payload,
            )
        if (
            draft.provider != self._assessment_marker.provider_name
            or not _model_slug_matches_execution_source(
                executed_slug=transform_payload.model_slug,
                output_slug=draft.model_slug,
                configured_slug=self._assessment_marker.model_slug,
            )
        ):
            raise StructuredOutputRejectionError(
                app_error=scoring_error(
                    "Assessment output provider metadata did not match the execution source",
                    code="SS-SCORING-009",
                    details={
                        "expected_provider": self._assessment_marker.provider_name,
                        "observed_provider": draft.provider,
                        "expected_model_slug": transform_payload.model_slug,
                        "observed_model_slug": draft.model_slug,
                    },
                ),
                raw_payload=transform_payload.raw_payload,
            )
        try:
            validate_assessment_draft(
                response_text=prompt_payload.response_text,
                required_skill_slugs=prompt_payload.prompt.target_skill_slugs,
                draft=draft,
            )
        except AppError as exc:
            raise StructuredOutputRejectionError(
                app_error=exc,
                raw_payload=transform_payload.raw_payload,
            ) from exc

        return StageExecutionResult(
            payload=ValidatedAssessmentPayload(
                prompt_version=draft.prompt_version,
                rubric_id=prompt_payload.prompt.rubric_id,
                rubric_version=draft.rubric_version,
                provider=draft.provider,
                model_slug=transform_payload.model_slug,
                schema_version=transform_payload.schema_version,
                config_version=settings.scoring_config_version,
                overall_score=draft.overall_score,
                rationale=draft.rationale,
                skill_scores=draft.skill_scores,
                evidence=draft.evidence,
                strengths=draft.strengths,
                weaknesses=draft.weaknesses,
                next_actions=draft.next_actions,
                raw_payload=transform_payload.raw_payload,
            ),
            summary={"overall_score": draft.overall_score},
        )


def _model_slug_matches_execution_source(
    *,
    executed_slug: str,
    output_slug: str,
    configured_slug: str,
) -> bool:
    accepted_slugs = {
        executed_slug,
        output_slug,
        configured_slug,
        _normalize_model_slug(executed_slug),
        _normalize_model_slug(output_slug),
        _normalize_model_slug(configured_slug),
    }
    normalized_executed = _normalize_model_slug(executed_slug)
    normalized_output = _normalize_model_slug(output_slug)
    normalized_configured = _normalize_model_slug(configured_slug)
    return (
        output_slug in accepted_slugs
        and normalized_output in {normalized_executed, normalized_configured}
    )


def _normalize_model_slug(model_slug: str) -> str:
    base, separator, suffix = model_slug.partition(":")
    normalized_base = re.sub(r"(?:-\d{8}|-\d{4}-\d{2}-\d{2})$", "", base)
    return normalized_base if not separator else f"{normalized_base}{separator}{suffix}"
