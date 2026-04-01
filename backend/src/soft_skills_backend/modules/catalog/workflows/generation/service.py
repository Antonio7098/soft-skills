"""Provider-backed creator generation service facade."""

from __future__ import annotations

import asyncio
import re
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
from soft_skills_backend.modules.taxonomy import TaxonomyService, TaxonomySnapshot
from soft_skills_backend.modules.practice.workflows.assessment import TypedLLMOutput
from soft_skills_backend.platform.db.models import RubricRecord
from soft_skills_backend.platform.observability.events import WorkflowEventRecorder
from soft_skills_backend.platform.workflows.stageflow import StageflowPipelineSupport
from soft_skills_backend.platform.workflows.stageflow_runtime import StageflowRuntime
from soft_skills_backend.shared.auth import Actor
from soft_skills_backend.shared.errors import validation_error
from soft_skills_backend.shared.ports.llm import LLMProvider

_WORD_PATTERN = re.compile(r"[a-z0-9]+")
_DEFAULT_SKILL_PRIORITY = (
    "active-listening",
    "structured-communication",
    "expectation-setting",
    "decision-justification",
)


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
        taxonomy_service: TaxonomyService,
        stageflow_runtime: StageflowRuntime,
        broker: GenerationRealtimeBroker | None = None,
    ) -> None:
        self._settings = settings
        self._session_factory = session_factory
        self._events = events
        self._llm_provider = llm_provider
        self._prompt_security_policy = prompt_security_policy
        self._prompt_registry = prompt_registry
        self._taxonomy_service = taxonomy_service
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
                self._broker.publish_nowait(execution.stream_token, event)

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
            taxonomy_context_for_commands=self._collection_taxonomy_context,
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
        command = self.normalize_chat_generation_command(actor, command)
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
            taxonomy_context_for_commands=self._collection_taxonomy_context,
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
        execution.task = asyncio.current_task()
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
                taxonomy_context_for_commands=self._collection_taxonomy_context,
                progress_callback=progress_callback,
                execution=execution,
                idempotency_key_suffix=execution.generation_id,
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
        except asyncio.CancelledError:
            cancelled_event = GenerationStreamEvent(
                event_id=uuid4().hex,
                generation_id=execution.generation_id,
                type="cancelled",
                stage=GenerationStage.CANCELLED,
                sequence_number=999,
                emitted_at=datetime.now(UTC),
                progress_percent=0.0,
                payload={"reason": execution.cancel_reason or "user_requested"},
            )
            if self._broker is not None:
                await self._broker.publish(execution.stream_token, cancelled_event)
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
            execution.task = None
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
        command = self.normalize_chat_generation_command(actor, command)
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
        execution.task = asyncio.current_task()
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
                taxonomy_context_for_commands=self._collection_taxonomy_context,
                progress_callback=progress_callback,
                execution=execution,
                idempotency_key_suffix=execution.generation_id,
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
        except asyncio.CancelledError:
            cancelled_event = GenerationStreamEvent(
                event_id=uuid4().hex,
                generation_id=execution.generation_id,
                type="cancelled",
                stage=GenerationStage.CANCELLED,
                sequence_number=999,
                emitted_at=datetime.now(UTC),
                progress_percent=0.0,
                payload={"reason": execution.cancel_reason or "user_requested"},
            )
            if self._broker is not None:
                await self._broker.publish(execution.stream_token, cancelled_event)
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
            execution.task = None
            if self._broker is not None:
                self._broker.remove_execution(execution.generation_id)

    def _compatible_prompt_item_rubric_ids(self, rubric_ids: list[str]) -> list[str]:
        with self._session_factory() as session:
            rubrics = (
                session.query(RubricRecord)
                .filter(RubricRecord.id.in_(rubric_ids))
                .order_by(RubricRecord.id)
                .all()
            )
        return [
            rubric.id
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

    def _collection_taxonomy_context(
        self,
        actor: Actor,
        structured_command: StructuredCollectionGenerationCommand | None,
        chat_command: ChatCollectionGenerationCommand | None,
    ) -> str:
        command = structured_command or chat_command
        organisation_id = (
            command.organisation_id
            if command is not None and command.organisation_id is not None
            else actor.organisation_id
        )
        return self._taxonomy_service.render_prompt_context(organisation_id)

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

    def normalize_chat_generation_command(
        self,
        actor: Actor,
        command: ChatCollectionGenerationCommand,
    ) -> ChatCollectionGenerationCommand:
        organisation_id = command.organisation_id or actor.organisation_id
        snapshot = self._taxonomy_service.snapshot(organisation_id)

        skill_slugs = list(command.target_skill_slugs)
        competency_slugs = list(command.target_competency_slugs)
        skill_index = {skill.slug: skill for skill in snapshot.skills}
        competency_index = {competency.slug: competency for competency in snapshot.competencies}

        if not skill_slugs:
            skill_slugs = self._infer_skill_slugs(
                text=" ".join(
                    part for part in (command.prompt, command.target_audience) if part.strip()
                ),
                snapshot=snapshot,
            )
        if not skill_slugs:
            skill_slugs = self._default_skill_slugs(snapshot)

        if skill_slugs and not competency_slugs:
            competency_slugs = self._infer_competency_slugs(
                skill_slugs=skill_slugs,
                snapshot=snapshot,
            )

        if competency_slugs and skill_slugs:
            aligned = [
                skill_slug
                for skill_slug in skill_slugs
                if any(
                    skill_slug in competency_index[competency_slug].skill_slugs
                    for competency_slug in competency_slugs
                    if competency_slug in competency_index
                )
            ]
            if aligned:
                skill_slugs = aligned

        content_format_mix = list(dict.fromkeys(command.content_format_mix))
        if command.counts.quick_practice_prompt_count > 0 and "quick_practice_prompt" not in content_format_mix:
            content_format_mix.append("quick_practice_prompt")
        if command.counts.interview_prompt_count > 0 and "interview_prompt" not in content_format_mix:
            content_format_mix.append("interview_prompt")
        if command.counts.scenario_count > 0 and "scenario_step" not in content_format_mix:
            content_format_mix.append("scenario_step")

        rubric_ids = list(dict.fromkeys(command.rubric_ids))
        if not rubric_ids:
            rubric_ids = self._default_rubric_ids_for_formats(
                content_format_mix=content_format_mix,
                snapshot=snapshot,
            )

        counts = command.counts
        if counts.scenario_count == 0 and counts.scenario_artifact_count > 0:
            counts = counts.model_copy(update={"scenario_artifact_count": 0})

        return command.model_copy(
            update={
                "target_skill_slugs": [slug for slug in skill_slugs if slug in skill_index],
                "target_competency_slugs": [
                    slug for slug in competency_slugs if slug in competency_index
                ],
                "content_format_mix": content_format_mix,
                "rubric_ids": rubric_ids,
                "counts": counts,
                "organisation_id": organisation_id,
            }
        )

    def _infer_skill_slugs(self, *, text: str, snapshot: TaxonomySnapshot) -> list[str]:
        terms = set(_WORD_PATTERN.findall(text.lower()))
        scored: list[tuple[int, str]] = []
        for skill in snapshot.skills:
            skill_terms = set(_WORD_PATTERN.findall(skill.slug.replace("-", " "))) | set(
                _WORD_PATTERN.findall(skill.name.lower())
            )
            score = len(terms & skill_terms)
            if score > 0:
                scored.append((score, skill.slug))
        scored.sort(key=lambda item: (-item[0], item[1]))
        return [slug for _, slug in scored[:4]]

    def _infer_competency_slugs(
        self,
        *,
        skill_slugs: list[str],
        snapshot: TaxonomySnapshot,
    ) -> list[str]:
        requested = set(skill_slugs)
        scored: list[tuple[int, str]] = []
        for competency in snapshot.competencies:
            overlap = len(requested & set(competency.skill_slugs))
            if overlap > 0:
                scored.append((overlap, competency.slug))
        scored.sort(key=lambda item: (-item[0], item[1]))
        return [slug for _, slug in scored[:2]]

    def _default_rubric_ids_for_formats(
        self,
        *,
        content_format_mix: list[str],
        snapshot: TaxonomySnapshot,
    ) -> list[str]:
        selected: list[str] = []
        for content_type in content_format_mix:
            matching = [rubric for rubric in snapshot.rubrics if rubric.content_type == content_type]
            if not matching:
                continue
            general = [rubric for rubric in matching if rubric.skill_slug == "general"]
            chosen = sorted(general or matching, key=lambda rubric: rubric.rubric_id)[0]
            selected.append(chosen.rubric_id)
        return list(dict.fromkeys(selected))

    def _default_skill_slugs(self, snapshot: TaxonomySnapshot) -> list[str]:
        available = {skill.slug for skill in snapshot.skills}
        prioritized = [slug for slug in _DEFAULT_SKILL_PRIORITY if slug in available]
        if prioritized:
            return prioritized[:4]
        return sorted(available)[:4]
