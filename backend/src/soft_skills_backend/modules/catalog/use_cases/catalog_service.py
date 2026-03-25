"""Catalog application facade."""

from __future__ import annotations

from sqlalchemy.orm import Session, sessionmaker

from soft_skills_backend.modules.catalog.contracts.collection_commands import (
    CollectionCreateCommand,
    CollectionLifecycleCommand,
    CollectionListFilters,
)
from soft_skills_backend.modules.catalog.contracts.collection_views import CollectionView
from soft_skills_backend.modules.catalog.contracts.prompt_item_commands import (
    PromptItemCreateCommand,
)
from soft_skills_backend.modules.catalog.contracts.prompt_item_views import PromptItemView
from soft_skills_backend.modules.catalog.contracts.scenario_commands import ScenarioCreateCommand
from soft_skills_backend.modules.catalog.contracts.scenario_views import ScenarioView
from soft_skills_backend.modules.catalog.infra.events import CatalogEventRecorder
from soft_skills_backend.modules.catalog.workflows.collections.service import CollectionService
from soft_skills_backend.modules.catalog.workflows.prompt_items.service import PromptItemService
from soft_skills_backend.modules.catalog.workflows.scenarios.service import ScenarioService
from soft_skills_backend.platform.db.repositories import SqlAlchemyWorkflowEventRepository
from soft_skills_backend.platform.workflows.stageflow_runtime import StageflowRuntime
from soft_skills_backend.shared.auth import Actor


class CatalogService:
    """Compose the feature-specific catalog services behind one application API."""

    def __init__(
        self,
        *,
        session_factory: sessionmaker[Session],
        workflow_events: SqlAlchemyWorkflowEventRepository,
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

    def list_collections(
        self, actor: Actor | None, filters: CollectionListFilters
    ) -> list[CollectionView]:
        return self._collections.list_collections(actor, filters)

    def get_collection(self, actor: Actor | None, collection_id: str) -> CollectionView:
        return self._collections.get_collection(actor, collection_id)

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
