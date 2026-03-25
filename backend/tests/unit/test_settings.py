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
