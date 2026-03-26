"""Evaluation application facade."""

from __future__ import annotations

from sqlalchemy.orm import Session, sessionmaker

from soft_skills_backend.config import Settings
from soft_skills_backend.modules.evaluation.contracts.commands import EvaluationRunCommand
from soft_skills_backend.modules.evaluation.contracts.views import (
    EvaluationRunView,
    EvaluationSuiteView,
)
from soft_skills_backend.modules.evaluation.infra.repository import EvaluationRepository
from soft_skills_backend.modules.evaluation.use_cases.marking_benchmark import (
    MarkingBenchmarkRunner,
    ProviderFactory,
)
from soft_skills_backend.modules.evaluation.workflows.service import EvaluationWorkflowService
from soft_skills_backend.platform.db.repositories import SqlAlchemyWorkflowEventRepository
from soft_skills_backend.platform.observability.stageflow_logging import DatabaseProviderCallLogger
from soft_skills_backend.platform.workflows.stageflow_runtime import StageflowRuntime
from soft_skills_backend.shared.auth import Actor


class EvaluationService:
    """Feature facade for provider-backed marking evaluations."""

    def __init__(
        self,
        *,
        settings: Settings,
        session_factory: sessionmaker[Session],
        workflow_events: SqlAlchemyWorkflowEventRepository,
        provider_call_logger: DatabaseProviderCallLogger,
        stageflow_runtime: StageflowRuntime,
    ) -> None:
        repository = EvaluationRepository(
            session_factory=session_factory,
            workflow_events=workflow_events,
        )
        self._repository = repository
        self._marking_benchmark = MarkingBenchmarkRunner(
            settings=settings,
            provider_call_logger=provider_call_logger,
        )
        self._workflows = EvaluationWorkflowService(
            stageflow_runtime=stageflow_runtime,
            repository=repository,
            marking_benchmark=self._marking_benchmark,
        )

    def set_provider_factory(self, provider_factory: ProviderFactory) -> None:
        self._marking_benchmark.set_provider_factory(provider_factory)

    def list_suites(self, actor: Actor) -> list[EvaluationSuiteView]:
        del actor
        return self._repository.list_suites()

    def list_runs(self, actor: Actor, *, limit: int = 20) -> list[EvaluationRunView]:
        del actor
        return self._repository.list_runs(limit=limit)

    def get_run(self, actor: Actor, run_id: str) -> EvaluationRunView:
        del actor
        return self._repository.get_run(run_id)

    async def execute(
        self,
        actor: Actor,
        *,
        request_id: str,
        trace_id: str,
        workflow_id: str,
        command: EvaluationRunCommand,
    ) -> EvaluationRunView:
        return await self._workflows.execute(
            actor=actor,
            request_id=request_id,
            trace_id=trace_id,
            workflow_id=workflow_id,
            command=command,
        )
