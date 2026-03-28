"""Provider-backed creator generation service facade."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from sqlalchemy.orm import Session, sessionmaker
from stageflow.agent.security import PromptSecurityError, PromptSecurityPolicy

from soft_skills_backend.config import Settings
from soft_skills_backend.engines.config import load_catalog_generation_runtime_config
from soft_skills_backend.modules.admin.domain.prompt_registry import PromptRegistry
from soft_skills_backend.modules.catalog.contracts.collection_commands import (
    ChatCollectionGenerationCommand,
    StructuredCollectionGenerationCommand,
)
from soft_skills_backend.modules.catalog.contracts.collection_views import CollectionGenerationView
from soft_skills_backend.modules.catalog.contracts.prompt_item_commands import (
    ChatPromptItemGenerationCommand,
    StructuredPromptItemGenerationCommand,
)
from soft_skills_backend.modules.catalog.contracts.prompt_item_views import PromptItemGenerationView
from soft_skills_backend.modules.catalog.contracts.stream import (
    GenerationStage,
    GenerationStreamEvent,
)
from soft_skills_backend.modules.catalog.domain.models import (
    GeneratedCollectionBlueprint,
    GeneratedPromptItemDraft,
    GeneratedPromptItemPlanBatch,
    GeneratedScenarioDraft,
)
from soft_skills_backend.platform.observability.events import WorkflowEventRecorder
from soft_skills_backend.modules.catalog.infra.realtime import (
    GenerationExecution,
    GenerationRealtimeBroker,
)
from soft_skills_backend.modules.catalog.workflows.generation.collection_pipeline import (
    generate_collection,
)
from soft_skills_backend.modules.catalog.workflows.generation.prompt_item_pipeline import (
    generate_prompt_items_for_collection,
)
from soft_skills_backend.modules.practice.workflows.assessment import TypedLLMOutput
from soft_skills_backend.platform.db.models import RubricRecord
from soft_skills_backend.platform.workflows.stageflow import StageflowPipelineSupport
from soft_skills_backend.platform.workflows.stageflow_runtime import StageflowRuntime
from soft_skills_backend.shared.auth import Actor
from soft_skills_backend.shared.errors import validation_error
from soft_skills_backend.shared.ports.llm import LLMProvider


@dataclass(frozen=True, slots=True)
class GenerationStartedView:
    generation_id: str
    stream_token: str
    mode: str


class CatalogGenerationService:
    """Generate draft collections and prompt items through typed Stageflow workflows."""

    def __init__(
        self,
        *,
        settings: Settings,
        session_factory: sessionmaker[Session],
        events: WorkflowEventRecorder,
        llm_provider: LLMProvider,
        prompt_security_policy: PromptSecurityPolicy,
        prompt_registry: PromptRegistry,
        stageflow_runtime: StageflowRuntime,
        broker: GenerationRealtimeBroker | None = None,
    ) -> None:
        self._settings = settings
        self._session_factory = session_factory
        self._events = events
        self._llm_provider = llm_provider
        self._prompt_security_policy = prompt_security_policy
        self._prompt_registry = prompt_registry
        self._stageflow = StageflowPipelineSupport.from_runtime(stageflow_runtime)
        self._config = load_catalog_generation_runtime_config()
        self._blueprint_output = TypedLLMOutput(
            GeneratedCollectionBlueprint,
            schema_version=self._config.output_schema_version,
            max_validation_retries=settings.creator_generation_validation_retries,
        )
        self._prompt_item_plan_output = TypedLLMOutput(
            GeneratedPromptItemPlanBatch,
            schema_version=self._config.output_schema_version,
            max_validation_retries=settings.creator_generation_validation_retries,
        )
        self._prompt_item_worker_output = TypedLLMOutput(
            GeneratedPromptItemDraft,
            schema_version=self._config.output_schema_version,
            max_validation_retries=settings.creator_generation_validation_retries,
        )
        self._scenario_worker_output = TypedLLMOutput(
            GeneratedScenarioDraft,
            schema_version=self._config.output_schema_version,
            max_validation_retries=settings.creator_generation_validation_retries,
        )
        self._broker = broker

    def _make_progress_callback(self, execution: GenerationExecution) -> Any:
        sequence = {"value": 0}

        def callback(stage: str, progress: float, summary: dict[str, Any]) -> None:
            event = GenerationStreamEvent(
                event_id=uuid4().hex,
                generation_id=execution.generation_id,
                type="progress",
                stage=GenerationStage(stage),
                sequence_number=sequence["value"],
                emitted_at=datetime.now(UTC),
                progress_percent=progress,
                payload=summary,
            )
            sequence["value"] += 1
            if self._broker is not None:
                import asyncio

                try:
                    loop = asyncio.get_running_loop()
                    loop.create_task(self._broker.publish(execution.stream_token, event))
                except RuntimeError:
                    pass

        return callback

    async def generate_structured_draft(
        self,
        actor: Actor,
        *,
        request_id: str,
        trace_id: str,
        workflow_id: str | None,
        command: StructuredCollectionGenerationCommand,
    ) -> CollectionGenerationView:
        return await generate_collection(
            actor=actor,
            request_id=request_id,
            trace_id=trace_id,
            workflow_id=workflow_id,
            mode="structured",
            structured_command=command,
            chat_command=None,
            session_factory=self._session_factory,
            events=self._events,
            llm_provider=self._llm_provider,
            prompt_security_policy=self._prompt_security_policy,
            stageflow=self._stageflow,
            prompt_registry=self._prompt_registry,
            config=self._config,
            blueprint_output=self._blueprint_output,
            prompt_item_worker_output=self._prompt_item_worker_output,
            scenario_worker_output=self._scenario_worker_output,
            timeout_ms=self._generation_timeout_ms,
            sanitize_text=self._sanitize_generation_text,
            workplace_context_for_commands=self._collection_workplace_context,
        )

    async def generate_chat_draft(
        self,
        actor: Actor,
        *,
        request_id: str,
        trace_id: str,
        workflow_id: str | None,
        command: ChatCollectionGenerationCommand,
    ) -> CollectionGenerationView:
        return await generate_collection(
            actor=actor,
            request_id=request_id,
            trace_id=trace_id,
            workflow_id=workflow_id,
            mode="chat",
            structured_command=None,
            chat_command=command,
            session_factory=self._session_factory,
            events=self._events,
            llm_provider=self._llm_provider,
            prompt_security_policy=self._prompt_security_policy,
            stageflow=self._stageflow,
            prompt_registry=self._prompt_registry,
            config=self._config,
            blueprint_output=self._blueprint_output,
            prompt_item_worker_output=self._prompt_item_worker_output,
            scenario_worker_output=self._scenario_worker_output,
            timeout_ms=self._generation_timeout_ms,
            sanitize_text=self._sanitize_generation_text,
            workplace_context_for_commands=self._collection_workplace_context,
        )

    async def generate_prompt_items_structured(
        self,
        actor: Actor,
        *,
        request_id: str,
        trace_id: str,
        workflow_id: str | None,
        collection_id: str,
        command: StructuredPromptItemGenerationCommand,
    ) -> PromptItemGenerationView:
        return await generate_prompt_items_for_collection(
            actor=actor,
            request_id=request_id,
            trace_id=trace_id,
            workflow_id=workflow_id,
            collection_id=collection_id,
            mode="prompt_items_structured",
            structured_command=command,
            chat_command=None,
            session_factory=self._session_factory,
            events=self._events,
            llm_provider=self._llm_provider,
            prompt_security_policy=self._prompt_security_policy,
            stageflow=self._stageflow,
            prompt_registry=self._prompt_registry,
            config=self._config,
            prompt_item_plan_output=self._prompt_item_plan_output,
            prompt_item_worker_output=self._prompt_item_worker_output,
            timeout_ms=self._generation_timeout_ms,
            sanitize_text=self._sanitize_generation_text,
            compatible_prompt_item_rubric_ids=self._compatible_prompt_item_rubric_ids,
        )

    async def generate_prompt_items_chat(
        self,
        actor: Actor,
        *,
        request_id: str,
        trace_id: str,
        workflow_id: str | None,
        collection_id: str,
        command: ChatPromptItemGenerationCommand,
    ) -> PromptItemGenerationView:
        return await generate_prompt_items_for_collection(
            actor=actor,
            request_id=request_id,
            trace_id=trace_id,
            workflow_id=workflow_id,
            collection_id=collection_id,
            mode="prompt_items_chat",
            structured_command=None,
            chat_command=command,
            session_factory=self._session_factory,
            events=self._events,
            llm_provider=self._llm_provider,
            prompt_security_policy=self._prompt_security_policy,
            stageflow=self._stageflow,
            prompt_registry=self._prompt_registry,
            config=self._config,
            prompt_item_plan_output=self._prompt_item_plan_output,
            prompt_item_worker_output=self._prompt_item_worker_output,
            timeout_ms=self._generation_timeout_ms,
            sanitize_text=self._sanitize_generation_text,
            compatible_prompt_item_rubric_ids=self._compatible_prompt_item_rubric_ids,
        )

    def prepare_structured_draft_stream(
        self,
        actor: Actor,
        *,
        request_id: str,
        trace_id: str,
        workflow_id: str | None,
        command: StructuredCollectionGenerationCommand,
    ) -> tuple[GenerationStartedView, StructuredCollectionGenerationCommand]:
        generation_id = uuid4().hex
        stream_token = f"gen_{generation_id}"
        execution = GenerationExecution(
            generation_id=generation_id,
            mode="structured",
            stream_token=stream_token,
        )
        if self._broker is not None:
            self._broker.register_execution(execution)
        return (
            GenerationStartedView(
                generation_id=generation_id,
                stream_token=stream_token,
                mode="structured",
            ),
            command,
        )

    async def run_structured_draft_stream(
        self,
        actor: Actor,
        execution: GenerationExecution,
        request_id: str,
        trace_id: str,
        workflow_id: str | None,
        command: StructuredCollectionGenerationCommand,
    ) -> None:
        started_event = GenerationStreamEvent(
            event_id=uuid4().hex,
            generation_id=execution.generation_id,
            type="started",
            stage=GenerationStage.PENDING,
            sequence_number=0,
            emitted_at=datetime.now(UTC),
            progress_percent=0.0,
            payload={"mode": "structured"},
        )
        if self._broker is not None:
            await self._broker.publish(execution.stream_token, started_event)

        try:
            progress_callback = self._make_progress_callback(execution)
            result = await generate_collection(
                actor=actor,
                request_id=request_id,
                trace_id=trace_id,
                workflow_id=workflow_id,
                mode="structured",
                structured_command=command,
                chat_command=None,
                session_factory=self._session_factory,
                events=self._events,
                llm_provider=self._llm_provider,
                prompt_security_policy=self._prompt_security_policy,
                stageflow=self._stageflow,
                prompt_registry=self._prompt_registry,
                config=self._config,
                blueprint_output=self._blueprint_output,
                prompt_item_worker_output=self._prompt_item_worker_output,
                scenario_worker_output=self._scenario_worker_output,
                timeout_ms=self._generation_timeout_ms,
                sanitize_text=self._sanitize_generation_text,
                workplace_context_for_commands=self._collection_workplace_context,
                progress_callback=progress_callback,
            )
            complete_event = GenerationStreamEvent(
                event_id=uuid4().hex,
                generation_id=execution.generation_id,
                type="completed",
                stage=GenerationStage.COMPLETED,
                sequence_number=100,
                emitted_at=datetime.now(UTC),
                progress_percent=100.0,
                payload={
                    "collection_id": str(result.collection.id),
                    "generation_artifact_id": result.generation_artifact_id,
                },
            )
            if self._broker is not None:
                await self._broker.publish(execution.stream_token, complete_event)
        except Exception as exc:
            error_event = GenerationStreamEvent(
                event_id=uuid4().hex,
                generation_id=execution.generation_id,
                type="failed",
                stage=GenerationStage.FAILED,
                sequence_number=999,
                emitted_at=datetime.now(UTC),
                progress_percent=0.0,
                payload={"error": str(exc)},
            )
            if self._broker is not None:
                await self._broker.publish(execution.stream_token, error_event)
        finally:
            if self._broker is not None:
                self._broker.remove_execution(execution.generation_id)

    def prepare_chat_draft_stream(
        self,
        actor: Actor,
        *,
        request_id: str,
        trace_id: str,
        workflow_id: str | None,
        command: ChatCollectionGenerationCommand,
    ) -> tuple[GenerationStartedView, ChatCollectionGenerationCommand]:
        generation_id = uuid4().hex
        stream_token = f"gen_{generation_id}"
        execution = GenerationExecution(
            generation_id=generation_id,
            mode="chat",
            stream_token=stream_token,
        )
        if self._broker is not None:
            self._broker.register_execution(execution)
        return (
            GenerationStartedView(
                generation_id=generation_id,
                stream_token=stream_token,
                mode="chat",
            ),
            command,
        )

    async def run_chat_draft_stream(
        self,
        actor: Actor,
        execution: GenerationExecution,
        request_id: str,
        trace_id: str,
        workflow_id: str | None,
        command: ChatCollectionGenerationCommand,
    ) -> None:
        started_event = GenerationStreamEvent(
            event_id=uuid4().hex,
            generation_id=execution.generation_id,
            type="started",
            stage=GenerationStage.PENDING,
            sequence_number=0,
            emitted_at=datetime.now(UTC),
            progress_percent=0.0,
            payload={"mode": "chat"},
        )
        if self._broker is not None:
            await self._broker.publish(execution.stream_token, started_event)

        try:
            progress_callback = self._make_progress_callback(execution)
            result = await generate_collection(
                actor=actor,
                request_id=request_id,
                trace_id=trace_id,
                workflow_id=workflow_id,
                mode="chat",
                structured_command=None,
                chat_command=command,
                session_factory=self._session_factory,
                events=self._events,
                llm_provider=self._llm_provider,
                prompt_security_policy=self._prompt_security_policy,
                stageflow=self._stageflow,
                prompt_registry=self._prompt_registry,
                config=self._config,
                blueprint_output=self._blueprint_output,
                prompt_item_worker_output=self._prompt_item_worker_output,
                scenario_worker_output=self._scenario_worker_output,
                timeout_ms=self._generation_timeout_ms,
                sanitize_text=self._sanitize_generation_text,
                workplace_context_for_commands=self._collection_workplace_context,
                progress_callback=progress_callback,
            )
            complete_event = GenerationStreamEvent(
                event_id=uuid4().hex,
                generation_id=execution.generation_id,
                type="completed",
                stage=GenerationStage.COMPLETED,
                sequence_number=100,
                emitted_at=datetime.now(UTC),
                progress_percent=100.0,
                payload={
                    "collection_id": str(result.collection.id),
                    "generation_artifact_id": result.generation_artifact_id,
                },
            )
            if self._broker is not None:
                await self._broker.publish(execution.stream_token, complete_event)
        except Exception as exc:
            error_event = GenerationStreamEvent(
                event_id=uuid4().hex,
                generation_id=execution.generation_id,
                type="failed",
                stage=GenerationStage.FAILED,
                sequence_number=999,
                emitted_at=datetime.now(UTC),
                progress_percent=0.0,
                payload={"error": str(exc)},
            )
            if self._broker is not None:
                await self._broker.publish(execution.stream_token, error_event)
        finally:
            if self._broker is not None:
                self._broker.remove_execution(execution.generation_id)

    def _compatible_prompt_item_rubric_ids(self, rubric_ids: list[str]) -> list[str]:
        with self._session_factory() as session:
            rubrics = (
                session.query(RubricRecord)
                .filter(RubricRecord.rubric_id.in_(rubric_ids))
                .order_by(RubricRecord.rubric_id)
                .all()
            )
        return [
            rubric.rubric_id
            for rubric in rubrics
            if rubric.content_type in {"quick_practice_prompt", "interview_prompt"}
        ]

    def _collection_workplace_context(
        self,
        structured_command: StructuredCollectionGenerationCommand | None,
        chat_command: ChatCollectionGenerationCommand | None,
    ) -> str:
        if structured_command is not None:
            return structured_command.workplace_context
        assert chat_command is not None
        return chat_command.prompt

    def _sanitize_generation_text(self, text: str) -> str:
        try:
            _, report = self._prompt_security_policy.build_user_message(text)
        except PromptSecurityError as exc:
            raise validation_error(
                "Generation input was blocked by the prompt-security policy",
                code="SS-VALIDATION-056",
                details=exc.report.to_dict(),
            ) from exc
        return report.sanitized_text

    @property
    def _generation_timeout_ms(self) -> int:
        return int(max(60_000, self._settings.smoke_timeout_seconds * 4_000))
