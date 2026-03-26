"""Prompt item catalog service."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, cast
from uuid import uuid4

from sqlalchemy.orm import Session, sessionmaker
from stageflow.api import Pipeline, StageKind, stage
from stageflow.core import StageContext

from soft_skills_backend.modules.catalog.contracts.prompt_item_commands import (
    PromptItemCreateCommand,
    PromptItemUpdateCommand,
)
from soft_skills_backend.modules.catalog.contracts.prompt_item_views import PromptItemView
from soft_skills_backend.modules.catalog.domain.validators import (
    require_collection_owner_or_admin,
    validate_prompt_command,
)
from soft_skills_backend.modules.catalog.infra.events import CatalogEventRecorder
from soft_skills_backend.modules.catalog.workflows.collections.service import CollectionService
from soft_skills_backend.platform.db.models import CollectionRecord, PromptItemRecord
from soft_skills_backend.platform.workflows.stageflow import (
    StageflowPipelineSupport,
    StageflowStageResult,
    ok_output,
    payload_from_results,
    run_logged_pipeline,
)
from soft_skills_backend.platform.workflows.stageflow_runtime import StageflowRuntime
from soft_skills_backend.shared.auth import Actor
from soft_skills_backend.shared.errors import domain_error


class PromptItemService:
    """Own prompt item authoring operations."""

    def __init__(
        self,
        *,
        session_factory: sessionmaker[Session],
        events: CatalogEventRecorder,
        collections: CollectionService,
        stageflow_runtime: StageflowRuntime,
    ) -> None:
        self._session_factory = session_factory
        self._events = events
        self._collections = collections
        self._stageflow = StageflowPipelineSupport.from_runtime(stageflow_runtime)

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
        async def input_guard(_ctx: StageContext) -> Any:
            with self._session_factory() as session:
                collection = self._collection_or_error(session, collection_id)
                require_collection_owner_or_admin(actor, collection)
                validate_prompt_command(session, collection, command)
            return ok_output(
                StageflowStageResult(
                    payload=command,
                    summary={
                        "collection_id": collection_id,
                        "prompt_type": command.prompt_type,
                    },
                )
            )

        async def persistence_work(_ctx: StageContext) -> Any:
            with self._session_factory() as session:
                collection = self._collection_or_error(session, collection_id)
                record = PromptItemRecord(
                    id=uuid4().hex,
                    collection_id=collection_id,
                    author_user_id=actor.user_id,
                    prompt_type=command.prompt_type,
                    title=command.title,
                    prompt_text=command.prompt_text,
                    difficulty=command.difficulty,
                    lifecycle_state="draft",
                    target_skill_slugs=list(command.target_skill_slugs),
                    rubric_id=command.rubric_id,
                    created_at=datetime.now(UTC),
                    updated_at=datetime.now(UTC),
                )
                session.add(record)
                collection.updated_at = datetime.now(UTC)
                session.commit()
                prompt_id = record.id

            self._events.record(
                "catalog.prompt_item.created.v1",
                request_id=request_id,
                trace_id=trace_id,
                workflow_id=workflow_id or collection_id,
                payload={"collection_id": collection_id, "prompt_item_id": prompt_id},
            )
            return ok_output(
                StageflowStageResult(
                    payload=self._prompt_view(actor, collection_id, prompt_id),
                    summary={"collection_id": collection_id, "prompt_item_id": prompt_id},
                )
            )

        pipeline = Pipeline.from_stages(
            stage("input_guard", cast(Any, input_guard), StageKind.GUARD),
            stage(
                "persistence_work",
                cast(Any, persistence_work),
                StageKind.WORK,
                dependencies=("input_guard",),
            ),
            name="catalog_prompt_item_create",
        )
        results = await run_logged_pipeline(
            self._stageflow,
            pipeline,
            request_id=request_id,
            trace_id=trace_id,
            workflow_id=workflow_id or collection_id,
            user_id=actor.user_id,
            execution_mode="catalog_authoring",
            service="soft_skills_backend.catalog",
            idempotency_key=f"catalog_prompt_item_create:{actor.user_id}:{request_id}:{collection_id}",
            idempotency_params=command.model_dump(mode="json"),
        )
        return payload_from_results(results, "persistence_work", expected_type=PromptItemView)

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
        async def input_guard(_ctx: StageContext) -> Any:
            with self._session_factory() as session:
                collection = self._collection_or_error(session, collection_id)
                prompt_item = self._prompt_item_or_error(session, prompt_item_id)
                if prompt_item.collection_id != collection_id:
                    raise domain_error(
                        "Prompt item does not belong to the collection",
                        code="SS-DOMAIN-027",
                        details={"collection_id": collection_id, "prompt_item_id": prompt_item_id},
                    )
                require_collection_owner_or_admin(actor, collection)
                validate_prompt_command(session, collection, command)
            return ok_output(
                StageflowStageResult(
                    payload=command,
                    summary={"collection_id": collection_id, "prompt_item_id": prompt_item_id},
                )
            )

        async def persistence_work(_ctx: StageContext) -> Any:
            with self._session_factory() as session:
                collection = self._collection_or_error(session, collection_id)
                prompt_item = self._prompt_item_or_error(session, prompt_item_id)
                prompt_item.prompt_type = command.prompt_type
                prompt_item.title = command.title
                prompt_item.prompt_text = command.prompt_text
                prompt_item.difficulty = command.difficulty
                prompt_item.target_skill_slugs = list(command.target_skill_slugs)
                prompt_item.rubric_id = command.rubric_id
                prompt_item.updated_at = datetime.now(UTC)
                collection.updated_at = datetime.now(UTC)
                session.commit()

            self._events.record(
                "catalog.prompt_item.updated.v1",
                request_id=request_id,
                trace_id=trace_id,
                workflow_id=workflow_id or collection_id,
                payload={"collection_id": collection_id, "prompt_item_id": prompt_item_id},
            )
            return ok_output(
                StageflowStageResult(
                    payload=self._prompt_view(actor, collection_id, prompt_item_id),
                    summary={"collection_id": collection_id, "prompt_item_id": prompt_item_id},
                )
            )

        pipeline = Pipeline.from_stages(
            stage("input_guard", cast(Any, input_guard), StageKind.GUARD),
            stage(
                "persistence_work",
                cast(Any, persistence_work),
                StageKind.WORK,
                dependencies=("input_guard",),
            ),
            name="catalog_prompt_item_update",
        )
        results = await run_logged_pipeline(
            self._stageflow,
            pipeline,
            request_id=request_id,
            trace_id=trace_id,
            workflow_id=workflow_id or collection_id,
            user_id=actor.user_id,
            execution_mode="catalog_authoring",
            service="soft_skills_backend.catalog",
            idempotency_key=f"catalog_prompt_item_update:{actor.user_id}:{request_id}:{prompt_item_id}",
            idempotency_params=command.model_dump(mode="json"),
        )
        return payload_from_results(results, "persistence_work", expected_type=PromptItemView)

    def _prompt_view(self, actor: Actor, collection_id: str, prompt_item_id: str) -> PromptItemView:
        collection = self._collections.get_collection(actor, collection_id)
        for prompt_item in collection.prompt_items:
            if prompt_item.id == prompt_item_id:
                return prompt_item
        raise domain_error(
            "Prompt item was not found",
            code="SS-DOMAIN-028",
            status_code=404,
            details={"collection_id": collection_id, "prompt_item_id": prompt_item_id},
        )

    def _collection_or_error(self, session: Session, collection_id: str) -> CollectionRecord:
        record = session.get(CollectionRecord, collection_id)
        if record is None:
            raise domain_error(
                "Collection was not found",
                code="SS-DOMAIN-005",
                status_code=404,
                details={"collection_id": collection_id},
            )
        return record

    def _prompt_item_or_error(self, session: Session, prompt_item_id: str) -> PromptItemRecord:
        record = session.get(PromptItemRecord, prompt_item_id)
        if record is None:
            raise domain_error(
                "Prompt item was not found",
                code="SS-DOMAIN-028",
                status_code=404,
                details={"prompt_item_id": prompt_item_id},
            )
        return record
