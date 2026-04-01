from __future__ import annotations

import asyncio

import pytest

from soft_skills_backend.config import LLMTaskKind, Settings
from soft_skills_backend.platform.providers.llm.openai_compatible import (
    OpenAICompatibleLLMProvider,
    _build_json_response_format,
    resolve_llm_provider_config,
)
from soft_skills_backend.shared.ports.models import JsonSchemaResponseFormat
from soft_skills_backend.shared.errors import AppError
from soft_skills_backend.shared.ports.telemetry import ProviderCallContext


class _NoOpProviderCallLogger:
    async def log_call_start(self, **_: object) -> str:
        return "call-id"

    async def log_call_end(self, _call_id: object, **_: object) -> None:
        return None


def test_build_json_response_format_disables_strict_mode_for_groq() -> None:
    response_format = JsonSchemaResponseFormat(
        name="test",
        schema={
            "type": "object",
            "properties": {
                "required_field": {"type": "string"},
                "optional_field": {"type": "string"},
            },
            "required": ["required_field"],
        },
        strict=True,
    )

    payload = _build_json_response_format(response_format, provider_name="groq")

    assert payload["type"] == "json_schema"
    assert payload["json_schema"]["strict"] is False

    openai_payload = _build_json_response_format(response_format, provider_name="openai")
    assert openai_payload["json_schema"]["strict"] is True


@pytest.mark.asyncio
async def test_openai_compatible_provider_enforces_total_timeout(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class _SlowAsyncClient:
        def __init__(self, **_: object) -> None:
            return None

        async def __aenter__(self) -> _SlowAsyncClient:
            return self

        async def __aexit__(self, exc_type, exc, tb) -> None:
            return None

        async def post(self, *_args: object, **_kwargs: object) -> object:
            await asyncio.sleep(60)
            raise AssertionError("timeout should fire before post returns")

    monkeypatch.setattr(
        "soft_skills_backend.platform.providers.llm.openai_compatible.httpx.AsyncClient",
        _SlowAsyncClient,
    )

    provider = OpenAICompatibleLLMProvider(
        settings=Settings(
            _env_file=None,  # type: ignore[call-arg]
            provider_api_key="test-key",
            provider_base_url="https://example.com/v1",
            llm_default_model="test-model",
            smoke_timeout_seconds=0.01,
            provider_max_retries=0,
        ),
        provider_call_logger=_NoOpProviderCallLogger(),
    )

    with pytest.raises(AppError) as exc_info:
        await provider.complete_json(
            messages=[{"role": "user", "content": "Return JSON"}],
            call_context=ProviderCallContext(
                operation="test",
                request_id="request-id",
                trace_id="trace-id",
                pipeline_run_id="pipeline-id",
                workflow_id="workflow-id",
                user_id="user-id",
            ),
        )

    assert exc_info.value.code == "SS-PROVIDER-005"


@pytest.mark.asyncio
async def test_openai_compatible_provider_switches_to_backup_model_on_third_attempt(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    requested_models: list[str] = []

    class _Response:
        def __init__(self, status_code: int, payload: dict[str, object]) -> None:
            self.status_code = status_code
            self._payload = payload

        def json(self) -> dict[str, object]:
            return self._payload

    class _RetryingAsyncClient:
        call_count = 0

        def __init__(self, **_: object) -> None:
            return None

        async def __aenter__(self) -> _RetryingAsyncClient:
            return self

        async def __aexit__(self, exc_type, exc, tb) -> None:
            return None

        async def post(self, *_args: object, **kwargs: object) -> _Response:
            json_payload = kwargs["json"]
            assert isinstance(json_payload, dict)
            requested_models.append(str(json_payload["model"]))
            _RetryingAsyncClient.call_count += 1
            if _RetryingAsyncClient.call_count < 3:
                return _Response(503, {"error": {"message": "temporary outage"}})
            return _Response(
                200,
                {
                    "model": json_payload["model"],
                    "choices": [{"message": {"content": '{"ok": true}'}}],
                    "usage": {"total_tokens": 1},
                },
            )

    monkeypatch.setattr(
        "soft_skills_backend.platform.providers.llm.openai_compatible.httpx.AsyncClient",
        _RetryingAsyncClient,
    )

    provider = OpenAICompatibleLLMProvider(
        settings=Settings(
            _env_file=None,  # type: ignore[call-arg]
            provider_api_key="test-key",
            provider_base_url="https://example.com/v1",
            llm_default_model="primary-model",
            llm_default_backup_model="backup-model",
            provider_max_retries=2,
        ),
        provider_call_logger=_NoOpProviderCallLogger(),
    )

    completion = await provider.complete_json(
        messages=[{"role": "user", "content": "Return JSON"}],
        call_context=ProviderCallContext(
            operation="test",
            request_id="request-id",
            trace_id="trace-id",
            pipeline_run_id="pipeline-id",
            workflow_id="workflow-id",
            user_id="user-id",
        ),
    )

    assert requested_models == ["primary-model", "primary-model", "backup-model"]
    assert completion.model_slug == "backup-model"


@pytest.mark.asyncio
async def test_assistant_provider_switches_to_backup_model_on_first_retry(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    requested_models: list[str] = []

    class _Response:
        def __init__(self, status_code: int, payload: dict[str, object]) -> None:
            self.status_code = status_code
            self._payload = payload

        def json(self) -> dict[str, object]:
            return self._payload

    class _RetryingAsyncClient:
        call_count = 0

        def __init__(self, **_: object) -> None:
            return None

        async def __aenter__(self) -> _RetryingAsyncClient:
            return self

        async def __aexit__(self, exc_type, exc, tb) -> None:
            return None

        async def post(self, *_args: object, **kwargs: object) -> _Response:
            payload = kwargs["json"]
            assert isinstance(payload, dict)
            requested_models.append(str(payload["model"]))
            _RetryingAsyncClient.call_count += 1
            if _RetryingAsyncClient.call_count == 1:
                return _Response(503, {"error": {"message": "temporary outage"}})
            return _Response(
                200,
                {
                    "model": payload["model"],
                    "choices": [{"message": {"content": '{"ok": true}'}}],
                    "usage": {"total_tokens": 1},
                },
            )

    monkeypatch.setattr(
        "soft_skills_backend.platform.providers.llm.openai_compatible.httpx.AsyncClient",
        _RetryingAsyncClient,
    )

    provider = OpenAICompatibleLLMProvider(
        settings=Settings(
            _env_file=None,  # type: ignore[call-arg]
            provider_api_key="test-key",
            provider_base_url="https://example.com/v1",
            llm_default_model="primary-model",
            llm_assistant_model="primary-model",
            llm_default_backup_model="backup-model",
            provider_max_retries=2,
            llm_assistant_max_retries=1,
        ),
        provider_call_logger=_NoOpProviderCallLogger(),
        task=LLMTaskKind.ASSISTANT,
    )

    completion = await provider.complete_json(
        messages=[{"role": "user", "content": "Return JSON"}],
        call_context=ProviderCallContext(operation="test"),
    )

    assert requested_models == ["primary-model", "backup-model"]
    assert completion.model_slug == "backup-model"


@pytest.mark.asyncio
async def test_openai_compatible_provider_uses_json_schema_response_format_when_supplied(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured_payloads: list[dict[str, object]] = []

    class _Response:
        def __init__(self, payload: dict[str, object]) -> None:
            self.status_code = 200
            self._payload = payload

        def json(self) -> dict[str, object]:
            return self._payload

    class _CapturingAsyncClient:
        def __init__(self, **_: object) -> None:
            return None

        async def __aenter__(self) -> _CapturingAsyncClient:
            return self

        async def __aexit__(self, exc_type, exc, tb) -> None:
            return None

        async def post(self, *_args: object, **kwargs: object) -> _Response:
            payload = kwargs["json"]
            assert isinstance(payload, dict)
            captured_payloads.append(payload)
            return _Response(
                {
                    "model": payload["model"],
                    "choices": [{"message": {"content": '{"ok": true}'}}],
                    "usage": {"total_tokens": 1},
                }
            )

    monkeypatch.setattr(
        "soft_skills_backend.platform.providers.llm.openai_compatible.httpx.AsyncClient",
        _CapturingAsyncClient,
    )

    provider = OpenAICompatibleLLMProvider(
        settings=Settings(
            _env_file=None,  # type: ignore[call-arg]
            provider_name="openai",
            provider_api_key="test-key",
            provider_base_url="https://example.com/v1",
            llm_default_model="test-model",
            provider_max_retries=0,
        ),
        provider_call_logger=_NoOpProviderCallLogger(),
    )

    await provider.complete_json(
        messages=[{"role": "user", "content": "Return JSON"}],
        call_context=ProviderCallContext(
            operation="test",
            request_id="request-id",
            trace_id="trace-id",
            pipeline_run_id="pipeline-id",
            workflow_id="workflow-id",
            user_id="user-id",
        ),
        response_schema=JsonSchemaResponseFormat(
            name="test_contract",
            schema={"type": "object", "properties": {"ok": {"type": "boolean"}}, "required": ["ok"]},
        ),
        timeout_seconds=5,
    )

    assert captured_payloads
    assert captured_payloads[0]["response_format"] == {
        "type": "json_schema",
        "json_schema": {
            "name": "test_contract",
            "strict": True,
            "schema": {
                "type": "object",
                "properties": {"ok": {"type": "boolean"}},
                "required": ["ok"],
                "additionalProperties": False,
            },
        },
    }


@pytest.mark.asyncio
async def test_openai_compatible_provider_requires_parameters_for_openrouter_structured_output(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured_payloads: list[dict[str, object]] = []

    class _Response:
        def __init__(self, payload: dict[str, object]) -> None:
            self.status_code = 200
            self._payload = payload

        def json(self) -> dict[str, object]:
            return self._payload

    class _CapturingAsyncClient:
        def __init__(self, **_: object) -> None:
            return None

        async def __aenter__(self) -> _CapturingAsyncClient:
            return self

        async def __aexit__(self, exc_type, exc, tb) -> None:
            return None

        async def post(self, *_args: object, **kwargs: object) -> _Response:
            payload = kwargs["json"]
            assert isinstance(payload, dict)
            captured_payloads.append(payload)
            return _Response(
                {
                    "model": payload["model"],
                    "choices": [{"message": {"content": '{"ok": true}'}}],
                    "usage": {"total_tokens": 1},
                }
            )

    monkeypatch.setattr(
        "soft_skills_backend.platform.providers.llm.openai_compatible.httpx.AsyncClient",
        _CapturingAsyncClient,
    )

    provider = OpenAICompatibleLLMProvider(
        settings=Settings(
            _env_file=None,  # type: ignore[call-arg]
            provider_name="openrouter",
            provider_api_key="test-key",
            provider_base_url="https://openrouter.ai/api/v1",
            llm_default_model="test-model",
            provider_max_retries=0,
        ),
        provider_call_logger=_NoOpProviderCallLogger(),
    )

    await provider.complete_json(
        messages=[{"role": "user", "content": "Return JSON"}],
        call_context=ProviderCallContext(
            operation="test",
            request_id="request-id",
            trace_id="trace-id",
            pipeline_run_id="pipeline-id",
            workflow_id="workflow-id",
            user_id="user-id",
        ),
        response_schema=JsonSchemaResponseFormat(
            name="test_contract",
            schema={"type": "object", "properties": {"ok": {"type": "boolean"}}, "required": ["ok"]},
        ),
    )

    assert captured_payloads[0]["provider"] == {"require_parameters": True}


def test_resolve_llm_provider_config_uses_task_specific_model() -> None:
    settings = Settings(
        _env_file=None,  # type: ignore[call-arg]
        provider_api_key="test-key",
        llm_default_model="default-model",
        llm_assistant_model="assistant-model",
        llm_admin_agent_model="admin-model",
    )

    assistant = resolve_llm_provider_config(settings, LLMTaskKind.ASSISTANT)
    admin_agent = resolve_llm_provider_config(settings, LLMTaskKind.ADMIN_AGENT)
    generic = resolve_llm_provider_config(settings, None)

    assert assistant.model_slug == "assistant-model"
    assert admin_agent.model_slug == "admin-model"
    assert generic.model_slug == "default-model"
