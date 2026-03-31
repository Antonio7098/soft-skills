"""Progression application facade."""

from __future__ import annotations

from sqlalchemy.orm import Session, sessionmaker

from soft_skills_backend.modules.progression.contracts.commands import ProgressRecalculationCommand
from soft_skills_backend.modules.progression.contracts.views import (
    ProgressDashboardView,
    ProgressHistoryView,
    ProgressRecalculationView,
    RecommendationView,
    SkillTimelineView,
)
from soft_skills_backend.modules.progression.infra.repository import ProgressionRepository
from soft_skills_backend.modules.progression.workflows.service import ProgressionWorkflowService
from soft_skills_backend.platform.db.repositories import SqlAlchemyWorkflowEventRepository
from soft_skills_backend.platform.workflows.stageflow_runtime import StageflowRuntime
from soft_skills_backend.shared.auth import Actor


class ProgressionService:
    """Feature facade for read and write progression operations."""

    def __init__(
        self,
        *,
        session_factory: sessionmaker[Session],
        workflow_events: SqlAlchemyWorkflowEventRepository,
        stageflow_runtime: StageflowRuntime,
    ) -> None:
        repository = ProgressionRepository(
            session_factory=session_factory,
            workflow_events=workflow_events,
        )
        self._repository = repository
        self._workflows = ProgressionWorkflowService(
            stageflow_runtime=stageflow_runtime,
            repository=repository,
        )

    async def refresh_from_assessment(
        self,
        *,
        request_id: str,
        trace_id: str,
        workflow_id: str,
        learner_id: str,
        assessment_id: str,
    ) -> ProgressDashboardView:
        return await self._workflows.refresh_from_assessment(
            request_id=request_id,
            trace_id=trace_id,
            workflow_id=workflow_id,
            learner_id=learner_id,
            assessment_id=assessment_id,
        )

    def get_dashboard(self, actor: Actor, learner_id: str) -> ProgressDashboardView:
        return self._repository.get_dashboard(actor, learner_id)

    def get_recommendation(self, actor: Actor, learner_id: str) -> RecommendationView:
        return self._repository.get_recommendation(actor, learner_id)

    def get_progress_history(
        self,
        actor: Actor,
        learner_id: str,
        *,
        from_date: str | None = None,
        to_date: str | None = None,
        limit: int = 100,
    ) -> ProgressHistoryView:
        """Fetch historical progress snapshots for visualization."""
        from datetime import datetime
        from_date_dt = datetime.fromisoformat(from_date) if from_date else None
        to_date_dt = datetime.fromisoformat(to_date) if to_date else None
        return self._repository.get_progress_history(
            actor, learner_id, from_date=from_date_dt, to_date=to_date_dt, limit=limit
        )

    def get_skill_timeline(
        self,
        actor: Actor,
        learner_id: str,
        skill_slug: str,
        *,
        from_date: str | None = None,
        to_date: str | None = None,
        limit: int = 100,
    ) -> SkillTimelineView:
        """Fetch time-series data for a specific skill."""
        from datetime import datetime
        from_date_dt = datetime.fromisoformat(from_date) if from_date else None
        to_date_dt = datetime.fromisoformat(to_date) if to_date else None
        return self._repository.get_skill_timeline(
            actor, learner_id, skill_slug, from_date=from_date_dt, to_date=to_date_dt, limit=limit
        )

    async def recalculate(
        self,
        actor: Actor,
        *,
        request_id: str,
        trace_id: str,
        workflow_id: str,
        command: ProgressRecalculationCommand,
    ) -> ProgressRecalculationView:
        return await self._workflows.recalculate(
            actor=actor,
            request_id=request_id,
            trace_id=trace_id,
            workflow_id=workflow_id,
            command=command,
        )
