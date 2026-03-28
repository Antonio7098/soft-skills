from __future__ import annotations

import pytest
from pydantic import ValidationError

from soft_skills_backend.config import Settings


def test_settings_parse_cors_csv() -> None:
    settings = Settings(cors_allowed_origins="https://a.example, https://b.example")  # type: ignore[arg-type]
    assert settings.cors_allowed_origins == ("https://a.example", "https://b.example")


def test_settings_reject_zero_event_queue_size() -> None:
    with pytest.raises(ValidationError):
        Settings(stageflow_event_queue_size=0)


def test_settings_support_openrouter_aliases(monkeypatch) -> None:
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-openrouter-key")
    monkeypatch.setenv(
        "SOFT_SKILLS_LLM_MARKING_PER_SKILL_MODEL",
        "openrouter/test-model",
    )
    monkeypatch.setenv(
        "SOFT_SKILLS_LLM_DEFAULT_BACKUP_MODEL",
        "qwen/qwen3.5-9b",
    )

    settings = Settings(_env_file=None)  # type: ignore[call-arg]

    assert settings.openrouter_api_key == "test-openrouter-key"
    assert settings.llm_marking_per_skill_model == "openrouter/test-model"
    assert settings.llm_default_backup_model == "qwen/qwen3.5-9b"
