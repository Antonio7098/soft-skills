"""Smoke test helpers."""

from __future__ import annotations

from soft_skills_backend.config import Settings

from .contracts import SmokeContext, SmokeDefinition, SmokeExecutionResult
from .registry import SmokeRegistry
from .runner import SmokeRunner
from .suites.assessment_marking import (
    InterviewMarkingSmoke,
    QuickPracticeMarkingSmoke,
    ScenarioMarkingSmoke,
)
from .suites.practice_run_lifecycle import PracticeRunLifecycleSmoke
from .suites.practice_session_flow import PracticeSessionFlowSmoke
from .suites.provider_baseline import ProviderBaselineSmoke


def build_default_registry() -> SmokeRegistry:
    """Build the default smoke registry."""

    return SmokeRegistry(
        [
            ProviderBaselineSmoke(),
            QuickPracticeMarkingSmoke(),
            InterviewMarkingSmoke(),
            ScenarioMarkingSmoke(),
            PracticeSessionFlowSmoke(),
            PracticeRunLifecycleSmoke(),
        ]
    )


def build_default_runner(settings: Settings | None = None) -> SmokeRunner:
    """Build the default centralized smoke runner."""

    return SmokeRunner(build_default_registry(), SmokeContext.create(settings))


__all__ = [
    "SmokeContext",
    "SmokeDefinition",
    "SmokeExecutionResult",
    "SmokeRegistry",
    "SmokeRunner",
    "build_default_registry",
    "build_default_runner",
]
