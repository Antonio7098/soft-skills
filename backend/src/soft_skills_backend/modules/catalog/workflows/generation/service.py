"""Provider-backed creator generation service facade."""

from __future__ import annotations

from sqlalchemy.orm import Session, sessionmaker
from stageflow.agent.security import PromptSecurityError, PromptSecurityPolicy

from soft_skills_backend.config import Settings
from soft_skills_backend.engines.config import load_catalog_generation_runtime_config
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
from soft_skills_backend.modules.catalog.domain.models import (
    GeneratedCollectionBlueprint,
    GeneratedPromptItemDraft,
    GeneratedPromptItemPlanBatch,
    GeneratedScenarioDraft,
)
from soft_skills_backend.modules.catalog.infra.events import CatalogEventRecorder
from soft_skills_backend.modules.catalog.workflows.generation.collection_pipeline import (
    generate_collection,
)
from soft_skills_backend.modules.catalog.workflows.generation.prompt_item_pipeline import (
    generate_prompt_items_for_collection,
)
from soft_skills_backend.modules.catalog.workflows.generation.prompt_library import (
    build_catalog_generation_prompt_library,
)
from soft_skills_backend.modules.practice.workflows.assessment import TypedLLMOutput
from soft_skills_backend.platform.db.models import RubricRecord
from soft_skills_backend.platform.workflows.stageflow import StageflowPipelineSupport
from soft_skills_backend.platform.workflows.stageflow_runtime import StageflowRuntime
from soft_skills_backend.shared.auth import Actor
from soft_skills_backend.shared.errors import validation_error
from soft_skills_backend.shared.ports.llm import LLMProvider


class CatalogGenerationService:
    """Generate draft collections and prompt items through typed Stageflow workflows."""

    def __init__(
        self,
        *,
        settings: Settings,
        session_factory: sessionmaker[Session],
        events: CatalogEventRecorder,
        llm_provider: LLMProvider,
        prompt_security_policy: PromptSecurityPolicy,
        stageflow_runtime: StageflowRuntime,
    ) -> None:
        self._settings = settings
        self._session_factory = session_factory
        self._events = events
        self._llm_provider = llm_provider
        self._prompt_security_policy = prompt_security_policy
        self._stageflow = StageflowPipelineSupport.from_runtime(stageflow_runtime)
        self._prompt_library = build_catalog_generation_prompt_library(settings)
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
            prompt_library=self._prompt_library,
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
            prompt_library=self._prompt_library,
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
            prompt_library=self._prompt_library,
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
            prompt_library=self._prompt_library,
            config=self._config,
            prompt_item_plan_output=self._prompt_item_plan_output,
            prompt_item_worker_output=self._prompt_item_worker_output,
            timeout_ms=self._generation_timeout_ms,
            sanitize_text=self._sanitize_generation_text,
            compatible_prompt_item_rubric_ids=self._compatible_prompt_item_rubric_ids,
        )

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
