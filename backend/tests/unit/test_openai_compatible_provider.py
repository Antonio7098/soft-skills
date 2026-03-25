from __future__ import annotations

import asyncio

import pytest

from soft_skills_backend.shared.ports.telemetry import ProviderCallContext
from soft_skills_backend.config import Settings
from soft_skills_backend.shared.errors import AppError
from soft_skills_backend.platform.providers.llm.openai_compatible import OpenAICompatibleLLMProvider


class _NoOpProviderCallLogger:
    async def log_call_start(self, **_: object) -> str:
        return "call-id"

    async def log_call_end(self, _call_id: object, **_: object) -> None:
        return None


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
            _env_file=None,
            provider_api_key="test-key",
            provider_base_url="https://example.com/v1",
            provider_model_slug="test-model",
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
            requested_models.append(str(kwargs["json"]["model"]))
            _RetryingAsyncClient.call_count += 1
            if _RetryingAsyncClient.call_count < 3:
                return _Response(503, {"error": {"message": "temporary outage"}})
            return _Response(
                200,
                {
                    "model": kwargs["json"]["model"],
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
            _env_file=None,
            provider_api_key="test-key",
            provider_base_url="https://example.com/v1",
            provider_model_slug="primary-model",
            llm_marking_model_backup="backup-model",
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
