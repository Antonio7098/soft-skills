from __future__ import annotations

from pydantic import BaseModel
import pytest

from soft_skills_backend.engines.marking.use_cases.structured_output import (
    StructuredOutputRejectionError,
    StructuredOutputRepairMode,
    TypedLLMOutput,
)
from soft_skills_backend.shared.ports.models import (
    ProviderCompletion,
    normalize_strict_json_schema,
)
from soft_skills_backend.shared.ports.telemetry import ProviderCallContext


class _SimplePayload(BaseModel):
    ok: bool


class _FakeProvider:
    def __init__(self, responses: list[str | dict[str, object]]) -> None:
        self._responses = responses
        self.calls = 0

    @property
    def provider_name(self) -> str:
        return "test-provider"

    @property
    def model_slug(self) -> str:
        return "test-model"

    async def complete_json(
        self,
        *,
        messages: list[dict[str, str]],
        call_context: ProviderCallContext,
        response_schema=None,
        timeout_seconds=None,
    ) -> ProviderCompletion:
        del messages, call_context, response_schema, timeout_seconds
        self.calls += 1
        response = self._responses.pop(0)
        return ProviderCompletion(content=response, model_slug=self.model_slug)


@pytest.mark.asyncio
async def test_typed_output_fail_fast_does_not_attempt_self_repair() -> None:
    provider = _FakeProvider(['{"wrong": true}', '{"ok": true}'])
    typed_output = TypedLLMOutput(
        _SimplePayload,
        schema_version="test.v1",
        max_validation_retries=1,
        repair_mode=StructuredOutputRepairMode.FAIL_FAST,
        transport_schema_name="simple_payload",
    )

    with pytest.raises(StructuredOutputRejectionError):
        await typed_output.generate(
            provider,
            messages=[{"role": "user", "content": "Return JSON"}],
            call_context=ProviderCallContext(operation="test"),
        )

    assert provider.calls == 1


@pytest.mark.asyncio
async def test_typed_output_self_correct_retries_once() -> None:
    provider = _FakeProvider(['{"wrong": true}', '{"ok": true}'])
    typed_output = TypedLLMOutput(
        _SimplePayload,
        schema_version="test.v1",
        max_validation_retries=1,
        repair_mode=StructuredOutputRepairMode.SELF_CORRECT,
        transport_schema_name="simple_payload",
    )

    result = await typed_output.generate(
        provider,
        messages=[{"role": "user", "content": "Return JSON"}],
        call_context=ProviderCallContext(operation="test"),
    )

    assert result.parsed.ok is True
    assert provider.calls == 2


def test_normalize_strict_json_schema_closes_nested_object_nodes() -> None:
    schema = {
        "type": "object",
        "properties": {
            "ok": {"type": "boolean"},
            "nested": {
                "type": "object",
                "properties": {"name": {"type": "string"}},
            },
        },
        "$defs": {
            "item": {
                "type": "object",
                "properties": {"value": {"type": "number"}},
            }
        },
    }

    normalized = normalize_strict_json_schema(schema)

    assert normalized["additionalProperties"] is False
    assert normalized["properties"]["nested"]["additionalProperties"] is False
    assert normalized["$defs"]["item"]["additionalProperties"] is False
