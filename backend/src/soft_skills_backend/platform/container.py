"""Composition root."""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from soft_skills_backend.config import Settings
from soft_skills_backend.engines.marking.domain.rubric_repository import (
    SqlAlchemyRubricRepository,
)
from soft_skills_backend.entrypoints.http.health import HealthService
from soft_skills_backend.modules.admin import AdminService
from soft_skills_backend.modules.admin.domain.prompt_registry import PromptRegistry
from soft_skills_backend.modules.admin.infra.prompt_repository import PromptRepository
from soft_skills_backend.modules.assistant import AssistantService
from soft_skills_backend.modules.assistant.infra.realtime import AssistantRealtimeBroker
from soft_skills_backend.modules.assistant.infra.repository import AssistantRepository
from soft_skills_backend.modules.assistant.workflows.service import AssistantWorkflowService
from soft_skills_backend.modules.catalog import CatalogService
from soft_skills_backend.modules.catalog.infra.realtime import GenerationRealtimeBroker
from soft_skills_backend.modules.evaluation import EvaluationService
from soft_skills_backend.modules.events import EventsService
from soft_skills_backend.modules.identity import IdentityService
from soft_skills_backend.modules.organisations import OrganisationService
from soft_skills_backend.modules.practice import (
    PracticeRepository,
    PracticeService,
)
from soft_skills_backend.modules.practice.workflows.assessment import (
    DefaultAssessmentMarkingProvider,
    build_aggregation_typed_output,
    build_per_skill_typed_output,
    build_prompt_library,
)
from soft_skills_backend.modules.progression import ProgressionService
from soft_skills_backend.modules.taxonomy import TaxonomyService
from soft_skills_backend.platform.background_tasks import BackgroundTaskRunner
from soft_skills_backend.platform.db.repositories import (
    SqlAlchemyPipelineDefinitionRepository,
    SqlAlchemyPipelineExecutionTraceRepository,
    SqlAlchemyPipelineRunRepository,
    SqlAlchemyProviderCallRepository,
    SqlAlchemyStageDefinitionRepository,
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
from soft_skills_backend.shared.auth import AuthAdapter, HeaderAuthProvider


@dataclass(slots=True)
class AppContainer:
    """Resolved service graph."""

    settings: Settings
    engine: Engine
    session_factory: sessionmaker[Session]
    health_service: HealthService
    auth_provider: AuthAdapter
    identity_service: IdentityService
    admin_service: AdminService
    taxonomy_service: TaxonomyService
    assistant_service: AssistantService
    assistant_broker: AssistantRealtimeBroker
    generation_broker: GenerationRealtimeBroker
    catalog_service: CatalogService
    evaluation_service: EvaluationService
    practice_service: PracticeService
    progression_service: ProgressionService
    events_service: EventsService
    organisation_service: OrganisationService
    workflow_events: SqlAlchemyWorkflowEventRepository
    pipeline_runs: SqlAlchemyPipelineRunRepository
    provider_calls: SqlAlchemyProviderCallRepository
    pipeline_definitions: SqlAlchemyPipelineDefinitionRepository
    stage_definitions: SqlAlchemyStageDefinitionRepository
    pipeline_execution_traces: SqlAlchemyPipelineExecutionTraceRepository
    stageflow_runtime: StageflowRuntime
    background_tasks: BackgroundTaskRunner

    async def shutdown(self) -> None:
        """Clean up async infrastructure resources."""

        runtime_objects = self.stageflow_runtime.runtime_objects or {}
        event_sink = runtime_objects.get("event_sink")
        if event_sink is not None:
            stop = getattr(event_sink, "stop", None)
            if callable(stop):
                await stop(drain=True)

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
    pipeline_definitions = SqlAlchemyPipelineDefinitionRepository(session_factory)
    stage_definitions = SqlAlchemyStageDefinitionRepository(session_factory)
    pipeline_execution_traces = SqlAlchemyPipelineExecutionTraceRepository(session_factory)
    background_tasks = BackgroundTaskRunner()
    durable_event_sink = DurableEventSink(workflow_events)
    stageflow_runtime = build_stageflow_runtime(
        settings,
        event_sink=durable_event_sink,
        pipeline_runs=pipeline_runs,
        provider_calls=provider_calls,
        workflow_events=workflow_events,
        execution_trace_repository=pipeline_execution_traces,
    )
    auth_provider = HeaderAuthProvider(session_factory, workflow_events=workflow_events)
    prompt_repository = PromptRepository(session_factory)
    prompt_registry = PromptRegistry(settings=settings, prompts=prompt_repository)
    identity_service = IdentityService(
        session_factory=session_factory,
        workflow_events=workflow_events,
    )
    admin_service = AdminService(
        settings=settings,
        session_factory=session_factory,
        workflow_events=workflow_events,
        prompt_repository=prompt_repository,
        pipeline_definitions=pipeline_definitions,
        stage_definitions=stage_definitions,
        pipeline_execution_traces=pipeline_execution_traces,
        pipeline_runs=pipeline_runs,
    )
    taxonomy_service = TaxonomyService(
        session_factory=session_factory,
        workflow_events=workflow_events,
    )
    assistant_broker = AssistantRealtimeBroker()
    generation_broker = GenerationRealtimeBroker()
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
        prompt_registry=prompt_registry,
        stageflow_runtime=stageflow_runtime,
        generation_broker=generation_broker,
    )
    evaluation_service = EvaluationService(
        settings=settings,
        session_factory=session_factory,
        workflow_events=workflow_events,
        provider_call_logger=provider_call_logger,
        stageflow_runtime=stageflow_runtime,
    )
    progression_service = ProgressionService(
        session_factory=session_factory,
        workflow_events=workflow_events,
        stageflow_runtime=stageflow_runtime,
    )
    rubric_repository = SqlAlchemyRubricRepository(session_factory)
    practice_store = PracticeRepository(
        settings=settings,
        session_factory=session_factory,
        workflow_events=workflow_events,
    )
    practice_service = PracticeService(
        stageflow_runtime=stageflow_runtime,
        store=practice_store,
        assessment_marker=DefaultAssessmentMarkingProvider(
            settings=settings,
            llm_provider=llm_provider,
            prompt_library=build_prompt_library(settings),
            per_skill_typed_output=build_per_skill_typed_output(settings),
            aggregation_typed_output=build_aggregation_typed_output(settings),
            rubric_repository=rubric_repository,
        ),
        rubric_repository=rubric_repository,
        progression_service=progression_service,
    )
    assistant_repository = AssistantRepository(
        session_factory=session_factory,
        workflow_events=workflow_events,
    )
    assistant_service = AssistantService(
        repository=assistant_repository,
        workflows=AssistantWorkflowService(
            llm_provider=llm_provider,
            repository=assistant_repository,
            broker=assistant_broker,
            catalog_service=catalog_service,
            practice_service=practice_service,
            progression_service=progression_service,
            stageflow_runtime=stageflow_runtime,
            prompt_registry=prompt_registry,
            settings=settings,
        ),
        background_tasks=background_tasks,
    )
    health_service = HealthService(
        settings=settings,
        session_factory=session_factory,
        stageflow_runtime=stageflow_runtime,
    )
    events_service = EventsService(workflow_events=workflow_events)
    organisation_service = OrganisationService(
        session_factory=session_factory,
        workflow_events=workflow_events,
    )
    return AppContainer(
        settings=settings,
        engine=engine,
        session_factory=session_factory,
        health_service=health_service,
        auth_provider=auth_provider,
        identity_service=identity_service,
        admin_service=admin_service,
        taxonomy_service=taxonomy_service,
        assistant_service=assistant_service,
        assistant_broker=assistant_broker,
        generation_broker=generation_broker,
        catalog_service=catalog_service,
        evaluation_service=evaluation_service,
        practice_service=practice_service,
        progression_service=progression_service,
        events_service=events_service,
        organisation_service=organisation_service,
        workflow_events=workflow_events,
        pipeline_runs=pipeline_runs,
        provider_calls=provider_calls,
        pipeline_definitions=pipeline_definitions,
        stage_definitions=stage_definitions,
        pipeline_execution_traces=pipeline_execution_traces,
        stageflow_runtime=stageflow_runtime,
        background_tasks=background_tasks,
    )
