"""Shared smoke support models."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SmokeActors:
    """Registered smoke actors required for backend flows."""

    admin_id: str
    learner_id: str


@dataclass(frozen=True, slots=True)
class PracticeFixtures:
    """Fixture identifiers for seeded practice content."""

    quick_prompt_id: str
    interview_prompt_id: str
    scenario_id: str
