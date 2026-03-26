"""Progression feature package."""

from soft_skills_backend.modules.progression.contracts.commands import (
    ProgressRecalculationCommand,
)
from soft_skills_backend.modules.progression.contracts.views import (
    ProgressDashboardView,
    ProgressRecalculationView,
    ProgressSnapshotView,
    RecommendationView,
)
from soft_skills_backend.modules.progression.use_cases.progression_service import (
    ProgressionService,
)

__all__ = [
    "ProgressDashboardView",
    "ProgressRecalculationCommand",
    "ProgressRecalculationView",
    "ProgressSnapshotView",
    "ProgressionService",
    "RecommendationView",
]
