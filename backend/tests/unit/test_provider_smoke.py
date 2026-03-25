from __future__ import annotations

import pytest

from soft_skills_backend.config import Settings
from soft_skills_backend.domain.errors import AppError
from soft_skills_backend.smoke.provider_baseline import run_provider_smoke


def test_provider_smoke_requires_api_key() -> None:
    with pytest.raises(AppError) as exc_info:
        run_provider_smoke(Settings(provider_api_key=None))

    assert exc_info.value.code == "SS-VALIDATION-002"
