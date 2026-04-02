from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

import pytest

from soft_skills_backend.config import Settings
from soft_skills_backend.engines.marking import PromptLibrary, TypedLLMResult
from soft_skills_backend.modules.practice.workflows.assessment.marking_provider import (
    DefaultAssessmentMarkingProvider,
    StructuredOutputRejectionError,
    build_aggregation_typed_output,
    build_per_skill_typed_output,
)
from soft_skills_backend.shared.errors import scoring_error
from soft_skills_backend.shared.ports.models import ProviderCompletion, ProviderToolCompletion
from soft_skills_backend.shared.ports.telemetry import ProviderCallContext
from soft_skills_backend.shared.ports.models import ProviderTextChunk


class _StubProvider:
    def __init__(self, model_slug: str) -> None:
        self._model_slug = model_slug

    @property
    def provider_name(self) -> str:
        return "stub"

    @property
    def model_slug(self) -> str:
        return self._model_slug

    async def complete_json(self, **_: object) -> ProviderCompletion:
        raise NotImplementedError

    async def complete_with_tools(self, **_: object) -> ProviderToolCompletion:
        raise NotImplementedError

    def stream_text(self, **_: object) -> AsyncIterator[ProviderTextChunk]:
        raise NotImplementedError


class _RecordingTypedOutput:
    def __init__(self, payloads: list[object]) -> None:
        self.provider_models: list[str] = []
        self.messages_history: list[list[dict[str, object]]] = []
        self._payloads = payloads
        self._index = 0

    async def generate(
        self,
        provider: _StubProvider,
        *,
        messages: list[dict[str, str]],
        call_context: ProviderCallContext,
    ) -> TypedLLMResult:
        del call_context
        self.provider_models.append(provider.model_slug)
        self.messages_history.append(list(messages))
        payload = self._payloads[self._index]
        self._index += 1
        return TypedLLMResult(
            parsed={"value": payload},  # type: ignore[arg-type]
            raw_payload={"value": payload},
            schema_version="v1",
            usage={"total_tokens": 1},
            model_slug=provider.model_slug,
        )


class _RejectingThenSucceedingTypedOutput:
    def __init__(self) -> None:
        self.provider_models: list[str] = []
        self.messages_history: list[list[dict[str, object]]] = []
        self._attempt = 0

    async def generate(
        self,
        provider: _StubProvider,
        *,
        messages: list[dict[str, str]],
        call_context: ProviderCallContext,
    ) -> TypedLLMResult:
        del call_context
        self.provider_models.append(provider.model_slug)
        self.messages_history.append(list(messages))
        if self._attempt == 0:
            self._attempt += 1
            raise StructuredOutputRejectionError(
                app_error=scoring_error(
                    "Provider returned malformed structured output",
                    code="SS-VALIDATION-019",
                ),
                raw_payload={},
            )
        self._attempt += 1
        return TypedLLMResult(
            parsed={"value": "recovered"},  # type: ignore[arg-type]
            raw_payload={"value": "recovered"},
            schema_version="v1",
            usage={"total_tokens": 1},
            model_slug=provider.model_slug,
        )


class _NoOpRubricRepository:
    pass


def _build_provider(
    *,
    verification_retries: int,
    backup_provider: _StubProvider | None = None,
) -> DefaultAssessmentMarkingProvider:
    settings = Settings(
        _env_file=None,  # type: ignore[call-arg]
        assessment_validation_retries=verification_retries,
    )
    return DefaultAssessmentMarkingProvider(
        settings=settings,
        llm_provider=_StubProvider("primary-model"),
        backup_llm_provider=backup_provider,
        prompt_library=PromptLibrary(),
        per_skill_typed_output=_RecordingTypedOutput([]),  # type: ignore[arg-type]
        aggregation_typed_output=_RecordingTypedOutput([]),  # type: ignore[arg-type]
        rubric_repository=_NoOpRubricRepository(),  # type: ignore[arg-type]
    )


def _call_context() -> ProviderCallContext:
    return ProviderCallContext(
        operation="test_assessment",
        request_id="request-id",
        trace_id="trace-id",
        pipeline_run_id="pipeline-id",
        workflow_id="workflow-id",
        user_id="user-id",
    )


def _failing_verifier_factory(failures_before_success: int) -> Any:
    attempts = {"count": 0}

    def verifier(_: object) -> None:
        if attempts["count"] < failures_before_success:
            attempts["count"] += 1
            raise scoring_error(
                "Evidence must quote the learner response directly",
                code="SS-SCORING-004",
            )

    return verifier


@pytest.mark.asyncio
async def test_generate_verified_output_uses_backup_provider_on_final_retry() -> None:
    marker = _build_provider(
        verification_retries=2,
        backup_provider=_StubProvider("backup-model"),
    )
    typed_output = _RecordingTypedOutput(["first", "second", "third"])

    result = await marker._generate_verified_output(
        typed_output=typed_output,  # type: ignore[arg-type]
        messages=[{"role": "user", "content": "score this"}],
        call_context=_call_context(),
        verifier=_failing_verifier_factory(2),
    )

    assert typed_output.provider_models == ["primary-model", "primary-model", "backup-model"]
    assert result.model_slug == "backup-model"
    assert len(typed_output.messages_history) == 3
    assert typed_output.messages_history[1][-1]["role"] == "user"
    assert "failed verification" in str(typed_output.messages_history[1][-1]["content"])


@pytest.mark.asyncio
async def test_generate_verified_output_keeps_primary_provider_without_backup() -> None:
    marker = _build_provider(verification_retries=2)
    typed_output = _RecordingTypedOutput(["first", "second", "third"])

    result = await marker._generate_verified_output(
        typed_output=typed_output,  # type: ignore[arg-type]
        messages=[{"role": "user", "content": "score this"}],
        call_context=_call_context(),
        verifier=_failing_verifier_factory(2),
    )

    assert typed_output.provider_models == ["primary-model", "primary-model", "primary-model"]
    assert result.model_slug == "primary-model"


@pytest.mark.asyncio
async def test_generate_verified_output_does_not_use_backup_when_no_retry_budget() -> None:
    marker = _build_provider(
        verification_retries=0,
        backup_provider=_StubProvider("backup-model"),
    )
    typed_output = _RecordingTypedOutput(["first"])

    with pytest.raises(StructuredOutputRejectionError) as exc_info:
        await marker._generate_verified_output(
            typed_output=typed_output,  # type: ignore[arg-type]
            messages=[{"role": "user", "content": "score this"}],
            call_context=_call_context(),
            verifier=_failing_verifier_factory(1),
        )

    assert typed_output.provider_models == ["primary-model"]
    assert exc_info.value.app_error.code == "SS-SCORING-004"


@pytest.mark.asyncio
async def test_generate_verified_output_stops_before_backup_after_success() -> None:
    marker = _build_provider(
        verification_retries=2,
        backup_provider=_StubProvider("backup-model"),
    )
    typed_output = _RecordingTypedOutput(["first", "second"])

    result = await marker._generate_verified_output(
        typed_output=typed_output,  # type: ignore[arg-type]
        messages=[{"role": "user", "content": "score this"}],
        call_context=_call_context(),
        verifier=_failing_verifier_factory(1),
    )

    assert typed_output.provider_models == ["primary-model", "primary-model"]
    assert result.model_slug == "primary-model"


@pytest.mark.asyncio
async def test_generate_verified_output_retries_structured_output_rejection_and_uses_backup() -> None:
    marker = _build_provider(
        verification_retries=1,
        backup_provider=_StubProvider("backup-model"),
    )
    typed_output = _RejectingThenSucceedingTypedOutput()

    result = await marker._generate_verified_output(
        typed_output=typed_output,  # type: ignore[arg-type]
        messages=[{"role": "user", "content": "score this"}],
        call_context=_call_context(),
        verifier=lambda _: None,
    )

    assert typed_output.provider_models == ["primary-model", "backup-model"]
    assert result.model_slug == "backup-model"
    assert "single JSON object matching the required schema exactly" in str(
        typed_output.messages_history[1][-1]["content"]
    )


def test_assessment_retry_settings_default_to_legacy_value() -> None:
    settings = Settings(
        _env_file=None,  # type: ignore[call-arg]
        assessment_validation_retries=2,
    )

    assert settings.get_assessment_structured_output_retries() == 2
    assert settings.get_assessment_semantic_validation_retries() == 2


def test_assessment_retry_settings_can_be_decoupled() -> None:
    settings = Settings(
        _env_file=None,  # type: ignore[call-arg]
        assessment_validation_retries=1,
        assessment_structured_output_retries=0,
        assessment_semantic_validation_retries=2,
    )

    per_skill_output = build_per_skill_typed_output(settings)
    aggregation_output = build_aggregation_typed_output(settings)
    marker = DefaultAssessmentMarkingProvider(
        settings=settings,
        llm_provider=_StubProvider("primary-model"),
        backup_llm_provider=_StubProvider("backup-model"),
        prompt_library=PromptLibrary(),
        per_skill_typed_output=per_skill_output,
        aggregation_typed_output=aggregation_output,
        rubric_repository=_NoOpRubricRepository(),  # type: ignore[arg-type]
    )

    assert per_skill_output._max_validation_retries == 0
    assert aggregation_output._max_validation_retries == 0
    assert marker._verification_retries == 2
