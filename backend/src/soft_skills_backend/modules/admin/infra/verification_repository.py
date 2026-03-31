"""Admin verification persistence and queries."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy.orm import Session, sessionmaker

from soft_skills_backend.modules.admin.contracts.commands import AdminCollectionVerificationCommand
from soft_skills_backend.modules.admin.contracts.views import (
    CollectionVerificationAuditView,
    CollectionVerificationQueueItemView,
    CollectionVerificationReviewView,
)
from soft_skills_backend.modules.admin.domain.verification import (
    validate_admin_verification_transition,
)
from soft_skills_backend.modules.catalog.contracts.views import build_collection_view
from soft_skills_backend.modules.catalog.domain.validators import (
    discovery_tier_for_collection,
    validate_collection_publishability,
)
from soft_skills_backend.platform.db.models import (
    CollectionRecord,
    CollectionVerificationReviewRecord,
    PromptItemRecord,
    ScenarioRecord,
)
from soft_skills_backend.platform.db.repositories import SqlAlchemyWorkflowEventRepository
from soft_skills_backend.platform.observability.events import WorkflowEvent
from soft_skills_backend.shared.auth import Actor
from soft_skills_backend.shared.errors import domain_error


def _utcnow() -> datetime:
    return datetime.now(UTC)


class AdminVerificationRepository:
    """Own admin verification workflow state and history."""

    def __init__(
        self,
        *,
        session_factory: sessionmaker[Session],
        workflow_events: SqlAlchemyWorkflowEventRepository,
    ) -> None:
        self._session_factory = session_factory
        self._workflow_events = workflow_events

    def list_verification_queue(
        self, organisation_id: str | None = None
    ) -> list[CollectionVerificationQueueItemView]:
        with self._session_factory() as session:
            query = session.query(CollectionRecord).filter(
                CollectionRecord.lifecycle_state == "published_public"
            )
            if organisation_id is not None:
                query = query.filter(CollectionRecord.organisation_id == organisation_id)
            records = query.order_by(
                CollectionRecord.updated_at.desc(), CollectionRecord.created_at.desc()
            ).all()
            latest_reviews = self._latest_reviews_by_collection(
                session, [record.id for record in records]
            )
            items: list[CollectionVerificationQueueItemView] = []
            for record in records:
                latest_review = latest_reviews.get(record.id)
                items.append(
                    CollectionVerificationQueueItemView(
                        collection_id=record.id,
                        author_user_id=record.author_user_id,
                        title=record.title,
                        lifecycle_state=record.lifecycle_state,
                        verification_state=record.verification_state,
                        discovery_tier=discovery_tier_for_collection(record),
                        source_type=record.source_type,
                        prompt_item_count=self._prompt_item_count(session, record.id),
                        scenario_count=self._scenario_count(session, record.id),
                        created_at=record.created_at.isoformat(),
                        updated_at=record.updated_at.isoformat(),
                        latest_reviewed_at=None
                        if latest_review is None
                        else latest_review.occurred_at.isoformat(),
                        latest_reviewer_user_id=None
                        if latest_review is None
                        else latest_review.reviewer_user_id,
                        latest_note=None if latest_review is None else latest_review.note,
                    )
                )
            return items

    def get_collection_verification(
        self, collection_id: str, organisation_id: str | None = None
    ) -> CollectionVerificationAuditView:
        with self._session_factory() as session:
            collection = session.get(CollectionRecord, collection_id)
            if collection is None:
                raise domain_error(
                    "Collection was not found",
                    code="SS-DOMAIN-005",
                    status_code=404,
                    details={"collection_id": collection_id},
                )
            if organisation_id is not None and collection.organisation_id != organisation_id:
                raise domain_error(
                    "Collection is not in your organisation",
                    code="SS-AUTH-004",
                    status_code=403,
                    details={"collection_id": collection_id, "organisation_id": organisation_id},
                )
            history = self._history(session, collection_id)
            return CollectionVerificationAuditView(
                collection=build_collection_view(session, collection, actor=None),
                latest_review=None if not history else history[0],
                history=history,
            )

    def update_verification(
        self,
        actor: Actor,
        *,
        request_id: str,
        trace_id: str,
        workflow_id: str | None,
        collection_id: str,
        command: AdminCollectionVerificationCommand,
    ) -> CollectionVerificationAuditView:
        review_id = uuid4().hex
        occurred_at = _utcnow()
        with self._session_factory() as session:
            collection = session.get(CollectionRecord, collection_id)
            if collection is None:
                raise domain_error(
                    "Collection was not found",
                    code="SS-DOMAIN-005",
                    status_code=404,
                    details={"collection_id": collection_id},
                )
            validate_admin_verification_transition(
                lifecycle_state=collection.lifecycle_state,
                current_state=collection.verification_state,
                next_state=command.verification_state,
                note=command.note,
                collection_id=collection_id,
            )
            if command.verification_state == "verified":
                validate_collection_publishability(session, collection)

            previous_state = collection.verification_state
            collection.verification_state = command.verification_state
            collection.updated_at = occurred_at
            session.add(
                CollectionVerificationReviewRecord(
                    id=review_id,
                    collection_id=collection_id,
                    reviewer_user_id=actor.user_id,
                    previous_verification_state=previous_state,
                    next_verification_state=command.verification_state,
                    note=command.note,
                    request_id=request_id or None,
                    trace_id=trace_id or None,
                    workflow_id=workflow_id or collection_id,
                    occurred_at=occurred_at,
                )
            )
            session.commit()

        self._workflow_events.record(
            WorkflowEvent(
                event_type="catalog.collection.verification_changed.v1",
                request_id=request_id or None,
                trace_id=trace_id or None,
                workflow_id=workflow_id or collection_id,
                payload={
                    "collection_id": collection_id,
                    "review_id": review_id,
                    "reviewer_user_id": actor.user_id,
                    "previous_verification_state": previous_state,
                    "next_verification_state": command.verification_state,
                    "note": command.note,
                },
                organisation_id=actor.organisation_id,
            )
        )
        return self.get_collection_verification(collection_id)

    def _history(
        self,
        session: Session,
        collection_id: str,
    ) -> list[CollectionVerificationReviewView]:
        records = (
            session.query(CollectionVerificationReviewRecord)
            .filter(CollectionVerificationReviewRecord.collection_id == collection_id)
            .order_by(CollectionVerificationReviewRecord.occurred_at.desc())
            .all()
        )
        return [self._to_review_view(record) for record in records]

    def _latest_reviews_by_collection(
        self,
        session: Session,
        collection_ids: list[str],
    ) -> dict[str, CollectionVerificationReviewRecord]:
        if not collection_ids:
            return {}
        reviews = (
            session.query(CollectionVerificationReviewRecord)
            .filter(CollectionVerificationReviewRecord.collection_id.in_(collection_ids))
            .order_by(CollectionVerificationReviewRecord.occurred_at.desc())
            .all()
        )
        latest: dict[str, CollectionVerificationReviewRecord] = {}
        for review in reviews:
            latest.setdefault(review.collection_id, review)
        return latest

    def _prompt_item_count(self, session: Session, collection_id: str) -> int:
        return (
            session.query(PromptItemRecord)
            .filter(PromptItemRecord.collection_id == collection_id)
            .count()
        )

    def _scenario_count(self, session: Session, collection_id: str) -> int:
        return (
            session.query(ScenarioRecord)
            .filter(ScenarioRecord.collection_id == collection_id)
            .count()
        )

    def _to_review_view(
        self, record: CollectionVerificationReviewRecord
    ) -> CollectionVerificationReviewView:
        return CollectionVerificationReviewView(
            review_id=record.id,
            collection_id=record.collection_id,
            reviewer_user_id=record.reviewer_user_id,
            previous_verification_state=record.previous_verification_state,
            next_verification_state=record.next_verification_state,
            note=record.note,
            request_id=record.request_id,
            trace_id=record.trace_id,
            workflow_id=record.workflow_id,
            occurred_at=record.occurred_at.isoformat(),
        )
