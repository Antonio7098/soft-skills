"""Admin application facade."""

from __future__ import annotations

from sqlalchemy.orm import Session, sessionmaker

from soft_skills_backend.modules.admin.contracts.commands import (
    AdminCollectionVerificationCommand,
    AdminLearnerRelationshipCommand,
)
from soft_skills_backend.modules.admin.contracts.views import (
    AdminLearnerRelationshipView,
    AttemptAuditView,
    CohortAnalyticsView,
    CollectionVerificationAuditView,
    CollectionVerificationQueueItemView,
    LearnerAnalyticsView,
)
from soft_skills_backend.modules.admin.infra.analytics_repository import AdminAnalyticsRepository
from soft_skills_backend.modules.admin.infra.audit_repository import AdminAuditRepository
from soft_skills_backend.modules.admin.infra.relationship_repository import (
    AdminRelationshipRepository,
)
from soft_skills_backend.modules.admin.infra.verification_repository import (
    AdminVerificationRepository,
)
from soft_skills_backend.platform.db.repositories import SqlAlchemyWorkflowEventRepository
from soft_skills_backend.shared.auth import Actor


class AdminService:
    """Feature facade for admin-only verification, analytics, and audit APIs."""

    def __init__(
        self,
        *,
        session_factory: sessionmaker[Session],
        workflow_events: SqlAlchemyWorkflowEventRepository,
    ) -> None:
        relationships = AdminRelationshipRepository(session_factory=session_factory)
        self._verification = AdminVerificationRepository(
            session_factory=session_factory,
            workflow_events=workflow_events,
        )
        self._analytics = AdminAnalyticsRepository(session_factory=session_factory)
        self._relationships = relationships
        self._audit = AdminAuditRepository(
            session_factory=session_factory,
            relationships=relationships,
        )

    def list_collection_verification_queue(
        self, actor: Actor
    ) -> list[CollectionVerificationQueueItemView]:
        return self._verification.list_verification_queue(organisation_id=actor.organisation_id)

    def get_collection_verification(
        self,
        actor: Actor,
        collection_id: str,
    ) -> CollectionVerificationAuditView:
        return self._verification.get_collection_verification(
            collection_id, organisation_id=actor.organisation_id
        )

    def update_collection_verification(
        self,
        actor: Actor,
        *,
        request_id: str,
        trace_id: str,
        workflow_id: str | None,
        collection_id: str,
        command: AdminCollectionVerificationCommand,
    ) -> CollectionVerificationAuditView:
        return self._verification.update_verification(
            actor,
            request_id=request_id,
            trace_id=trace_id,
            workflow_id=workflow_id,
            collection_id=collection_id,
            command=command,
        )

    def get_learner_analytics(self, actor: Actor, learner_id: str) -> LearnerAnalyticsView:
        return self._analytics.get_learner_analytics(
            learner_id, organisation_id=actor.organisation_id
        )

    def get_cohort_analytics(self, actor: Actor, target_role: str | None) -> CohortAnalyticsView:
        return self._analytics.get_cohort_analytics(
            target_role, organisation_id=actor.organisation_id
        )

    def get_attempt_audit(self, actor: Actor, attempt_id: str) -> AttemptAuditView:
        return self._audit.get_attempt_audit(actor, attempt_id)

    def get_learner_relationship(
        self,
        actor: Actor,
        learner_id: str,
    ) -> AdminLearnerRelationshipView | None:
        return self._relationships.get_relationship(
            admin_user_id=actor.user_id,
            learner_user_id=learner_id,
        )

    def upsert_learner_relationship(
        self,
        actor: Actor,
        *,
        learner_id: str,
        command: AdminLearnerRelationshipCommand,
    ) -> AdminLearnerRelationshipView:
        return self._relationships.upsert_relationship(
            actor,
            learner_user_id=learner_id,
            command=command,
        )

    def delete_learner_relationship(self, actor: Actor, *, learner_id: str) -> None:
        self._relationships.delete_relationship(actor, learner_user_id=learner_id)
