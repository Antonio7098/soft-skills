"""Composition root."""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from soft_skills_backend.config import Settings
from soft_skills_backend.entrypoints.http.health import HealthService
from soft_skills_backend.modules.catalog import CatalogService
from soft_skills_backend.modules.identity import IdentityService
from soft_skills_backend.modules.practice import (
    QuickPracticeRepository,
    QuickPracticeService,
)
from soft_skills_backend.modules.practice.workflows.assessment import (
    DefaultQuickPracticeMarkingProvider,
    build_prompt_library,
    build_typed_output,
)
from soft_skills_backend.modules.progression import ProgressionService
from soft_skills_backend.modules.taxonomy import TaxonomyService
from soft_skills_backend.platform.db.repositories import (
    SqlAlchemyPipelineRunRepository,
    SqlAlchemyProviderCallRepository,
    SqlAlchemyWorkflowEventRepository,
)
from soft_skills_backend.platform.db.session import (
    create_engine_from_settings,
    create_session_factory,
)
from soft_skills_backend.platform.observability.event_sink import DurableEventSink
from soft_skills_backend.platform.observability.stageflow_logging import DatabaseProviderCallLogger
from soft_skills_backend.platform.providers.llm.openai_compatible import (
    OpenAICompatibleLLMProvider,
)
from soft_skills_backend.platform.workflows.stageflow_runtime import (
    StageflowRuntime,
    build_stageflow_runtime,
)
from soft_skills_backend.shared.auth import HeaderAuthProvider


@dataclass(slots=True)
class AppContainer:
    """Resolved service graph."""

    settings: Settings
    engine: Engine
    session_factory: sessionmaker[Session]
    health_service: HealthService
    auth_provider: HeaderAuthProvider
    identity_service: IdentityService
    taxonomy_service: TaxonomyService
    catalog_service: CatalogService
    practice_service: QuickPracticeService
    progression_service: ProgressionService
    workflow_events: SqlAlchemyWorkflowEventRepository
    pipeline_runs: SqlAlchemyPipelineRunRepository
    provider_calls: SqlAlchemyProviderCallRepository
    stageflow_runtime: StageflowRuntime

    def dispose(self) -> None:
        """Clean up infrastructure resources."""

        self.engine.dispose()


def build_container(settings: Settings) -> AppContainer:
    """Build the application composition root."""

    engine = create_engine_from_settings(settings)
    session_factory = create_session_factory(engine)
    workflow_events = SqlAlchemyWorkflowEventRepository(session_factory)
    pipeline_runs = SqlAlchemyPipelineRunRepository(session_factory)
    provider_calls = SqlAlchemyProviderCallRepository(session_factory)
    durable_event_sink = DurableEventSink(workflow_events)
    stageflow_runtime = build_stageflow_runtime(
        settings,
        event_sink=durable_event_sink,
        pipeline_runs=pipeline_runs,
        provider_calls=provider_calls,
    )
    auth_provider = HeaderAuthProvider(session_factory)
    identity_service = IdentityService(
        session_factory=session_factory,
        workflow_events=workflow_events,
    )
    taxonomy_service = TaxonomyService(
        session_factory=session_factory,
        workflow_events=workflow_events,
    )
    provider_call_logger = DatabaseProviderCallLogger(provider_calls)
    llm_provider = OpenAICompatibleLLMProvider(
        settings=settings,
        provider_call_logger=provider_call_logger,
    )
    catalog_service = CatalogService(
        settings=settings,
        session_factory=session_factory,
        workflow_events=workflow_events,
        llm_provider=llm_provider,
        stageflow_runtime=stageflow_runtime,
    )
    progression_service = ProgressionService(
        session_factory=session_factory,
        workflow_events=workflow_events,
        stageflow_runtime=stageflow_runtime,
    )
    practice_store = QuickPracticeRepository(
        settings=settings,
        session_factory=session_factory,
        workflow_events=workflow_events,
    )
    practice_service = QuickPracticeService(
        stageflow_runtime=stageflow_runtime,
        store=practice_store,
        assessment_marker=DefaultQuickPracticeMarkingProvider(
            settings=settings,
            llm_provider=llm_provider,
            prompt_library=build_prompt_library(settings),
            typed_output=build_typed_output(settings),
        ),
        progression_service=progression_service,
    )
    health_service = HealthService(
        settings=settings,
        session_factory=session_factory,
        stageflow_runtime=stageflow_runtime,
    )
    return AppContainer(
        settings=settings,
        engine=engine,
        session_factory=session_factory,
        health_service=health_service,
        auth_provider=auth_provider,
        identity_service=identity_service,
        taxonomy_service=taxonomy_service,
        catalog_service=catalog_service,
        practice_service=practice_service,
        progression_service=progression_service,
        workflow_events=workflow_events,
        pipeline_runs=pipeline_runs,
        provider_calls=provider_calls,
        stageflow_runtime=stageflow_runtime,
    )
