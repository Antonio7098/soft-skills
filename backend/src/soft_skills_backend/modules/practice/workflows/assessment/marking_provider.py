"""Shared assessment marker built on top of a swappable LLM provider."""

from __future__ import annotations

from typing import Protocol

from soft_skills_backend.config import Settings
from soft_skills_backend.engines.config import load_marking_runtime_config
from soft_skills_backend.engines.marking import (
    PromptLibrary,
    StructuredOutputRejectionError,
    TypedLLMOutput,
    TypedLLMResult,
)
from soft_skills_backend.modules.practice.domain.practice import (
    AssessmentDraft,
)
from soft_skills_backend.modules.practice.workflows.assessment.models import (
    AssessmentTransformPayload,
    LearnerContextPayload,
    PromptTemplate,
    ResolvedAttemptPayload,
)
from soft_skills_backend.platform.providers.llm.prompts import (
    QUICK_PRACTICE_ASSESSMENT_PROMPT,
)
from soft_skills_backend.shared.ports.llm import (
    LLMProvider,
)
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
    """Default assessment marker that calls a pluggable LLM provider."""

    def __init__(
        self,
        *,
        settings: Settings,
        llm_provider: LLMProvider,
        prompt_library: PromptLibrary,
        typed_output: TypedLLMOutput,
    ) -> None:
        del settings
        self._llm_provider = llm_provider
        self._prompt_library = prompt_library
        self._typed_output = typed_output

    @property
    def provider_name(self) -> str:
        return self._llm_provider.provider_name

    @property
    def model_slug(self) -> str:
        return self._llm_provider.model_slug

    async def mark_attempt(
        self,
        *,
        prompt_payload: ResolvedAttemptPayload,
        learner_payload: LearnerContextPayload,
        call_context: ProviderCallContext,
    ) -> AssessmentTransformPayload:
        config = load_marking_runtime_config()
        rendered_prompt = self._prompt_library.render(
            config.prompt_name,
            version=config.prompt_version,
            variables={
                "practice_type": prompt_payload.prompt.practice_type.value,
                "prompt_type": prompt_payload.prompt.prompt_type,
                "prompt_text": prompt_payload.prompt.prompt_text,
                "context_block": _render_context_block(prompt_payload),
                "response_text": prompt_payload.response_text,
                "skill_slugs": ", ".join(prompt_payload.prompt.target_skill_slugs),
                "rubric_version": prompt_payload.prompt.rubric_version,
                "prompt_version": config.prompt_version,
                "provider": self.provider_name,
                "model_slug": self.model_slug,
                "target_role": learner_payload.target_role or "not provided",
                "prior_assessed_attempts": learner_payload.prior_assessed_attempts,
                "goals": ", ".join(learner_payload.goals) or "not provided",
            },
        )
        typed_result = await self._typed_output.generate(
            self._llm_provider,
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
        )
        return AssessmentTransformPayload(
            draft=AssessmentDraft.model_validate(typed_result.parsed.model_dump()),
            raw_payload=typed_result.raw_payload,
            model_slug=typed_result.model_slug,
            schema_version=typed_result.schema_version,
        )


def build_prompt_library(settings: Settings) -> PromptLibrary:
    """Register the versioned assessment prompt."""

    del settings
    config = load_marking_runtime_config()
    library = PromptLibrary()
    library.register(
        PromptTemplate(
            name=config.prompt_name,
            version=config.prompt_version,
            template=QUICK_PRACTICE_ASSESSMENT_PROMPT,
        ),
        make_default=True,
    )
    return library


def build_typed_output(settings: Settings) -> TypedLLMOutput:
    """Create the typed output contract used by the marking pipeline."""

    config = load_marking_runtime_config()
    return TypedLLMOutput(
        AssessmentDraft,
        schema_version=config.output_schema_version,
        max_validation_retries=settings.assessment_validation_retries,
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


__all__ = [
    "AssessmentMarkingProvider",
    "DefaultAssessmentMarkingProvider",
    "PromptLibrary",
    "StructuredOutputRejectionError",
    "TypedLLMOutput",
    "TypedLLMResult",
    "build_prompt_library",
    "build_typed_output",
]
