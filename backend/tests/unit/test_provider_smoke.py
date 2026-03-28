from __future__ import annotations

import asyncio

import pytest

from soft_skills_backend.config import Settings
from soft_skills_backend.platform.providers.llm.openai_compatible import resolve_llm_provider_config
from soft_skills_backend.shared.errors import AppError
from soft_skills_backend.smoke.contracts import SmokeContext
from soft_skills_backend.smoke.suites import provider_baseline
from soft_skills_backend.smoke.suites.provider_baseline import (
    ProviderBaselineSmoke,
    run_provider_smoke,
)


def test_provider_smoke_requires_api_key() -> None:
    with pytest.raises(AppError) as exc_info:
        run_provider_smoke(Settings(_env_file=None, provider_api_key=None, openrouter_api_key=None))  # type: ignore[call-arg]

    assert exc_info.value.code == "SS-VALIDATION-002"


def test_provider_smoke_accepts_openrouter_api_key() -> None:
    settings = Settings(  # type: ignore[call-arg]
        _env_file=None,
        provider_api_key=None,
        OPENROUTER_API_KEY="test-openrouter-key",
        llm_marking_per_skill_model="openrouter/test-model",
    )
    resolved = resolve_llm_provider_config(settings)

    assert resolved.provider_name == "openrouter"
    assert resolved.api_key == "test-openrouter-key"
    assert resolved.model_slug == "openrouter/test-model"


def test_provider_smoke_fails_fast_when_flow_exceeds_budget() -> None:
    class _ReadyPreflight:
        def assert_ready(self, _settings: Settings) -> None:
            return None

        def build_provider(self, _settings: Settings) -> object:
            raise AssertionError("provider should not be built in timeout test")

    class _NeverFinishingSmoke(ProviderBaselineSmoke):
        async def _run(self, _settings: Settings) -> object:  # type: ignore[override]
            await asyncio.sleep(60)
            return object()

    smoke = _NeverFinishingSmoke(preflight=_ReadyPreflight(), flow_timeout_seconds=0.01)  # type: ignore[arg-type]

    with pytest.raises(AppError) as exc_info:
        smoke.run(SmokeContext.create(Settings(_env_file=None)))  # type: ignore[call-arg]

    assert exc_info.value.code == "SS-PROVIDER-012"


def test_provider_smoke_result_shape() -> None:
    result = provider_baseline.ProviderBaselineSmokeResult(
        status="ok",
        provider="openrouter",
        model_slug="test-model",
        response_preview='{"status":"ok"}',
    )

    assert result.status == "ok"
    assert result.provider == "openrouter"
    assert result.model_slug == "test-model"
