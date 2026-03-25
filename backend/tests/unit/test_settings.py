from __future__ import annotations

import pytest
from pydantic import ValidationError

from soft_skills_backend.config import Settings


def test_settings_parse_cors_csv() -> None:
    settings = Settings(cors_allowed_origins="https://a.example, https://b.example")
    assert settings.cors_allowed_origins == ("https://a.example", "https://b.example")


def test_settings_reject_zero_event_queue_size() -> None:
    with pytest.raises(ValidationError):
        Settings(stageflow_event_queue_size=0)


def test_settings_support_openrouter_aliases(monkeypatch) -> None:
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-openrouter-key")
    monkeypatch.setenv("LLM_MARKING_MODEL", "openrouter/test-model")
    monkeypatch.setenv("LLM_MARKING_MODEL_BACKUP", "qwen/qwen3.5-9b")

    settings = Settings(_env_file=None)

    assert settings.openrouter_api_key == "test-openrouter-key"
    assert settings.llm_marking_model == "openrouter/test-model"
    assert settings.llm_marking_model_backup == "qwen/qwen3.5-9b"
