from __future__ import annotations

import asyncio

import pytest

from soft_skills_backend.config import Settings
from soft_skills_backend.domain.errors import AppError
from soft_skills_backend.integrations.llm.openai_compatible import resolve_llm_provider_config
from soft_skills_backend.smoke import provider_baseline
from soft_skills_backend.smoke.provider_baseline import run_provider_smoke


def test_provider_smoke_requires_api_key() -> None:
    with pytest.raises(AppError) as exc_info:
        run_provider_smoke(Settings(_env_file=None, provider_api_key=None, openrouter_api_key=None))

    assert exc_info.value.code == "SS-VALIDATION-002"


def test_provider_smoke_accepts_openrouter_api_key() -> None:
    settings = Settings(
        _env_file=None,
        provider_api_key=None,
        OPENROUTER_API_KEY="test-openrouter-key",
        LLM_MARKING_MODEL="openrouter/test-model",
    )
    resolved = resolve_llm_provider_config(settings)

    assert resolved.provider_name == "openrouter"
    assert resolved.api_key == "test-openrouter-key"
    assert resolved.model_slug == "openrouter/test-model"


def test_provider_smoke_fails_fast_when_flow_exceeds_budget(monkeypatch: pytest.MonkeyPatch) -> None:
    class _ConfiguredProvider:
        def assert_configured(self) -> None:
            return None

    async def _never_finishes(_settings: Settings) -> object:
        await asyncio.sleep(60)
        return object()

    monkeypatch.setattr(provider_baseline, "_build_smoke_provider", lambda _settings: _ConfiguredProvider())
    monkeypatch.setattr(provider_baseline, "_run_quick_practice_smoke", _never_finishes)
    monkeypatch.setattr(provider_baseline, "SMOKE_FLOW_TIMEOUT_SECONDS", 0.01)

    with pytest.raises(AppError) as exc_info:
        run_provider_smoke(Settings(_env_file=None))

    assert exc_info.value.code == "SS-PROVIDER-012"
