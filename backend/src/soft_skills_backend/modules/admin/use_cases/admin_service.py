"""Admin application facade."""

from __future__ import annotations

from sqlalchemy.orm import Session, sessionmaker

from soft_skills_backend.modules.admin.contracts.commands import (
    AdminCollectionVerificationCommand,
    AdminFeatureCollectionCommand,
    AdminLearnerRelationshipCommand,
    CreateRubricCommand,
    CreateRubricCriterionCommand,
    RubricCriterionUpdateCommand,
    UpdateRubricCommand,
)
from soft_skills_backend.modules.admin.contracts.views import (
    AdminLearnerRelationshipView,
    AttemptAuditView,
    CohortAnalyticsView,
    CollectionVerificationAuditView,
    CollectionVerificationQueueItemView,
    LearnerAnalyticsView,
    RubricView,
)
from soft_skills_backend.modules.admin.infra.analytics_repository import AdminAnalyticsRepository
from soft_skills_backend.modules.admin.infra.audit_repository import AdminAuditRepository
from soft_skills_backend.modules.admin.infra.relationship_repository import (
    AdminRelationshipRepository,
)
from soft_skills_backend.modules.admin.infra.rubric_admin_repository import RubricAdminRepository
from soft_skills_backend.modules.admin.infra.verification_repository import (
    AdminVerificationRepository,
)
from soft_skills_backend.modules.catalog.contracts.collection_views import CollectionView
from soft_skills_backend.modules.catalog.contracts.views import build_collection_view
from soft_skills_backend.platform.db.models import CollectionRecord
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
        self._rubrics = RubricAdminRepository(session_factory=session_factory)

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

    def feature_collection(
        self,
        actor: Actor,
        collection_id: str,
        command: AdminFeatureCollectionCommand,
    ) -> CollectionView:
        with self._verification._session_factory() as session:
            record = session.get(CollectionRecord, collection_id)
            if record is None:
                from soft_skills_backend.shared.errors import domain_error

                raise domain_error(
                    "Collection was not found",
                    code="SS-DOMAIN-005",
                    status_code=404,
                    details={"collection_id": collection_id},
                )
            if record.organisation_id != actor.organisation_id:
                from soft_skills_backend.shared.errors import auth_error

                raise auth_error(
                    "Collection does not belong to this organisation",
                    code="SS-AUTH-008",
                    status_code=403,
                    details={"collection_id": collection_id},
                )
            record.featured = command.featured
            session.commit()
            return build_collection_view(session, record, actor=actor)

    def list_rubrics(self, actor: Actor) -> list[RubricView]:
        return self._rubrics.list_rubrics()

    def get_rubric(self, actor: Actor, rubric_id: str) -> RubricView:
        return self._rubrics.get_rubric(rubric_id)

    def create_rubric(self, actor: Actor, command: CreateRubricCommand) -> RubricView:
        return self._rubrics.create_rubric(command)

    def update_rubric(
        self, actor: Actor, rubric_id: str, command: UpdateRubricCommand
    ) -> RubricView:
        return self._rubrics.update_rubric(rubric_id, command)

    def delete_rubric(self, actor: Actor, rubric_id: str) -> None:
        self._rubrics.delete_rubric(rubric_id)

    def create_rubric_criterion(
        self, actor: Actor, rubric_id: str, command: CreateRubricCriterionCommand
    ) -> RubricView:
        return self._rubrics.create_criterion(rubric_id, command)

    def update_rubric_criterion(
        self,
        actor: Actor,
        rubric_id: str,
        criterion_ref: str,
        command: RubricCriterionUpdateCommand,
    ) -> RubricView:
        return self._rubrics.update_criterion(rubric_id, criterion_ref, command)

    def delete_rubric_criterion(
        self, actor: Actor, rubric_id: str, criterion_ref: str
    ) -> RubricView:
        return self._rubrics.delete_criterion(rubric_id, criterion_ref)
