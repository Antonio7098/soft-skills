"""Collection catalog service."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, cast
from uuid import uuid4

from sqlalchemy.orm import Session, sessionmaker
from stageflow.api import Pipeline, StageKind, stage

from soft_skills_backend.modules.catalog.contracts.collection_commands import (
    CollectionCreateCommand,
    CollectionLifecycleCommand,
    CollectionListFilters,
)
from soft_skills_backend.modules.catalog.contracts.collection_views import CollectionView
from soft_skills_backend.modules.catalog.contracts.views import build_collection_view
from soft_skills_backend.modules.catalog.domain.validators import (
    can_view_collection,
    require_collection_owner_or_admin,
    validate_collection_command,
    validate_lifecycle_transition,
)
from soft_skills_backend.modules.catalog.infra.events import CatalogEventRecorder
from soft_skills_backend.platform.db.models import CollectionRecord
from soft_skills_backend.platform.workflows.stageflow import (
    StageflowPipelineSupport,
    StageflowStageResult,
    ok_output,
    payload_from_results,
    run_logged_pipeline,
)
from soft_skills_backend.platform.workflows.stageflow_runtime import StageflowRuntime
from soft_skills_backend.shared.auth import Actor
from soft_skills_backend.shared.errors import auth_error, domain_error


class CollectionService:
    """Own collection browse and lifecycle operations."""

    def __init__(
        self,
        *,
        session_factory: sessionmaker[Session],
        events: CatalogEventRecorder,
        stageflow_runtime: StageflowRuntime,
    ) -> None:
        self._session_factory = session_factory
        self._events = events
        self._stageflow = StageflowPipelineSupport.from_runtime(stageflow_runtime)

    async def create_collection(
        self,
        actor: Actor,
        *,
        request_id: str,
        trace_id: str,
        workflow_id: str | None,
        command: CollectionCreateCommand,
    ) -> CollectionView:
        async def input_guard(_ctx) -> Any:
            with self._session_factory() as session:
                validate_collection_command(session, command)
            return ok_output(
                StageflowStageResult(
                    payload=command,
                    summary={"difficulty": command.difficulty},
                )
            )

        async def persistence_work(_ctx) -> Any:
            with self._session_factory() as session:
                now = datetime.now(UTC)
                collection = CollectionRecord(
                    id=uuid4().hex,
                    author_user_id=actor.user_id,
                    title=command.title,
                    summary=command.summary,
                    target_audience=command.target_audience,
                    difficulty=command.difficulty,
                    lifecycle_state="draft",
                    verification_state="unverified",
                    content_format_mix=command.content_format_mix,
                    target_skill_slugs=command.target_skill_slugs,
                    target_competency_slugs=command.target_competency_slugs,
                    rubric_ids=command.rubric_ids,
                    created_at=now,
                    updated_at=now,
                )
                session.add(collection)
                session.commit()
                collection_id = collection.id

            self._events.record(
                "catalog.collection.created.v1",
                actor.user_id,
                {"collection_id": collection_id, "author_user_id": actor.user_id},
            )
            return ok_output(
                StageflowStageResult(
                    payload=self.get_collection(actor, collection_id),
                    summary={"collection_id": collection_id},
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
            name="catalog_collection_create",
        )
        results = await run_logged_pipeline(
            self._stageflow,
            pipeline,
            request_id=request_id,
            trace_id=trace_id,
            workflow_id=workflow_id or f"catalog-collection-create:{actor.user_id}:{request_id}",
            user_id=actor.user_id,
            execution_mode="catalog_authoring",
            service="soft_skills_backend.catalog",
            idempotency_key=f"catalog_collection_create:{actor.user_id}:{request_id}",
            idempotency_params=command.model_dump(mode="json"),
        )
        return payload_from_results(results, "persistence_work", expected_type=CollectionView)

    def list_collections(
        self, actor: Actor | None, filters: CollectionListFilters
    ) -> list[CollectionView]:
        with self._session_factory() as session:
            query = session.query(CollectionRecord)
            if filters.difficulty is not None:
                query = query.filter(CollectionRecord.difficulty == filters.difficulty)
            records = query.order_by(CollectionRecord.created_at.desc()).all()
            visible = [
                record
                for record in records
                if can_view_collection(actor, record, filters.include_private)
                and (filters.skill_slug is None or filters.skill_slug in record.target_skill_slugs)
                and (
                    filters.competency_slug is None
                    or filters.competency_slug in record.target_competency_slugs
                )
            ]
            return [build_collection_view(session, record) for record in visible]

    def get_collection(self, actor: Actor | None, collection_id: str) -> CollectionView:
        with self._session_factory() as session:
            record = session.get(CollectionRecord, collection_id)
            if record is None:
                raise domain_error(
                    "Collection was not found",
                    code="SS-DOMAIN-005",
                    status_code=404,
                    details={"collection_id": collection_id},
                )
            if not can_view_collection(actor, record, include_private=True):
                raise auth_error(
                    "Collection is not visible to this actor",
                    code="SS-AUTH-004",
                    status_code=403,
                    details={"collection_id": collection_id},
                )
            return build_collection_view(session, record)

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
        async def input_guard(_ctx) -> Any:
            with self._session_factory() as session:
                record = session.get(CollectionRecord, collection_id)
                if record is None:
                    raise domain_error(
                        "Collection was not found",
                        code="SS-DOMAIN-005",
                        status_code=404,
                        details={"collection_id": collection_id},
                    )
                require_collection_owner_or_admin(actor, record)
                validate_lifecycle_transition(session, actor, record, command)
            return ok_output(
                StageflowStageResult(
                    payload=command,
                    summary={
                        "collection_id": collection_id,
                        "lifecycle_state": command.lifecycle_state,
                    },
                )
            )

        async def persistence_work(_ctx) -> Any:
            with self._session_factory() as session:
                record = session.get(CollectionRecord, collection_id)
                assert record is not None
                record.lifecycle_state = command.lifecycle_state
                if command.verification_state is not None:
                    record.verification_state = command.verification_state
                record.updated_at = datetime.now(UTC)
                session.commit()

            self._events.record(
                "catalog.collection.lifecycle_changed.v1",
                actor.user_id,
                {
                    "collection_id": collection_id,
                    "lifecycle_state": command.lifecycle_state,
                    "verification_state": command.verification_state,
                },
            )
            return ok_output(
                StageflowStageResult(
                    payload=self.get_collection(actor, collection_id),
                    summary={
                        "collection_id": collection_id,
                        "lifecycle_state": command.lifecycle_state,
                    },
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
            name="catalog_collection_lifecycle_update",
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
            idempotency_key=f"catalog_collection_lifecycle_update:{actor.user_id}:{request_id}:{collection_id}",
            idempotency_params=command.model_dump(mode="json"),
        )
        return payload_from_results(results, "persistence_work", expected_type=CollectionView)
