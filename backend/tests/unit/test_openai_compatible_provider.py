from __future__ import annotations

import asyncio

import pytest

from soft_skills_backend.application.ports.telemetry import ProviderCallContext
from soft_skills_backend.config import Settings
from soft_skills_backend.domain.errors import AppError
from soft_skills_backend.integrations.llm.openai_compatible import OpenAICompatibleLLMProvider


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
        "soft_skills_backend.integrations.llm.openai_compatible.httpx.AsyncClient",
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
