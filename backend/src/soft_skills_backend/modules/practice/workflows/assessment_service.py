"""Practice assessment helpers."""

from __future__ import annotations

import re

from stageflow.core import StageContext

from soft_skills_backend.engines.config import load_marking_runtime_config
from soft_skills_backend.engines.marking.domain.rubric_repository import RubricRepository
from soft_skills_backend.modules.practice.domain.practice import (
    PracticeType,
    validate_assessment_draft,
)
from soft_skills_backend.modules.practice.models import ValidatedAssessmentPayload
from soft_skills_backend.modules.practice.workflows.assessment.marking_provider import (
    AssessmentMarkingProvider,
    StructuredOutputRejectionError,
)
from soft_skills_backend.modules.practice.workflows.assessment.models import (
    AssessmentTransformPayload,
    LearnerContextPayload,
    ResolvedAttemptPayload,
)
from soft_skills_backend.platform.workflows.stageflow import (
    StageflowStageResult,
    metadata_value,
    pipeline_run_id_from_context,
    request_id_from_context,
    user_id_from_context,
)
from soft_skills_backend.shared.errors import AppError, scoring_error
from soft_skills_backend.shared.ports.telemetry import ProviderCallContext

from ..infra.repository import PracticeRepository


def _required_rubric_skills(prompt_payload: ResolvedAttemptPayload) -> list[str] | None:
    if prompt_payload.prompt.practice_type in {
        PracticeType.QUICK_PRACTICE,
        PracticeType.SCENARIO,
    }:
        return None
    return list(prompt_payload.prompt.target_skill_slugs)


class AssessmentService:
    """Own assessment provider calls and output validation."""

    def __init__(
        self,
        *,
        store: PracticeRepository,
        assessment_marker: AssessmentMarkingProvider,
        rubric_repository: RubricRepository,
    ) -> None:
        self._store = store
        self._assessment_marker = assessment_marker
        self._rubric_repository = rubric_repository

    def set_marker(self, assessment_marker: AssessmentMarkingProvider) -> None:
        self._assessment_marker = assessment_marker

    async def run_transform(
        self,
        *,
        ctx: StageContext,
        prompt_payload: ResolvedAttemptPayload,
        learner_payload: LearnerContextPayload,
    ) -> StageflowStageResult:
        config = load_marking_runtime_config()
        self._store.record_event(
            event_type="assessment.started.v1",
            request_id=request_id_from_context(ctx),
            trace_id=metadata_value(ctx, "trace_id"),
            workflow_id=metadata_value(ctx, "workflow_id"),
            payload={
                "attempt_id": prompt_payload.attempt_id,
                "session_id": prompt_payload.session_id,
                "practice_type": prompt_payload.prompt.practice_type.value,
                "prompt_type": prompt_payload.prompt.prompt_type,
                "prompt_version": config.prompt_version,
                "rubric_version": prompt_payload.prompt.rubric_version,
                "provider": self._assessment_marker.provider_name,
                "model_slug": self._assessment_marker.model_slug,
            },
        )
        call_context = ProviderCallContext(
            operation=f"{prompt_payload.prompt.practice_type.value}_assessment",
            request_id=request_id_from_context(ctx),
            trace_id=metadata_value(ctx, "trace_id"),
            pipeline_run_id=pipeline_run_id_from_context(ctx),
            workflow_id=metadata_value(ctx, "workflow_id"),
            user_id=user_id_from_context(ctx),
        )
        payload = await self._assessment_marker.mark_attempt(
            prompt_payload=prompt_payload,
            learner_payload=learner_payload,
            call_context=call_context,
        )
        return StageflowStageResult(
            payload=payload,
            summary={
                "model_slug": payload.model_slug,
                "schema_version": payload.schema_version,
            },
        )

    def validate_output(
        self,
        *,
        prompt_payload: ResolvedAttemptPayload,
        transform_payload: AssessmentTransformPayload,
    ) -> StageflowStageResult:
        draft = transform_payload.draft
        config = load_marking_runtime_config()
        if draft.prompt_version != config.prompt_version:
            raise StructuredOutputRejectionError(
                app_error=scoring_error(
                    "Assessment output prompt version did not match the active contract",
                    code="SS-SCORING-007",
                    details={
                        "expected_prompt_version": config.prompt_version,
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
            or not model_slug_matches_execution_source(
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
            required_rubric_skills = _required_rubric_skills(prompt_payload)
            rubric_definition = self._rubric_repository.get_rubric_definition(
                prompt_payload.prompt.rubric_id,
                required_skill_slugs=required_rubric_skills,
            )
            validate_assessment_draft(
                response_text=prompt_payload.response_text,
                required_skill_slugs=required_rubric_skills or [],
                draft=draft,
                rubric_definition=rubric_definition,
            )
        except AppError as exc:
            raise StructuredOutputRejectionError(
                app_error=exc,
                raw_payload=transform_payload.raw_payload,
            ) from exc

        return StageflowStageResult(
            payload=ValidatedAssessmentPayload(
                prompt_version=draft.prompt_version,
                rubric_id=prompt_payload.prompt.rubric_id,
                rubric_version=draft.rubric_version,
                provider=draft.provider,
                model_slug=transform_payload.model_slug,
                schema_version=transform_payload.schema_version,
                config_version=config.config_version,
                overall_score=draft.overall_score,
                rationale=draft.rationale,
                per_skill_assessments=transform_payload.per_skill_assessments,
                skill_scores=draft.skill_scores,
                evidence=draft.evidence,
                strengths=draft.strengths,
                weaknesses=draft.weaknesses,
                next_actions=draft.next_actions,
                raw_payload=transform_payload.raw_payload,
            ),
            summary={"overall_score": draft.overall_score},
        )


def model_slug_matches_execution_source(
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
    return output_slug in accepted_slugs and normalized_output in {
        normalized_executed,
        normalized_configured,
    }


def _normalize_model_slug(model_slug: str) -> str:
    base, separator, suffix = model_slug.partition(":")
    normalized_base = re.sub(r"(?:-\d{8}|-\d{4}-\d{2}-\d{2})$", "", base)
    return normalized_base if not separator else f"{normalized_base}{separator}{suffix}"
