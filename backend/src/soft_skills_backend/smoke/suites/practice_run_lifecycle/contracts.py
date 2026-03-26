"""Practice-run lifecycle smoke contracts."""

from __future__ import annotations

from pydantic import BaseModel


class PracticeRunLifecycleCheckpointResult(BaseModel):
    status: str
    completed_items: int
    validated_items: int
    failed_items: int
    current_attempt_id: str | None
    validated_attempt_count: int
    failed_attempt_count: int
    overall_score_average: float | None


class PracticeRunHistoryEntrySmokeResult(BaseModel):
    run_id: str
    status: str
    overall_score_average: float | None
    practice_types: list[str]


class PracticeRunLifecycleSmokeResult(BaseModel):
    status: str
    run_id: str
    total_items: int
    started: PracticeRunLifecycleCheckpointResult
    in_progress: PracticeRunLifecycleCheckpointResult
    completed: PracticeRunLifecycleCheckpointResult
    score_distribution: dict[str, int]
    skill_slugs: list[str]
    practice_types: list[str]
    history_entry: PracticeRunHistoryEntrySmokeResult
