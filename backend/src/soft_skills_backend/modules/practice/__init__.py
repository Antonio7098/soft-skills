"""Practice feature package."""

from soft_skills_backend.modules.practice.infra.repository import (
    PracticeRepository,
)
from soft_skills_backend.modules.practice.use_cases.practice_service import (
    PracticeService,
)

__all__ = ["PracticeRepository", "PracticeService"]
