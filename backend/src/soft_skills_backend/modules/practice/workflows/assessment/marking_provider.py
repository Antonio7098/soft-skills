"""Shared assessment marker built on top of a swappable LLM provider."""

from __future__ import annotations

import asyncio
import json
from typing import Callable, Protocol, cast

from soft_skills_backend.config import Settings
from soft_skills_backend.engines.config import load_marking_runtime_config
from soft_skills_backend.engines.marking import (
    PromptLibrary,
    RubricCriterion,
    StructuredOutputRejectionError,
    TypedLLMOutput,
    TypedLLMResult,
)
from soft_skills_backend.engines.marking.domain.per_skill_aggregation import (
    compute_overall_score,
    compute_strengths,
    compute_weaknesses,
)
from soft_skills_backend.engines.marking.domain.rubric_repository import RubricRepository
from soft_skills_backend.modules.practice.domain.practice import (
    AssessmentDraft,
    PerSkillAssessment,
    PracticeType,
    flatten_per_skill_assessments,
)
from soft_skills_backend.modules.practice.workflows.assessment.models import (
    AssessmentAggregationOutput,
    AssessmentTransformPayload,
    LearnerContextPayload,
    PromptTemplate,
    ResolvedAttemptPayload,
)
from soft_skills_backend.platform.providers.llm.prompts import (
    ASSESSMENT_AGGREGATION_PROMPT,
    PER_SKILL_ASSESSMENT_PROMPT,
)
from soft_skills_backend.shared.errors import AppError, scoring_error
from soft_skills_backend.shared.ports.llm import LLMProvider
from soft_skills_backend.shared.ports.telemetry import ProviderCallContext


class AssessmentMarkingProvider(Protocol):
    """Assessment-specific marker sitting above the raw LLM provider."""

    @property
    def provider_name(self) -> str: ...

    @property
    def model_slug(self) -> str: ...

    async def mark_attempt(
        self,
        *,
        prompt_payload: ResolvedAttemptPayload,
        learner_payload: LearnerContextPayload,
        call_context: ProviderCallContext,
    ) -> AssessmentTransformPayload: ...


class DefaultAssessmentMarkingProvider:
    """Default assessment marker using per-skill verified marking plus aggregation."""

    def __init__(
        self,
        *,
        settings: Settings,
        llm_provider: LLMProvider,
        prompt_library: PromptLibrary,
        per_skill_typed_output: TypedLLMOutput,
        aggregation_typed_output: TypedLLMOutput,
        rubric_repository: RubricRepository,
    ) -> None:
        self._llm_provider = llm_provider
        self._prompt_library = prompt_library
        self._per_skill_typed_output = per_skill_typed_output
        self._aggregation_typed_output = aggregation_typed_output
        self._rubric_repository = rubric_repository
        self._verification_retries = settings.assessment_validation_retries

    @property
    def provider_name(self) -> str:
        return self._llm_provider.provider_name

    @property
    def model_slug(self) -> str:
        return self._llm_provider.model_slug

    def _required_rubric_skills(self, prompt_payload: ResolvedAttemptPayload) -> list[str] | None:
        if prompt_payload.prompt.practice_type == PracticeType.QUICK_PRACTICE:
            if not prompt_payload.prompt.target_skill_slugs:
                return None
        return list(prompt_payload.prompt.target_skill_slugs)

    async def mark_attempt(
        self,
        *,
        prompt_payload: ResolvedAttemptPayload,
        learner_payload: LearnerContextPayload,
        call_context: ProviderCallContext,
    ) -> AssessmentTransformPayload:
        config = load_marking_runtime_config()
        rubric = self._rubric_repository.get_rubric_definition(
            prompt_payload.prompt.rubric_id,
            required_skill_slugs=self._required_rubric_skills(prompt_payload),
        )
        per_skill_results = await self._assess_skills(
            prompt_payload=prompt_payload,
            learner_payload=learner_payload,
            call_context=call_context,
            criteria=rubric.criteria,
            max_parallel=config.max_parallel_skill_children,
        )
        assessments = [item[0] for item in per_skill_results]
        overall_score = compute_overall_score(criteria=rubric.criteria, assessments=assessments)
        is_quick_practice = prompt_payload.prompt.practice_type == PracticeType.QUICK_PRACTICE
        if is_quick_practice:
            strengths, weaknesses = _build_quick_practice_strengths_weaknesses(assessments)
        else:
            strengths = compute_strengths(criteria=rubric.criteria, assessments=assessments)
            weaknesses = compute_weaknesses(criteria=rubric.criteria, assessments=assessments)
        aggregation_summary: str
        next_actions: list[str]
        model_slug = self.model_slug
        aggregation_raw_payload: dict[str, object]
        aggregation_usage: dict[str, int]
        if is_quick_practice:
            aggregation_summary, next_actions = _build_quick_practice_feedback(assessments)
            model_slug = self.model_slug
            aggregation_raw_payload = {
                "summary": aggregation_summary,
                "next_actions": list(next_actions),
                "mode": "deterministic_quick_practice",
            }
            aggregation_usage = {}
        else:
            aggregation_result = await self._aggregate_assessment(
                assessments=assessments,
                response_text=prompt_payload.response_text,
                call_context=ProviderCallContext(
                    operation=f"{call_context.operation}:aggregation",
                    request_id=call_context.request_id,
                    trace_id=call_context.trace_id,
                    pipeline_run_id=call_context.pipeline_run_id,
                    workflow_id=call_context.workflow_id,
                    user_id=call_context.user_id,
                ),
            )
            parsed = cast(AssessmentAggregationOutput, aggregation_result.parsed)
            aggregation_summary = parsed.summary
            next_actions = parsed.next_actions
            model_slug = aggregation_result.model_slug
            aggregation_raw_payload = aggregation_result.raw_payload
            aggregation_usage = aggregation_result.usage

        skill_scores, evidence = flatten_per_skill_assessments(assessments)
        draft = AssessmentDraft(
            prompt_version=config.per_skill_prompt_version,
            rubric_version=prompt_payload.prompt.rubric_version,
            provider=self.provider_name,
            model_slug=model_slug,
            overall_score=overall_score,
            rationale=aggregation_summary,
            skill_scores=skill_scores,
            evidence=evidence,
            strengths=strengths,
            weaknesses=weaknesses,
            next_actions=next_actions,
        )
        usage = _merge_usage([item[2] for item in per_skill_results] + [aggregation_usage])
        return AssessmentTransformPayload(
            draft=draft,
            per_skill_assessments=assessments,
            raw_payload={
                "rubric_id": prompt_payload.prompt.rubric_id,
                "per_skill_assessments": [item[1] for item in per_skill_results],
                "aggregation": aggregation_raw_payload,
            },
            model_slug=model_slug,
            schema_version=config.output_schema_version,
            usage=usage,
        )

    async def _assess_skills(
        self,
        *,
        prompt_payload: ResolvedAttemptPayload,
        learner_payload: LearnerContextPayload,
        call_context: ProviderCallContext,
        criteria: list[RubricCriterion],
        max_parallel: int,
    ) -> list[tuple[PerSkillAssessment, dict[str, object], dict[str, int]]]:
        semaphore = asyncio.Semaphore(max(1, max_parallel))

        async def run_one(
            criterion: RubricCriterion,
        ) -> tuple[PerSkillAssessment, dict[str, object], dict[str, int]]:
            async with semaphore:
                return await self._assess_skill(
                    prompt_payload=prompt_payload,
                    learner_payload=learner_payload,
                    criterion=criterion,
                    call_context=ProviderCallContext(
                        operation=f"{call_context.operation}:{criterion.criterion_ref}",
                        request_id=call_context.request_id,
                        trace_id=call_context.trace_id,
                        pipeline_run_id=call_context.pipeline_run_id,
                        workflow_id=call_context.workflow_id,
                        user_id=call_context.user_id,
                    ),
                )

        results = await asyncio.gather(*(run_one(criterion) for criterion in criteria))
        return list(results)

    async def _assess_skill(
        self,
        *,
        prompt_payload: ResolvedAttemptPayload,
        learner_payload: LearnerContextPayload,
        criterion: RubricCriterion,
        call_context: ProviderCallContext,
    ) -> tuple[PerSkillAssessment, dict[str, object], dict[str, int]]:
        config = load_marking_runtime_config()
        rendered_prompt = self._prompt_library.render(
            config.per_skill_prompt_name,
            version=config.per_skill_prompt_version,
            variables={
                "practice_type": prompt_payload.prompt.practice_type.value,
                "prompt_type": prompt_payload.prompt.prompt_type,
                "prompt_text": prompt_payload.prompt.prompt_text,
                "context_block": _render_context_block(prompt_payload),
                "response_text": prompt_payload.response_text,
                "target_role": learner_payload.target_role or "not provided",
                "goals": ", ".join(learner_payload.goals) or "not provided",
                "prior_assessed_attempts": learner_payload.prior_assessed_attempts,
                "skill_slug": criterion.criterion_ref,
                "rubric_id": prompt_payload.prompt.rubric_id,
                "rubric_version": prompt_payload.prompt.rubric_version,
                "criterion_title": criterion.title or criterion.criterion_ref,
                "criterion_description": criterion.description,
                "criterion_levels": _render_criterion_levels(criterion),
            },
        )
        typed_result = await self._generate_verified_output(
            typed_output=self._per_skill_typed_output,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a strict assessment engine. Return JSON only, without markdown fences."
                    ),
                },
                {"role": "user", "content": rendered_prompt.content},
            ],
            call_context=call_context,
            verifier=lambda item: _verify_per_skill_assessment(
                criterion=criterion,
                assessment=item,
                response_text=prompt_payload.response_text,
            ),
        )
        parsed = typed_result.parsed
        if not isinstance(parsed, PerSkillAssessment):
            raise scoring_error(
                "Per-skill assessment output type was invalid",
                code="SS-SCORING-021",
                details={"skill_slug": criterion.criterion_ref},
            )
        return parsed, typed_result.raw_payload, typed_result.usage

    async def _aggregate_assessment(
        self,
        *,
        assessments: list[PerSkillAssessment],
        response_text: str,
        call_context: ProviderCallContext,
    ) -> TypedLLMResult:
        config = load_marking_runtime_config()
        rendered_prompt = self._prompt_library.render(
            config.aggregation_prompt_name,
            version=config.aggregation_prompt_version,
            variables={
                "response_text": response_text,
                "per_skill_json": json.dumps(
                    [item.model_dump(mode="json") for item in assessments],
                    ensure_ascii=True,
                ),
            },
        )
        return await self._aggregation_typed_output.generate(
            self._llm_provider,
            messages=[
                {
                    "role": "system",
                    "content": "You are a strict aggregation engine. Return JSON only.",
                },
                {"role": "user", "content": rendered_prompt.content},
            ],
            call_context=call_context,
        )

    async def _generate_verified_output(
        self,
        *,
        typed_output: TypedLLMOutput,
        messages: list[dict[str, str]],
        call_context: ProviderCallContext,
        verifier: Callable[[object], None],
    ) -> TypedLLMResult:
        retry_messages = list(messages)
        last_result: TypedLLMResult | None = None
        for attempt in range(self._verification_retries + 1):
            typed_result = await typed_output.generate(
                self._llm_provider,
                messages=retry_messages,
                call_context=call_context,
            )
            last_result = typed_result
            try:
                verifier(typed_result.parsed)
                return typed_result
            except AppError as exc:
                if attempt >= self._verification_retries:
                    raise StructuredOutputRejectionError(
                        app_error=exc,
                        raw_payload=typed_result.raw_payload,
                    ) from exc
                retry_messages = [
                    *messages,
                    {
                        "role": "assistant",
                        "content": json.dumps(typed_result.raw_payload, ensure_ascii=True),
                    },
                    {
                        "role": "user",
                        "content": (
                            "Return JSON only. The previous output failed verification. "
                            f"Fix these issues exactly: {exc.message}"
                        ),
                    },
                ]
        if last_result is None:
            raise StructuredOutputRejectionError(
                app_error=scoring_error(
                    "Per-skill verification could not start",
                    code="SS-SCORING-022",
                    details={"operation": call_context.operation},
                ),
                raw_payload={},
            )
        return last_result


def build_prompt_library(settings: Settings) -> PromptLibrary:
    """Register the versioned assessment prompts."""

    del settings
    config = load_marking_runtime_config()
    library = PromptLibrary()
    library.register(
        PromptTemplate(
            name=config.per_skill_prompt_name,
            version=config.per_skill_prompt_version,
            template=PER_SKILL_ASSESSMENT_PROMPT,
        ),
        make_default=True,
    )
    library.register(
        PromptTemplate(
            name=config.aggregation_prompt_name,
            version=config.aggregation_prompt_version,
            template=ASSESSMENT_AGGREGATION_PROMPT,
        ),
        make_default=True,
    )
    return library


def build_typed_output(settings: Settings) -> TypedLLMOutput:
    """Backward-compatible builder for the per-skill worker output."""

    return build_per_skill_typed_output(settings)


def build_per_skill_typed_output(settings: Settings) -> TypedLLMOutput:
    """Create the typed output contract used by per-skill workers."""

    config = load_marking_runtime_config()
    return TypedLLMOutput(
        PerSkillAssessment,
        schema_version=config.per_skill_output_schema_version,
        max_validation_retries=settings.assessment_validation_retries,
    )


def build_aggregation_typed_output(settings: Settings) -> TypedLLMOutput:
    """Create the typed output contract used by the aggregation stage."""

    config = load_marking_runtime_config()
    return TypedLLMOutput(
        AssessmentAggregationOutput,
        schema_version=config.aggregation_output_schema_version,
        max_validation_retries=settings.assessment_validation_retries,
    )


def _verify_per_skill_assessment(
    *,
    criterion: RubricCriterion,
    assessment: object,
    response_text: str,
) -> None:
    if not isinstance(assessment, PerSkillAssessment):
        raise scoring_error(
            "Per-skill assessment output shape was invalid",
            code="SS-SCORING-023",
            details={"criterion_ref": criterion.criterion_ref},
        )
    if assessment.skill_slug != criterion.criterion_ref:
        raise scoring_error(
            "Per-skill assessment returned the wrong skill_slug",
            code="SS-SCORING-024",
            details={
                "expected_skill_slug": criterion.criterion_ref,
                "observed_skill_slug": assessment.skill_slug,
            },
        )
    if assessment.score not in {level.level for level in criterion.levels}:
        raise scoring_error(
            "Per-skill assessment returned a score outside the rubric levels",
            code="SS-SCORING-025",
            details={"skill_slug": assessment.skill_slug, "score": assessment.score},
        )
    normalized_response = _normalize_text(response_text)
    for evidence in assessment.evidence:
        if (
            len(evidence.quote.strip()) < 6
            or _normalize_text(evidence.quote) not in normalized_response
        ):
            raise scoring_error(
                "Evidence must quote the learner response directly",
                code="SS-SCORING-004",
                details={"skill_slug": assessment.skill_slug, "quote": evidence.quote},
            )


def _render_context_block(prompt_payload: ResolvedAttemptPayload) -> str:
    prompt = prompt_payload.prompt
    lines: list[str] = ["- none"]
    if prompt.interview_context is not None:
        interview_lines = [
            "- interview competency context: "
            f"{prompt.interview_context.competency_context or 'not provided'}",
            "- interviewer perspective: "
            f"{prompt.interview_context.interviewer_perspective or 'not provided'}",
        ]
        lines = interview_lines
    if prompt.scenario_context is not None:
        lines = [
            f"- business context: {prompt.scenario_context.business_context}",
            f"- learner objective: {prompt.scenario_context.learner_objective}",
        ]
        if prompt.scenario_context.constraints:
            lines.append("- constraints: " + "; ".join(prompt.scenario_context.constraints))
        if prompt.scenario_context.stakeholder_tensions:
            lines.append(
                "- stakeholder tensions: " + "; ".join(prompt.scenario_context.stakeholder_tensions)
            )
        if prompt.scenario_context.mock_company is not None:
            lines.append(
                "- company: "
                f"{prompt.scenario_context.mock_company.name} / "
                f"{prompt.scenario_context.mock_company.industry} / "
                f"{prompt.scenario_context.mock_company.operating_context}"
            )
        if prompt.scenario_context.mock_people:
            lines.append(
                "- stakeholders: "
                + " | ".join(
                    f"{person.name} ({person.role}) goals={'; '.join(person.goals) or 'none'} "
                    f"style={person.communication_style} "
                    f"relationship={person.relationship_to_scenario}"
                    for person in prompt.scenario_context.mock_people
                )
            )
        if prompt.scenario_context.artifacts:
            lines.append(
                "- artifacts: "
                + " | ".join(
                    f"{artifact.title} [{artifact.artifact_type}] {artifact.body}"
                    for artifact in prompt.scenario_context.artifacts
                )
            )
    return "\n".join(lines)


def _render_criterion_levels(criterion: RubricCriterion) -> str:
    return "\n".join(
        f"- level {level.level}: {level.description} Examples: {'; '.join(level.examples)}"
        for level in sorted(criterion.levels, key=lambda item: item.level)
    )


def _normalize_text(value: str) -> str:
    return " ".join(value.strip().lower().split())


def _merge_usage(usages: list[dict[str, int]]) -> dict[str, int]:
    merged: dict[str, int] = {}
    for usage in usages:
        for key, value in usage.items():
            merged[key] = merged.get(key, 0) + int(value)
    return merged


def _build_quick_practice_feedback(
    assessments: list[PerSkillAssessment],
) -> tuple[str, list[str]]:
    passed = [item for item in assessments if item.score >= 2]
    failed = [item for item in assessments if item.score < 2]
    summary = f"Passed {len(passed)} of {len(assessments)} rubric areas."
    next_actions = [f"Improve {item.skill_slug}: {item.rationale}" for item in failed[:2]]
    if not next_actions:
        next_actions = ["Repeat the exercise and keep the same behaviors explicit."]
    return summary, next_actions


def _build_quick_practice_strengths_weaknesses(
    assessments: list[PerSkillAssessment],
) -> tuple[list[str], list[str]]:
    strengths = [f"{item.skill_slug}: passed" for item in assessments if item.score >= 2]
    weaknesses = [f"{item.skill_slug}: {item.rationale}" for item in assessments if item.score < 2]
    if not strengths:
        strengths = ["No rubric areas passed."]
    if not weaknesses:
        weaknesses = ["No failed rubric areas."]
    return strengths[:2], weaknesses[:2]


__all__ = [
    "AssessmentMarkingProvider",
    "DefaultAssessmentMarkingProvider",
    "PromptLibrary",
    "StructuredOutputRejectionError",
    "TypedLLMOutput",
    "TypedLLMResult",
    "build_prompt_library",
    "build_typed_output",
    "build_per_skill_typed_output",
    "build_aggregation_typed_output",
]
