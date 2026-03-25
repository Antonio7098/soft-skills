"""Quick-practice assessment marker built on top of a swappable LLM provider."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Protocol, TypeVar, cast

from pydantic import BaseModel, ValidationError

from soft_skills_backend.config import Settings
from soft_skills_backend.modules.practice.domain.practice import (
    QuickPracticeAssessmentDraft,
)
from soft_skills_backend.modules.practice.workflows.assessment.models import (
    AssessmentTransformPayload,
    LearnerContextPayload,
    PromptTemplate,
    RenderedPrompt,
    ResolvedAttemptPayload,
)
from soft_skills_backend.platform.providers.llm.prompts import (
    ASSESSMENT_PROMPT_NAME,
    QUICK_PRACTICE_ASSESSMENT_PROMPT,
)
from soft_skills_backend.shared.errors import AppError, validation_error
from soft_skills_backend.shared.ports.llm import (
    LLMProvider,
)
from soft_skills_backend.shared.ports.telemetry import ProviderCallContext

ModelT = TypeVar("ModelT", bound=BaseModel)


class QuickPracticeMarkingProvider(Protocol):
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


@dataclass(slots=True)
class TypedLLMResult:
    """Validated typed model output."""

    parsed: BaseModel
    raw_payload: dict[str, Any]
    schema_version: str
    usage: dict[str, int]
    model_slug: str


@dataclass(slots=True)
class StructuredOutputRejectionError(Exception):
    """Raised when a provider returned data that must be rejected."""

    app_error: AppError
    raw_payload: dict[str, Any]


class PromptLibrary:
    """Small local prompt library aligned with the Stageflow guidance."""

    def __init__(self) -> None:
        self._templates: dict[tuple[str, str], PromptTemplate] = {}
        self._defaults: dict[str, str] = {}

    def register(self, template: PromptTemplate, *, make_default: bool = False) -> None:
        self._templates[(template.name, template.version)] = template
        if make_default or template.name not in self._defaults:
            self._defaults[template.name] = template.version

    def render(
        self,
        name: str,
        *,
        variables: dict[str, object],
        version: str | None = None,
    ) -> RenderedPrompt:
        resolved_version = version or self._defaults.get(name)
        if resolved_version is None:
            raise validation_error(
                "Prompt library default version was not found",
                code="SS-VALIDATION-017",
                details={"prompt_name": name},
            )
        template = self._templates.get((name, resolved_version))
        if template is None:
            raise validation_error(
                "Prompt library template was not found",
                code="SS-VALIDATION-018",
                details={"prompt_name": name, "prompt_version": resolved_version},
            )
        return RenderedPrompt(
            name=template.name,
            version=template.version,
            content=template.template.format(**variables),
        )


class TypedLLMOutput:
    """Pydantic-backed typed output parser with bounded corrective retries."""

    def __init__(
        self,
        model_type: type[ModelT],
        *,
        schema_version: str,
        max_validation_retries: int,
    ) -> None:
        self._model_type = model_type
        self._schema_version = schema_version
        self._max_validation_retries = max_validation_retries

    async def generate(
        self,
        provider: LLMProvider,
        *,
        messages: list[dict[str, str]],
        call_context: ProviderCallContext,
    ) -> TypedLLMResult:
        retry_messages = list(messages)
        last_payload: dict[str, Any] = {}
        for attempt in range(self._max_validation_retries + 1):
            completion = await provider.complete_json(
                messages=retry_messages,
                call_context=call_context,
            )
            try:
                payload = _coerce_json_payload(completion.content)
                last_payload = payload
                parsed = self._model_type.model_validate(payload)
                return TypedLLMResult(
                    parsed=parsed,
                    raw_payload=payload,
                    schema_version=self._schema_version,
                    usage=completion.usage,
                    model_slug=completion.model_slug,
                )
            except (json.JSONDecodeError, ValidationError) as exc:
                if attempt >= self._max_validation_retries:
                    raise StructuredOutputRejectionError(
                        app_error=validation_error(
                            "Provider returned malformed structured output",
                            code="SS-VALIDATION-019",
                            details={"reason": str(exc)},
                        ),
                        raw_payload=last_payload,
                    ) from exc
                retry_messages = [
                    *messages,
                    {
                        "role": "assistant",
                        "content": _stringify_provider_content(completion.content),
                    },
                    {
                        "role": "user",
                        "content": (
                            "Return JSON only. The previous output was invalid. "
                            f"Fix the schema issues: {exc}"
                        ),
                    },
                ]
        raise StructuredOutputRejectionError(
            app_error=validation_error(
                "Provider returned malformed structured output",
                code="SS-VALIDATION-019",
            ),
            raw_payload=last_payload,
        )


class DefaultQuickPracticeMarkingProvider:
    """Default assessment marker that calls a pluggable LLM provider."""

    def __init__(
        self,
        *,
        settings: Settings,
        llm_provider: LLMProvider,
        prompt_library: PromptLibrary,
        typed_output: TypedLLMOutput,
    ) -> None:
        self._settings = settings
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
        rendered_prompt = self._prompt_library.render(
            ASSESSMENT_PROMPT_NAME,
            version=self._settings.assessment_prompt_version,
            variables={
                "practice_type": prompt_payload.prompt.practice_type.value,
                "prompt_type": prompt_payload.prompt.prompt_type,
                "prompt_text": prompt_payload.prompt.prompt_text,
                "context_block": _render_context_block(prompt_payload),
                "response_text": prompt_payload.response_text,
                "skill_slugs": ", ".join(prompt_payload.prompt.target_skill_slugs),
                "rubric_version": prompt_payload.prompt.rubric_version,
                "prompt_version": self._settings.assessment_prompt_version,
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
            draft=QuickPracticeAssessmentDraft.model_validate(typed_result.parsed.model_dump()),
            raw_payload=typed_result.raw_payload,
            model_slug=typed_result.model_slug,
            schema_version=typed_result.schema_version,
        )


def build_prompt_library(settings: Settings) -> PromptLibrary:
    """Register the versioned quick-practice assessment prompt."""

    library = PromptLibrary()
    library.register(
        PromptTemplate(
            name=ASSESSMENT_PROMPT_NAME,
            version=settings.assessment_prompt_version,
            template=QUICK_PRACTICE_ASSESSMENT_PROMPT,
        ),
        make_default=True,
    )
    return library


def build_typed_output(settings: Settings) -> TypedLLMOutput:
    """Create the typed output contract used by the marking pipeline."""

    return TypedLLMOutput(
        QuickPracticeAssessmentDraft,
        schema_version=settings.assessment_output_schema_version,
        max_validation_retries=settings.assessment_validation_retries,
    )


def _coerce_json_payload(content: str | dict[str, Any]) -> dict[str, Any]:
    if isinstance(content, dict):
        return content
    parsed = json.loads(content)
    if isinstance(parsed, dict):
        return cast(dict[str, Any], parsed)
    raise json.JSONDecodeError("Expected a JSON object", content, 0)


def _stringify_provider_content(content: str | dict[str, Any]) -> str:
    if isinstance(content, str):
        return content
    return json.dumps(content)


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
