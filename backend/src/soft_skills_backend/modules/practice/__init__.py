"""Practice feature package."""

from soft_skills_backend.modules.practice.infra.repository import (
    QuickPracticeRepository,
)
from soft_skills_backend.modules.practice.use_cases.text_practice_service import (
    QuickPracticeService,
)

__all__ = ["QuickPracticeRepository", "QuickPracticeService"]
