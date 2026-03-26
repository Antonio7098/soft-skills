"""Collection catalog service."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, cast
from uuid import uuid4

from sqlalchemy.orm import Session, sessionmaker
from stageflow.api import Pipeline, StageKind, stage
from stageflow.core import StageContext

from soft_skills_backend.modules.catalog.contracts.collection_commands import (
    CollectionCreateCommand,
    CollectionLifecycleCommand,
    CollectionListFilters,
    CollectionRateCommand,
    CollectionUpdateCommand,
)
from soft_skills_backend.modules.catalog.contracts.collection_views import CollectionView
from soft_skills_backend.modules.catalog.contracts.views import build_collection_view
from soft_skills_backend.modules.catalog.domain.validators import (
    can_view_collection,
    require_collection_owner_or_admin,
    validate_collection_command,
    validate_collection_filters,
    validate_collection_publishability,
    validate_collection_rate,
    validate_collection_save,
    validate_collection_source_type,
    validate_collection_unrate,
    validate_collection_unsave,
    validate_lifecycle_transition,
)
from soft_skills_backend.modules.catalog.infra.events import CatalogEventRecorder
from soft_skills_backend.platform.db.models import (
    CollectionRatingRecord,
    CollectionRecord,
    CollectionSaveRecord,
    PromptItemRecord,
    ScenarioRecord,
)
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
    """Own collection browse, save, and lifecycle operations."""

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
        source_type: str = "manual",
        last_generation_artifact_id: str | None = None,
    ) -> CollectionView:
        validate_collection_source_type(source_type)

        async def input_guard(_ctx: StageContext) -> Any:
            with self._session_factory() as session:
                validate_collection_command(session, command)
            return ok_output(
                StageflowStageResult(
                    payload=command,
                    summary={"difficulty": command.difficulty, "source_type": source_type},
                )
            )

        async def persistence_work(_ctx: StageContext) -> Any:
            with self._session_factory() as session:
                collection_id = self._create_collection_record(
                    session,
                    actor=actor,
                    command=command,
                    source_type=source_type,
                    last_generation_artifact_id=last_generation_artifact_id,
                )
                session.commit()

            self._events.record(
                "catalog.collection.created.v1",
                request_id=request_id,
                trace_id=trace_id,
                workflow_id=workflow_id or collection_id,
                payload={
                    "collection_id": collection_id,
                    "author_user_id": actor.user_id,
                    "source_type": source_type,
                    "last_generation_artifact_id": last_generation_artifact_id,
                },
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
            idempotency_params={
                **command.model_dump(mode="json"),
                "source_type": source_type,
                "last_generation_artifact_id": last_generation_artifact_id,
            },
        )
        return payload_from_results(results, "persistence_work", expected_type=CollectionView)

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
        async def input_guard(_ctx: StageContext) -> Any:
            with self._session_factory() as session:
                record = self._collection_record_or_error(session, collection_id)
                require_collection_owner_or_admin(actor, record)
                validate_collection_command(session, command)
            return ok_output(
                StageflowStageResult(
                    payload=command,
                    summary={"collection_id": collection_id, "difficulty": command.difficulty},
                )
            )

        async def persistence_work(_ctx: StageContext) -> Any:
            with self._session_factory() as session:
                record = self._collection_record_or_error(session, collection_id)
                record.title = command.title
                record.summary = command.summary
                record.target_audience = command.target_audience
                record.difficulty = command.difficulty
                record.content_format_mix = list(command.content_format_mix)
                record.target_skill_slugs = list(command.target_skill_slugs)
                record.target_competency_slugs = list(command.target_competency_slugs)
                record.rubric_ids = list(command.rubric_ids)
                record.updated_at = datetime.now(UTC)
                if record.lifecycle_state == "published_public":
                    validate_collection_publishability(session, record)
                session.commit()

            self._events.record(
                "catalog.collection.updated.v1",
                request_id=request_id,
                trace_id=trace_id,
                workflow_id=workflow_id or collection_id,
                payload={"collection_id": collection_id},
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
            name="catalog_collection_update",
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
            idempotency_key=f"catalog_collection_update:{actor.user_id}:{request_id}:{collection_id}",
            idempotency_params=command.model_dump(mode="json"),
        )
        return payload_from_results(results, "persistence_work", expected_type=CollectionView)

    def list_collections(
        self, actor: Actor | None, filters: CollectionListFilters
    ) -> list[CollectionView]:
        validate_collection_filters(filters)
        if filters.saved_only and actor is None:
            raise auth_error(
                "Saved collections require authentication",
                code="SS-AUTH-007",
                status_code=401,
            )
        with self._session_factory() as session:
            query = session.query(CollectionRecord)
            if filters.difficulty is not None:
                query = query.filter(CollectionRecord.difficulty == filters.difficulty)
            if filters.author_user_id is not None:
                query = query.filter(CollectionRecord.author_user_id == filters.author_user_id)
            if filters.organisation_id is not None:
                query = query.filter(CollectionRecord.organisation_id == filters.organisation_id)
            elif actor is not None and actor.organisation_id is not None:
                query = query.filter(CollectionRecord.organisation_id == actor.organisation_id)
            records = query.order_by(CollectionRecord.created_at.desc()).all()
            saved_collection_ids = set()
            if actor is not None:
                saved_collection_ids = {
                    record.collection_id
                    for record in session.query(CollectionSaveRecord)
                    .filter(CollectionSaveRecord.user_id == actor.user_id)
                    .all()
                }
            visible = [
                record
                for record in records
                if can_view_collection(actor, record, filters.include_private)
                and (filters.skill_slug is None or filters.skill_slug in record.target_skill_slugs)
                and (
                    filters.competency_slug is None
                    or filters.competency_slug in record.target_competency_slugs
                )
                and (filters.discovery_tier is None or record.lifecycle_state == "published_public")
                and (
                    filters.discovery_tier is None
                    or build_collection_view(session, record, actor=actor).discovery_tier
                    == filters.discovery_tier
                )
                and (not filters.saved_only or record.id in saved_collection_ids)
            ]
            return [build_collection_view(session, record, actor=actor) for record in visible]

    def get_collection(self, actor: Actor | None, collection_id: str) -> CollectionView:
        with self._session_factory() as session:
            record = self._collection_record_or_error(session, collection_id)
            if not can_view_collection(actor, record, include_private=True):
                raise auth_error(
                    "Collection is not visible to this actor",
                    code="SS-AUTH-004",
                    status_code=403,
                    details={"collection_id": collection_id},
                )
            return build_collection_view(session, record, actor=actor)

    async def save_collection(
        self,
        actor: Actor,
        *,
        request_id: str,
        trace_id: str,
        workflow_id: str | None,
        collection_id: str,
    ) -> CollectionView:
        async def input_guard(_ctx: StageContext) -> Any:
            with self._session_factory() as session:
                record = self._collection_record_or_error(session, collection_id)
                validate_collection_save(session, actor, record)
            return ok_output(
                StageflowStageResult(payload={"collection_id": collection_id}, summary={})
            )

        async def persistence_work(_ctx: StageContext) -> Any:
            with self._session_factory() as session:
                session.add(
                    CollectionSaveRecord(
                        user_id=actor.user_id,
                        collection_id=collection_id,
                        saved_at=datetime.now(UTC),
                    )
                )
                session.commit()

            self._events.record(
                "catalog.collection.saved.v1",
                request_id=request_id,
                trace_id=trace_id,
                workflow_id=workflow_id or collection_id,
                payload={"collection_id": collection_id, "user_id": actor.user_id},
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
            name="catalog_collection_save",
        )
        results = await run_logged_pipeline(
            self._stageflow,
            pipeline,
            request_id=request_id,
            trace_id=trace_id,
            workflow_id=workflow_id or collection_id,
            user_id=actor.user_id,
            execution_mode="catalog_discovery",
            service="soft_skills_backend.catalog",
            idempotency_key=f"catalog_collection_save:{actor.user_id}:{collection_id}",
            idempotency_params={"collection_id": collection_id},
        )
        return payload_from_results(results, "persistence_work", expected_type=CollectionView)

    async def unsave_collection(
        self,
        actor: Actor,
        *,
        request_id: str,
        trace_id: str,
        workflow_id: str | None,
        collection_id: str,
    ) -> CollectionView:
        async def input_guard(_ctx: StageContext) -> Any:
            with self._session_factory() as session:
                record = self._collection_record_or_error(session, collection_id)
                validate_collection_unsave(session, actor, record)
            return ok_output(
                StageflowStageResult(payload={"collection_id": collection_id}, summary={})
            )

        async def persistence_work(_ctx: StageContext) -> Any:
            with self._session_factory() as session:
                (
                    session.query(CollectionSaveRecord)
                    .filter(
                        CollectionSaveRecord.collection_id == collection_id,
                        CollectionSaveRecord.user_id == actor.user_id,
                    )
                    .delete()
                )
                session.commit()

            self._events.record(
                "catalog.collection.unsaved.v1",
                request_id=request_id,
                trace_id=trace_id,
                workflow_id=workflow_id or collection_id,
                payload={"collection_id": collection_id, "user_id": actor.user_id},
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
            name="catalog_collection_unsave",
        )
        results = await run_logged_pipeline(
            self._stageflow,
            pipeline,
            request_id=request_id,
            trace_id=trace_id,
            workflow_id=workflow_id or collection_id,
            user_id=actor.user_id,
            execution_mode="catalog_discovery",
            service="soft_skills_backend.catalog",
            idempotency_key=f"catalog_collection_unsave:{actor.user_id}:{collection_id}",
            idempotency_params={"collection_id": collection_id},
        )
        return payload_from_results(results, "persistence_work", expected_type=CollectionView)

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
        async def input_guard(_ctx: StageContext) -> Any:
            with self._session_factory() as session:
                record = self._collection_record_or_error(session, collection_id)
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

        async def persistence_work(_ctx: StageContext) -> Any:
            with self._session_factory() as session:
                record = self._collection_record_or_error(session, collection_id)
                record.lifecycle_state = command.lifecycle_state
                if command.verification_state is not None:
                    record.verification_state = command.verification_state
                record.updated_at = datetime.now(UTC)
                now = datetime.now(UTC)
                (
                    session.query(PromptItemRecord)
                    .filter(PromptItemRecord.collection_id == collection_id)
                    .update(
                        {
                            PromptItemRecord.lifecycle_state: command.lifecycle_state,
                            PromptItemRecord.updated_at: now,
                        }
                    )
                )
                (
                    session.query(ScenarioRecord)
                    .filter(ScenarioRecord.collection_id == collection_id)
                    .update(
                        {
                            ScenarioRecord.lifecycle_state: command.lifecycle_state,
                            ScenarioRecord.updated_at: now,
                        }
                    )
                )
                session.commit()

            payload = {
                "collection_id": collection_id,
                "lifecycle_state": command.lifecycle_state,
                "verification_state": command.verification_state,
            }
            self._events.record(
                "catalog.collection.lifecycle_changed.v1",
                request_id=request_id,
                trace_id=trace_id,
                workflow_id=workflow_id or collection_id,
                payload=payload,
            )
            if command.lifecycle_state.startswith("published_"):
                self._events.record(
                    "content.published.v1",
                    request_id=request_id,
                    trace_id=trace_id,
                    workflow_id=workflow_id or collection_id,
                    payload=payload,
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

    async def rate_collection(
        self,
        actor: Actor,
        *,
        request_id: str,
        trace_id: str,
        workflow_id: str | None,
        collection_id: str,
        command: CollectionRateCommand,
    ) -> CollectionView:
        async def input_guard(_ctx: StageContext) -> Any:
            with self._session_factory() as session:
                record = self._collection_record_or_error(session, collection_id)
                validate_collection_rate(session, actor, record, command)
            return ok_output(
                StageflowStageResult(payload={"collection_id": collection_id}, summary={})
            )

        async def persistence_work(_ctx: StageContext) -> Any:
            with self._session_factory() as session:
                record = self._collection_record_or_error(session, collection_id)
                existing = session.get(
                    CollectionRatingRecord,
                    {"user_id": actor.user_id, "collection_id": collection_id},
                )
                now = datetime.now(UTC)
                if existing is not None:
                    existing.rating = command.rating
                    existing.updated_at = now
                else:
                    session.add(
                        CollectionRatingRecord(
                            user_id=actor.user_id,
                            collection_id=collection_id,
                            rating=command.rating,
                            created_at=now,
                            updated_at=now,
                        )
                    )
                ratings = (
                    session.query(CollectionRatingRecord)
                    .filter(CollectionRatingRecord.collection_id == collection_id)
                    .all()
                )
                total = sum(r.rating for r in ratings)
                count = len(ratings)
                record.avg_rating = total / count if count > 0 else None
                record.rating_count = count
                record.updated_at = now
                session.commit()

            self._events.record(
                "catalog.collection.rated.v1",
                request_id=request_id,
                trace_id=trace_id,
                workflow_id=workflow_id or collection_id,
                payload={
                    "collection_id": collection_id,
                    "user_id": actor.user_id,
                    "rating": command.rating,
                },
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
            name="catalog_collection_rate",
        )
        results = await run_logged_pipeline(
            self._stageflow,
            pipeline,
            request_id=request_id,
            trace_id=trace_id,
            workflow_id=workflow_id or collection_id,
            user_id=actor.user_id,
            execution_mode="catalog_discovery",
            service="soft_skills_backend.catalog",
            idempotency_key=f"catalog_collection_rate:{actor.user_id}:{collection_id}",
            idempotency_params={"collection_id": collection_id, "rating": command.rating},
        )
        return payload_from_results(results, "persistence_work", expected_type=CollectionView)

    async def unrate_collection(
        self,
        actor: Actor,
        *,
        request_id: str,
        trace_id: str,
        workflow_id: str | None,
        collection_id: str,
    ) -> CollectionView:
        async def input_guard(_ctx: StageContext) -> Any:
            with self._session_factory() as session:
                record = self._collection_record_or_error(session, collection_id)
                validate_collection_unrate(session, actor, record)
            return ok_output(
                StageflowStageResult(payload={"collection_id": collection_id}, summary={})
            )

        async def persistence_work(_ctx: StageContext) -> Any:
            with self._session_factory() as session:
                record = self._collection_record_or_error(session, collection_id)
                (
                    session.query(CollectionRatingRecord)
                    .filter(
                        CollectionRatingRecord.collection_id == collection_id,
                        CollectionRatingRecord.user_id == actor.user_id,
                    )
                    .delete()
                )
                ratings = (
                    session.query(CollectionRatingRecord)
                    .filter(CollectionRatingRecord.collection_id == collection_id)
                    .all()
                )
                total = sum(r.rating for r in ratings) if ratings else 0
                count = len(ratings)
                record.avg_rating = total / count if count > 0 else None
                record.rating_count = count
                record.updated_at = datetime.now(UTC)
                session.commit()

            self._events.record(
                "catalog.collection.unrated.v1",
                request_id=request_id,
                trace_id=trace_id,
                workflow_id=workflow_id or collection_id,
                payload={"collection_id": collection_id, "user_id": actor.user_id},
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
            name="catalog_collection_unrate",
        )
        results = await run_logged_pipeline(
            self._stageflow,
            pipeline,
            request_id=request_id,
            trace_id=trace_id,
            workflow_id=workflow_id or collection_id,
            user_id=actor.user_id,
            execution_mode="catalog_discovery",
            service="soft_skills_backend.catalog",
            idempotency_key=f"catalog_collection_unrate:{actor.user_id}:{collection_id}",
            idempotency_params={"collection_id": collection_id},
        )
        return payload_from_results(results, "persistence_work", expected_type=CollectionView)

    def _collection_record_or_error(self, session: Session, collection_id: str) -> CollectionRecord:
        record = session.get(CollectionRecord, collection_id)
        if record is None:
            raise domain_error(
                "Collection was not found",
                code="SS-DOMAIN-005",
                status_code=404,
                details={"collection_id": collection_id},
            )
        return record

    def _create_collection_record(
        self,
        session: Session,
        *,
        actor: Actor,
        command: CollectionCreateCommand,
        source_type: str,
        last_generation_artifact_id: str | None,
    ) -> str:
        now = datetime.now(UTC)
        collection = CollectionRecord(
            id=uuid4().hex,
            author_user_id=actor.user_id,
            organisation_id=command.organisation_id,
            title=command.title,
            summary=command.summary,
            target_audience=command.target_audience,
            difficulty=command.difficulty,
            lifecycle_state="draft",
            verification_state="unverified",
            source_type=source_type,
            last_generation_artifact_id=last_generation_artifact_id,
            content_format_mix=list(command.content_format_mix),
            target_skill_slugs=list(command.target_skill_slugs),
            target_competency_slugs=list(command.target_competency_slugs),
            rubric_ids=list(command.rubric_ids),
            created_at=now,
            updated_at=now,
        )
        session.add(collection)
        session.flush()
        return collection.id
