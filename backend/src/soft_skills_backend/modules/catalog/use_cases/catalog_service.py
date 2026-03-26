"""Catalog application facade."""

from __future__ import annotations

from sqlalchemy.orm import Session, sessionmaker
from stageflow.agent.security import PromptSecurityPolicy

from soft_skills_backend.config import Settings
from soft_skills_backend.modules.catalog.contracts.collection_commands import (
    ChatCollectionGenerationCommand,
    CollectionCreateCommand,
    CollectionLifecycleCommand,
    CollectionListFilters,
    CollectionUpdateCommand,
    StructuredCollectionGenerationCommand,
)
from soft_skills_backend.modules.catalog.contracts.collection_views import (
    CollectionGenerationView,
    CollectionView,
)
from soft_skills_backend.modules.catalog.contracts.prompt_item_commands import (
    PromptItemCreateCommand,
    PromptItemUpdateCommand,
)
from soft_skills_backend.modules.catalog.contracts.prompt_item_views import PromptItemView
from soft_skills_backend.modules.catalog.contracts.scenario_commands import (
    ScenarioCreateCommand,
    ScenarioUpdateCommand,
)
from soft_skills_backend.modules.catalog.contracts.scenario_views import ScenarioView
from soft_skills_backend.modules.catalog.infra.events import CatalogEventRecorder
from soft_skills_backend.modules.catalog.workflows.collections.service import CollectionService
from soft_skills_backend.modules.catalog.workflows.generation.service import (
    CatalogGenerationService,
    build_catalog_generation_prompt_library,
    build_catalog_generation_typed_output,
)
from soft_skills_backend.modules.catalog.workflows.prompt_items.service import PromptItemService
from soft_skills_backend.modules.catalog.workflows.scenarios.service import ScenarioService
from soft_skills_backend.platform.db.repositories import SqlAlchemyWorkflowEventRepository
from soft_skills_backend.platform.workflows.stageflow_runtime import StageflowRuntime
from soft_skills_backend.shared.auth import Actor
from soft_skills_backend.shared.ports.llm import LLMProvider


class CatalogService:
    """Compose the feature-specific catalog services behind one application API."""

    def __init__(
        self,
        *,
        settings: Settings,
        session_factory: sessionmaker[Session],
        workflow_events: SqlAlchemyWorkflowEventRepository,
        llm_provider: LLMProvider,
        stageflow_runtime: StageflowRuntime,
    ) -> None:
        events = CatalogEventRecorder(workflow_events)
        self._collections = CollectionService(
            session_factory=session_factory,
            events=events,
            stageflow_runtime=stageflow_runtime,
        )
        self._prompt_items = PromptItemService(
            session_factory=session_factory,
            events=events,
            collections=self._collections,
            stageflow_runtime=stageflow_runtime,
        )
        self._scenarios = ScenarioService(
            session_factory=session_factory,
            events=events,
            collections=self._collections,
            stageflow_runtime=stageflow_runtime,
        )
        self._generation = CatalogGenerationService(
            settings=settings,
            session_factory=session_factory,
            events=events,
            llm_provider=llm_provider,
            prompt_library=build_catalog_generation_prompt_library(settings),
            typed_output=build_catalog_generation_typed_output(settings),
            prompt_security_policy=PromptSecurityPolicy(),
            stageflow_runtime=stageflow_runtime,
        )

    async def create_collection(
        self,
        actor: Actor,
        *,
        request_id: str,
        trace_id: str,
        workflow_id: str | None,
        command: CollectionCreateCommand,
    ) -> CollectionView:
        return await self._collections.create_collection(
            actor,
            request_id=request_id,
            trace_id=trace_id,
            workflow_id=workflow_id,
            command=command,
        )

    async def update_collection(
        self,
        actor: Actor,
        *,
        request_id: str,
        trace_id: str,
        workflow_id: str | None,
        collection_id: str,
        command: CollectionUpdateCommand,
    ) -> CollectionView:
        return await self._collections.update_collection(
            actor,
            request_id=request_id,
            trace_id=trace_id,
            workflow_id=workflow_id,
            collection_id=collection_id,
            command=command,
        )

    def list_collections(
        self, actor: Actor | None, filters: CollectionListFilters
    ) -> list[CollectionView]:
        return self._collections.list_collections(actor, filters)

    def get_collection(self, actor: Actor | None, collection_id: str) -> CollectionView:
        return self._collections.get_collection(actor, collection_id)

    async def save_collection(
        self,
        actor: Actor,
        *,
        request_id: str,
        trace_id: str,
        workflow_id: str | None,
        collection_id: str,
    ) -> CollectionView:
        return await self._collections.save_collection(
            actor,
            request_id=request_id,
            trace_id=trace_id,
            workflow_id=workflow_id,
            collection_id=collection_id,
        )

    async def unsave_collection(
        self,
        actor: Actor,
        *,
        request_id: str,
        trace_id: str,
        workflow_id: str | None,
        collection_id: str,
    ) -> CollectionView:
        return await self._collections.unsave_collection(
            actor,
            request_id=request_id,
            trace_id=trace_id,
            workflow_id=workflow_id,
            collection_id=collection_id,
        )

    async def update_collection_lifecycle(
        self,
        actor: Actor,
        *,
        request_id: str,
        trace_id: str,
        workflow_id: str | None,
        collection_id: str,
        command: CollectionLifecycleCommand,
    ) -> CollectionView:
        return await self._collections.update_collection_lifecycle(
            actor,
            request_id=request_id,
            trace_id=trace_id,
            workflow_id=workflow_id,
            collection_id=collection_id,
            command=command,
        )

    async def add_prompt_item(
        self,
        actor: Actor,
        *,
        request_id: str,
        trace_id: str,
        workflow_id: str | None,
        collection_id: str,
        command: PromptItemCreateCommand,
    ) -> PromptItemView:
        return await self._prompt_items.add_prompt_item(
            actor,
            request_id=request_id,
            trace_id=trace_id,
            workflow_id=workflow_id,
            collection_id=collection_id,
            command=command,
        )

    async def update_prompt_item(
        self,
        actor: Actor,
        *,
        request_id: str,
        trace_id: str,
        workflow_id: str | None,
        collection_id: str,
        prompt_item_id: str,
        command: PromptItemUpdateCommand,
    ) -> PromptItemView:
        return await self._prompt_items.update_prompt_item(
            actor,
            request_id=request_id,
            trace_id=trace_id,
            workflow_id=workflow_id,
            collection_id=collection_id,
            prompt_item_id=prompt_item_id,
            command=command,
        )

    async def add_scenario(
        self,
        actor: Actor,
        *,
        request_id: str,
        trace_id: str,
        workflow_id: str | None,
        collection_id: str,
        command: ScenarioCreateCommand,
    ) -> ScenarioView:
        return await self._scenarios.add_scenario(
            actor,
            request_id=request_id,
            trace_id=trace_id,
            workflow_id=workflow_id,
            collection_id=collection_id,
            command=command,
        )

    async def update_scenario(
        self,
        actor: Actor,
        *,
        request_id: str,
        trace_id: str,
        workflow_id: str | None,
        collection_id: str,
        scenario_id: str,
        command: ScenarioUpdateCommand,
    ) -> ScenarioView:
        return await self._scenarios.update_scenario(
            actor,
            request_id=request_id,
            trace_id=trace_id,
            workflow_id=workflow_id,
            collection_id=collection_id,
            scenario_id=scenario_id,
            command=command,
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
        return await self._generation.generate_structured_draft(
            actor,
            request_id=request_id,
            trace_id=trace_id,
            workflow_id=workflow_id,
            command=command,
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
        return await self._generation.generate_chat_draft(
            actor,
            request_id=request_id,
            trace_id=trace_id,
            workflow_id=workflow_id,
            command=command,
        )
