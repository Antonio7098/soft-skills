"""Admin application facade."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import func, or_
from sqlalchemy.orm import Session, sessionmaker

from soft_skills_backend.config import Settings
from soft_skills_backend.modules.admin.contracts.commands import (
    AdminAddUserCommand,
    AdminCollectionVerificationCommand,
    AdminFeatureCollectionCommand,
    AdminLearnerRelationshipCommand,
    AdminUserRoleCommand,
    AdminUserStatusCommand,
    ArchivePromptCommand,
    BulkUserOperationCommand,
    ComparePromptsCommand,
    CreatePromptCommand,
    CreateRubricCommand,
    CreateRubricCriterionCommand,
    PublishPromptCommand,
    RubricCriterionUpdateCommand,
    UpdatePromptCommand,
    UpdateRubricCommand,
)
from soft_skills_backend.modules.admin.contracts.views import (
    AdminLearnerRelationshipView,
    AdminUserListView,
    AdminUserView,
    AnalyticsOverviewView,
    AttemptAuditView,
    BulkOperationResultView,
    CohortAnalyticsView,
    CohortComparisonView,
    CollectionVerificationAuditView,
    CollectionVerificationQueueItemView,
    LearnerAnalyticsView,
    PipelineDAGView,
    PipelineDefinitionView,
    PipelineMetricsView,
    PipelineRunSummaryView,
    PipelineTraceView,
    PromptAnalyticsView,
    PromptCompareView,
    PromptSummaryView,
    PromptVersionView,
    RubricView,
    StageDefinitionView,
    StageExecutionEventView,
    StageMetricsView,
    TelemetryOverviewView,
    TelemetryTraceListView,
    TelemetryTraceView,
    UserActivityView,
    UserAttemptSummaryView,
    UserLoginEventView,
    UserSessionView,
)
from soft_skills_backend.modules.admin.infra.analytics_repository import AdminAnalyticsRepository
from soft_skills_backend.modules.admin.infra.audit_repository import AdminAuditRepository
from soft_skills_backend.modules.admin.infra.prompt_repository import PromptRepository
from soft_skills_backend.modules.admin.infra.relationship_repository import (
    AdminRelationshipRepository,
)
from soft_skills_backend.modules.admin.infra.rubric_admin_repository import RubricAdminRepository
from soft_skills_backend.modules.admin.infra.verification_repository import (
    AdminVerificationRepository,
)
from soft_skills_backend.modules.admin.use_cases.prompt_service import PromptService
from soft_skills_backend.modules.catalog.contracts.collection_views import CollectionView
from soft_skills_backend.modules.catalog.contracts.views import build_collection_view
from soft_skills_backend.platform.db.models import (
    AttemptRecord,
    CollectionRecord,
    OrganisationMembershipRecord,
    PracticeSessionRecord,
    UserAccountRecord,
    WorkflowEventRecord,
)
from soft_skills_backend.platform.db.repositories import (
    SqlAlchemyPipelineDefinitionRepository,
    SqlAlchemyPipelineExecutionTraceRepository,
    SqlAlchemyPipelineRunRepository,
    SqlAlchemyStageDefinitionRepository,
    SqlAlchemyWorkflowEventRepository,
)
from soft_skills_backend.platform.observability.events import WorkflowEvent
from soft_skills_backend.shared.auth import Actor


class AdminService:
    """Feature facade for admin-only verification, analytics, and audit APIs."""

    def __init__(
        self,
        *,
        settings: Settings | None = None,
        session_factory: sessionmaker[Session],
        workflow_events: SqlAlchemyWorkflowEventRepository,
        prompt_repository: PromptRepository | None = None,
        pipeline_definitions: SqlAlchemyPipelineDefinitionRepository | None = None,
        stage_definitions: SqlAlchemyStageDefinitionRepository | None = None,
        pipeline_execution_traces: SqlAlchemyPipelineExecutionTraceRepository | None = None,
        pipeline_runs: SqlAlchemyPipelineRunRepository | None = None,
    ) -> None:
        self._session_factory = session_factory
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
        self._prompts = (
            PromptService(
                settings=settings,
                prompts=prompt_repository or PromptRepository(session_factory),
            )
            if settings is not None
            else None
        )
        self._pipeline_definitions = pipeline_definitions
        self._stage_definitions = stage_definitions
        self._pipeline_execution_traces = pipeline_execution_traces
        self._pipeline_runs = pipeline_runs
        self._workflow_events = workflow_events

    def list_users(
        self,
        actor: Actor,
        *,
        offset: int = 0,
        limit: int = 50,
        search: str | None = None,
        role: str | None = None,
        is_active: bool | None = None,
    ) -> AdminUserListView:
        """List users in the organisation with pagination and filters."""
        with self._session_factory() as session:
            query = (
                session.query(UserAccountRecord)
                .join(
                    OrganisationMembershipRecord,
                    UserAccountRecord.id == OrganisationMembershipRecord.user_id,
                    isouter=True,
                )
                .filter(
                    or_(
                        OrganisationMembershipRecord.organisation_id == actor.organisation_id,
                        OrganisationMembershipRecord.organisation_id.is_(None),
                    )
                )
            )

            if actor.organisation_id is not None:
                query = query.filter(
                    or_(
                        OrganisationMembershipRecord.organisation_id == actor.organisation_id,
                        UserAccountRecord.id.in_(
                            session.query(OrganisationMembershipRecord.user_id).filter(
                                OrganisationMembershipRecord.organisation_id
                                == actor.organisation_id
                            )
                        ),
                    )
                )

            if search:
                search_pattern = f"%{search.lower()}%"
                query = query.filter(
                    or_(
                        func.lower(UserAccountRecord.email).like(search_pattern),
                        func.lower(UserAccountRecord.display_name).like(search_pattern),
                    )
                )

            if role is not None:
                query = query.filter(OrganisationMembershipRecord.role == role)

            if is_active is not None:
                query = query.filter(UserAccountRecord.is_active == is_active)

            total = query.count()
            users = query.offset(offset).limit(limit).all()

            user_views = []
            for user in users:
                membership = None
                if actor.organisation_id is not None:
                    membership = (
                        session.query(OrganisationMembershipRecord)
                        .filter(
                            OrganisationMembershipRecord.user_id == user.id,
                            OrganisationMembershipRecord.organisation_id == actor.organisation_id,
                        )
                        .first()
                    )

                user_views.append(
                    AdminUserView(
                        user_id=user.id,
                        email=user.email,
                        display_name=user.display_name,
                        auth_provider=user.auth_provider,
                        is_active=user.is_active,
                        organisation_id=membership.organisation_id if membership else None,
                        organisation_role=membership.role if membership else None,
                        created_at=user.created_at.isoformat() if user.created_at else None,
                    )
                )

            return AdminUserListView(
                users=user_views,
                total=total,
                offset=offset,
                limit=limit,
            )

    def get_user(self, actor: Actor, user_id: str) -> AdminUserView | None:
        """Get a specific user by ID."""
        with self._session_factory() as session:
            user = session.get(UserAccountRecord, user_id)
            if user is None:
                return None

            membership = None
            if actor.organisation_id is not None:
                membership = (
                    session.query(OrganisationMembershipRecord)
                    .filter(
                        OrganisationMembershipRecord.user_id == user_id,
                        OrganisationMembershipRecord.organisation_id == actor.organisation_id,
                    )
                    .first()
                )

            return AdminUserView(
                user_id=user.id,
                email=user.email,
                display_name=user.display_name,
                auth_provider=user.auth_provider,
                is_active=user.is_active,
                organisation_id=membership.organisation_id if membership else None,
                organisation_role=membership.role if membership else None,
                created_at=user.created_at.isoformat() if user.created_at else None,
            )

    def update_user_role(
        self,
        actor: Actor,
        user_id: str,
        command: AdminUserRoleCommand,
    ) -> AdminUserView:
        """Change a user's role within the organisation."""
        if actor.organisation_id is None:
            from soft_skills_backend.shared.errors import auth_error

            raise auth_error(
                "Organisation context is required",
                code="SS-AUTH-010",
                status_code=400,
            )

        with self._session_factory() as session:
            user = session.get(UserAccountRecord, user_id)
            if user is None:
                from soft_skills_backend.shared.errors import domain_error

                raise domain_error(
                    "User was not found",
                    code="SS-DOMAIN-003",
                    status_code=404,
                    details={"user_id": user_id},
                )

            membership = (
                session.query(OrganisationMembershipRecord)
                .filter(
                    OrganisationMembershipRecord.user_id == user_id,
                    OrganisationMembershipRecord.organisation_id == actor.organisation_id,
                )
                .first()
            )

            if membership is None:
                from soft_skills_backend.shared.errors import domain_error

                raise domain_error(
                    "User is not a member of this organisation",
                    code="SS-DOMAIN-006",
                    status_code=404,
                    details={"user_id": user_id},
                )

            old_role = membership.role
            membership.role = command.role
            session.commit()

            self._workflow_events.record(
                WorkflowEvent(
                    event_type="admin.user.role_changed.v1",
                    payload={
                        "admin_user_id": actor.user_id,
                        "target_user_id": user_id,
                        "organisation_id": actor.organisation_id,
                        "old_role": old_role,
                        "new_role": command.role,
                    },
                )
            )

            return AdminUserView(
                user_id=user.id,
                email=user.email,
                display_name=user.display_name,
                auth_provider=user.auth_provider,
                is_active=user.is_active,
                organisation_id=membership.organisation_id,
                organisation_role=membership.role,
                created_at=user.created_at.isoformat() if user.created_at else None,
            )

    def update_user_status(
        self,
        actor: Actor,
        user_id: str,
        command: AdminUserStatusCommand,
    ) -> AdminUserView:
        """Suspend or activate a user."""
        with self._session_factory() as session:
            user = session.get(UserAccountRecord, user_id)
            if user is None:
                from soft_skills_backend.shared.errors import domain_error

                raise domain_error(
                    "User was not found",
                    code="SS-DOMAIN-003",
                    status_code=404,
                    details={"user_id": user_id},
                )

            user.is_active = command.is_active
            session.commit()

            self._workflow_events.record(
                WorkflowEvent(
                    event_type="admin.user.suspended.v1"
                    if not command.is_active
                    else "admin.user.activated.v1",
                    payload={
                        "admin_user_id": actor.user_id,
                        "target_user_id": user_id,
                        "organisation_id": actor.organisation_id,
                        "is_active": command.is_active,
                    },
                )
            )

            membership = None
            if actor.organisation_id is not None:
                membership = (
                    session.query(OrganisationMembershipRecord)
                    .filter(
                        OrganisationMembershipRecord.user_id == user_id,
                        OrganisationMembershipRecord.organisation_id == actor.organisation_id,
                    )
                    .first()
                )

            return AdminUserView(
                user_id=user.id,
                email=user.email,
                display_name=user.display_name,
                auth_provider=user.auth_provider,
                is_active=user.is_active,
                organisation_id=membership.organisation_id if membership else None,
                organisation_role=membership.role if membership else None,
                created_at=user.created_at.isoformat() if user.created_at else None,
            )

    def add_user_to_org(
        self,
        actor: Actor,
        command: AdminAddUserCommand,
    ) -> AdminUserView:
        """Add a user to an organisation."""
        if actor.organisation_id is None:
            from soft_skills_backend.shared.errors import auth_error

            raise auth_error(
                "Organisation context is required",
                code="SS-AUTH-010",
                status_code=400,
            )

        with self._session_factory() as session:
            user = (
                session.query(UserAccountRecord)
                .filter(func.lower(UserAccountRecord.email) == command.email.lower())
                .first()
            )

            if user is None:
                now = datetime.now(UTC)
                user = UserAccountRecord(
                    id=uuid4().hex,
                    email=command.email,
                    display_name=command.email.split("@")[0],
                    auth_provider="internal",
                    auth_subject=command.email,
                    is_active=True,
                    created_at=now,
                )
                session.add(user)
                session.flush()

                self._workflow_events.record(
                    WorkflowEvent(
                        event_type="identity.user_registered.v1",
                        payload={"user_id": user.id, "email": user.email},
                    )
                )

            existing_membership = (
                session.query(OrganisationMembershipRecord)
                .filter(
                    OrganisationMembershipRecord.user_id == user.id,
                    OrganisationMembershipRecord.organisation_id == actor.organisation_id,
                )
                .first()
            )

            if existing_membership is not None:
                from soft_skills_backend.shared.errors import domain_error

                raise domain_error(
                    "User is already a member of this organisation",
                    code="SS-DOMAIN-007",
                    status_code=409,
                    details={"user_id": user.id, "organisation_id": actor.organisation_id},
                )

            membership = OrganisationMembershipRecord(
                organisation_id=actor.organisation_id,
                user_id=user.id,
                role=command.role,
                joined_at=datetime.now(UTC),
            )
            session.add(membership)
            session.commit()

            self._workflow_events.record(
                WorkflowEvent(
                    event_type="admin.user.added_to_org.v1",
                    payload={
                        "admin_user_id": actor.user_id,
                        "target_user_id": user.id,
                        "organisation_id": actor.organisation_id,
                        "role": command.role,
                    },
                )
            )

            return AdminUserView(
                user_id=user.id,
                email=user.email,
                display_name=user.display_name,
                auth_provider=user.auth_provider,
                is_active=user.is_active,
                organisation_id=membership.organisation_id,
                organisation_role=membership.role,
                created_at=user.created_at.isoformat() if user.created_at else None,
            )

    def bulk_user_operation(
        self,
        actor: Actor,
        command: BulkUserOperationCommand,
    ) -> BulkOperationResultView:
        """Perform bulk operations on users."""
        success_count = 0
        failure_count = 0
        failed_user_ids = []

        for user_id in command.user_ids:
            try:
                if command.operation == "suspend":
                    self.update_user_status(
                        actor,
                        user_id,
                        AdminUserStatusCommand(is_active=False),
                    )
                    success_count += 1
                elif command.operation == "activate":
                    self.update_user_status(
                        actor,
                        user_id,
                        AdminUserStatusCommand(is_active=True),
                    )
                    success_count += 1
                elif command.operation == "change_role":
                    if command.payload is None or "role" not in command.payload:
                        raise ValueError("role is required in payload for change_role operation")
                    self.update_user_role(
                        actor,
                        user_id,
                        AdminUserRoleCommand(role=str(command.payload["role"])),
                    )
                    success_count += 1
                else:
                    failure_count += 1
                    failed_user_ids.append(user_id)
            except Exception:
                failure_count += 1
                failed_user_ids.append(user_id)

        return BulkOperationResultView(
            operation=command.operation,
            requested_count=len(command.user_ids),
            success_count=success_count,
            failure_count=failure_count,
            failed_user_ids=failed_user_ids,
        )

    def get_user_activity(self, actor: Actor, user_id: str) -> UserActivityView | None:
        """Get activity summary for a user."""
        with self._session_factory() as session:
            user = session.get(UserAccountRecord, user_id)
            if user is None:
                return None

            membership = None
            if actor.organisation_id is not None:
                membership = (
                    session.query(OrganisationMembershipRecord)
                    .filter(
                        OrganisationMembershipRecord.user_id == user_id,
                        OrganisationMembershipRecord.organisation_id == actor.organisation_id,
                    )
                    .first()
                )

            sessions = (
                session.query(PracticeSessionRecord)
                .filter(PracticeSessionRecord.user_id == user_id)
                .order_by(PracticeSessionRecord.created_at.desc())
                .limit(10)
                .all()
            )

            attempts = (
                session.query(AttemptRecord)
                .filter(AttemptRecord.user_id == user_id)
                .order_by(AttemptRecord.created_at.desc())
                .limit(10)
                .all()
            )

            login_events = (
                session.query(WorkflowEventRecord)
                .filter(
                    WorkflowEventRecord.payload.contains({"user_id": user_id}),
                    WorkflowEventRecord.event_type.like("auth.login%"),
                )
                .order_by(WorkflowEventRecord.occurred_at.desc())
                .limit(10)
                .all()
            )

            total_sessions = (
                session.query(PracticeSessionRecord)
                .filter(PracticeSessionRecord.user_id == user_id)
                .count()
            )

            total_attempts = (
                session.query(AttemptRecord).filter(AttemptRecord.user_id == user_id).count()
            )

            session_views = [
                UserSessionView(
                    session_id=s.id,
                    practice_type=s.practice_type,
                    content_item_id=s.content_item_id,
                    status=s.status,
                    created_at=s.created_at.isoformat() if s.created_at else None,
                    completed_at=s.completed_at.isoformat() if s.completed_at else None,
                )
                for s in sessions
            ]

            attempt_views = [
                UserAttemptSummaryView(
                    attempt_id=a.id,
                    session_id=a.session_id,
                    practice_type=a.practice_type,
                    content_item_id=a.content_item_id,
                    content_item_type=a.content_item_type,
                    status=a.status,
                    overall_score=None,
                    submitted_at=a.submitted_at.isoformat() if a.submitted_at else None,
                    assessed_at=a.assessed_at.isoformat() if a.assessed_at else None,
                )
                for a in attempts
            ]

            login_views = [
                UserLoginEventView(
                    event_type=e.event_type,
                    occurred_at=e.occurred_at.isoformat() if e.occurred_at else None,
                    trace_id=e.trace_id,
                )
                for e in login_events
            ]

            return UserActivityView(
                user_id=user.id,
                email=user.email,
                display_name=user.display_name,
                organisation_id=membership.organisation_id if membership else None,
                organisation_role=membership.role if membership else None,
                total_sessions=total_sessions,
                total_attempts=total_attempts,
                recent_sessions=session_views,
                recent_attempts=attempt_views,
                recent_logins=login_views,
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

    def get_learner_analytics(
        self,
        actor: Actor,
        learner_id: str,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
    ) -> LearnerAnalyticsView:
        return self._analytics.get_learner_analytics(
            learner_id,
            organisation_id=actor.organisation_id,
            from_date=from_date,
            to_date=to_date,
        )

    def get_cohort_analytics(
        self,
        actor: Actor,
        target_role: str | None,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
    ) -> CohortAnalyticsView:
        return self._analytics.get_cohort_analytics(
            target_role,
            organisation_id=actor.organisation_id,
            from_date=from_date,
            to_date=to_date,
        )

    def get_analytics_overview(
        self,
        actor: Actor,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
    ) -> AnalyticsOverviewView:
        return self._analytics.get_analytics_overview(
            organisation_id=actor.organisation_id,
            from_date=from_date,
            to_date=to_date,
        )

    def get_cohort_comparison(
        self,
        actor: Actor,
        cohort_keys: list[str],
        from_date: datetime | None = None,
        to_date: datetime | None = None,
    ) -> CohortComparisonView:
        return self._analytics.get_cohort_comparison(
            cohort_keys=cohort_keys,
            organisation_id=actor.organisation_id,
            from_date=from_date,
            to_date=to_date,
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

    def list_prompts(self, actor: Actor) -> list[PromptSummaryView]:
        return self._require_prompt_service().list_prompts(actor)

    def list_prompt_versions(self, actor: Actor, name: str) -> list[PromptVersionView]:
        return self._require_prompt_service().list_versions(actor, name)

    def get_prompt_version(self, actor: Actor, name: str, version: str) -> PromptVersionView | None:
        return self._require_prompt_service().get_version(actor, name, version)

    def create_prompt(self, actor: Actor, command: CreatePromptCommand) -> PromptVersionView:
        return self._require_prompt_service().create_prompt(actor, command)

    def update_prompt(
        self,
        actor: Actor,
        name: str,
        version: str,
        command: UpdatePromptCommand,
    ) -> PromptVersionView | None:
        return self._require_prompt_service().update_prompt(actor, name, version, command)

    def publish_prompt(
        self,
        actor: Actor,
        name: str,
        version: str,
        command: PublishPromptCommand,
    ) -> PromptVersionView | None:
        return self._require_prompt_service().publish_prompt(actor, name, version, command)

    def archive_prompt(
        self,
        actor: Actor,
        name: str,
        version: str,
        command: ArchivePromptCommand,
    ) -> PromptVersionView | None:
        return self._require_prompt_service().archive_prompt(actor, name, version, command)

    def get_prompt_analytics(
        self, actor: Actor, name: str, version: str
    ) -> PromptAnalyticsView | None:
        return self._require_prompt_service().get_analytics(actor, name, version)

    def compare_prompts(
        self,
        actor: Actor,
        command: ComparePromptsCommand,
    ) -> PromptCompareView | None:
        return self._require_prompt_service().compare_prompts(actor, command)

    def _require_prompt_service(self) -> PromptService:
        if self._prompts is None:
            raise RuntimeError("PromptService was not configured for this AdminService instance")
        return self._prompts

    def list_pipelines(self, actor: Actor) -> list[PipelineDefinitionView]:
        """List all registered pipeline definitions."""
        if self._pipeline_definitions is None:
            return []
        records = self._pipeline_definitions.list_all()
        return [
            PipelineDefinitionView(
                pipeline_name=r.pipeline_name,
                topology=r.topology,
                description=r.description,
                stage_count=len(r.stage_definitions),
                created_at=r.created_at.isoformat() if r.created_at else None,
                updated_at=r.updated_at.isoformat() if r.updated_at else None,
            )
            for r in records
        ]

    def get_pipeline_dag(self, actor: Actor, pipeline_name: str) -> PipelineDAGView | None:
        """Get full pipeline DAG with stages and dependencies."""
        if self._pipeline_definitions is None or self._stage_definitions is None:
            return None
        definition = self._pipeline_definitions.get_by_name(pipeline_name)
        if definition is None:
            return None
        stage_records = self._stage_definitions.get_by_pipeline(pipeline_name)
        stages = [
            StageDefinitionView(
                name=s.stage_name,
                kind=s.stage_kind,
                dependencies=s.dependencies,
                runner_class=s.runner_class,
                description=s.description,
            )
            for s in stage_records
        ]
        return PipelineDAGView(
            pipeline_name=definition.pipeline_name,
            topology=definition.topology,
            description=definition.description,
            stages=stages,
        )

    def list_pipeline_runs(
        self, actor: Actor, pipeline_name: str, *, offset: int = 0, limit: int = 50
    ) -> list[PipelineRunSummaryView]:
        """List recent runs for a pipeline."""
        if self._pipeline_execution_traces is None or self._pipeline_runs is None:
            return []
        trace_records = self._pipeline_execution_traces.get_by_pipeline(
            pipeline_name, offset=offset, limit=limit
        )
        run_records = self._pipeline_runs.list_by_pipeline(
            pipeline_name, offset=offset, limit=limit
        )
        run_map = {r.pipeline_run_id: r for r in run_records}
        result = []
        for trace in trace_records:
            run = run_map.get(trace.pipeline_run_id)
            result.append(
                PipelineRunSummaryView(
                    pipeline_run_id=trace.pipeline_run_id,
                    pipeline_name=trace.pipeline_name,
                    status=run.status if run else "unknown",
                    execution_mode=run.execution_mode if run else None,
                    user_id=run.user_id if run else None,
                    request_id=run.request_id if run else None,
                    trace_id=run.trace_id if run else None,
                    error=None,
                    failed_stage=run.failed_stage if run else None,
                    started_at=trace.started_at.isoformat() if trace.started_at else None,
                    finished_at=trace.completed_at.isoformat() if trace.completed_at else None,
                    duration_ms=trace.total_duration_ms,
                )
            )
        return result

    def get_pipeline_trace(
        self, actor: Actor, pipeline_name: str, pipeline_run_id: str
    ) -> PipelineTraceView | None:
        """Get execution trace for a specific pipeline run."""
        if self._pipeline_execution_traces is None:
            return None
        trace = self._pipeline_execution_traces.get_by_run_id(pipeline_run_id)
        if trace is None or trace.pipeline_name != pipeline_name:
            return None
        events = [
            StageExecutionEventView(
                stage_name=e.get("stage_name", ""),
                event_type=e.get("event_type", ""),
                timestamp=e.get("timestamp", ""),
                duration_ms=e.get("duration_ms"),
                status=e.get("status"),
                error=e.get("error"),
            )
            for e in trace.execution_sequence
        ]
        return PipelineTraceView(
            pipeline_run_id=trace.pipeline_run_id,
            pipeline_name=trace.pipeline_name,
            execution_sequence=events,
            total_duration_ms=trace.total_duration_ms,
            started_at=trace.started_at.isoformat() if trace.started_at else None,
            completed_at=trace.completed_at.isoformat() if trace.completed_at else None,
        )

    def get_pipeline_metrics(self, actor: Actor, pipeline_name: str) -> PipelineMetricsView | None:
        """Get aggregate stage metrics for a pipeline."""
        if self._pipeline_execution_traces is None or self._pipeline_runs is None:
            return None
        runs = self._pipeline_runs.list_by_pipeline(pipeline_name, offset=0, limit=1000)
        if not runs:
            return PipelineMetricsView(pipeline_name=pipeline_name, total_runs=0)
        traces = self._pipeline_execution_traces.get_by_pipeline(
            pipeline_name, offset=0, limit=1000
        )
        traces_by_run_id = {t.pipeline_run_id: t for t in traces}
        success_count = sum(1 for r in runs if r.status == "completed")
        failure_count = sum(1 for r in runs if r.status == "failed")
        cancel_count = sum(1 for r in runs if r.status == "cancelled")

        invocation_counts: dict[str, int] = {}
        success_counts: dict[str, int] = {}
        failure_counts: dict[str, int] = {}
        skip_counts: dict[str, int] = {}
        cancel_counts: dict[str, int] = {}
        retry_counts: dict[str, int] = {}
        stage_durations: dict[str, list[int]] = {}

        for run in runs:
            trace = traces_by_run_id.get(run.pipeline_run_id)
            if trace is None:
                continue
            for event in trace.execution_sequence:
                stage_name = event.get("stage_name", "unknown")
                if stage_name not in invocation_counts:
                    invocation_counts[stage_name] = 0
                    success_counts[stage_name] = 0
                    failure_counts[stage_name] = 0
                    skip_counts[stage_name] = 0
                    cancel_counts[stage_name] = 0
                    retry_counts[stage_name] = 0
                    stage_durations[stage_name] = []
                invocation_counts[stage_name] += 1
                status = event.get("status", "unknown")
                if status == "completed":
                    success_counts[stage_name] += 1
                elif status == "failed":
                    failure_counts[stage_name] += 1
                elif status == "skipped":
                    skip_counts[stage_name] += 1
                elif status == "cancelled":
                    cancel_counts[stage_name] += 1
                duration = event.get("duration_ms")
                if duration is not None:
                    stage_durations[stage_name].append(duration)

        stage_metrics_views = []
        for stage_name in invocation_counts:
            durations = sorted(stage_durations.get(stage_name, []))
            p50_idx = len(durations) // 2
            p95_idx = int(len(durations) * 0.95)
            p99_idx = int(len(durations) * 0.99)
            avg_duration = sum(durations) / len(durations) if durations else None
            stage_metrics_views.append(
                StageMetricsView(
                    stage_name=stage_name,
                    invocation_count=invocation_counts[stage_name],
                    success_count=success_counts[stage_name],
                    failure_count=failure_counts[stage_name],
                    skip_count=skip_counts[stage_name],
                    cancel_count=cancel_counts[stage_name],
                    retry_count=retry_counts[stage_name],
                    avg_duration_ms=avg_duration,
                    p50_duration_ms=durations[p50_idx] if durations else None,
                    p95_duration_ms=durations[p95_idx] if durations else None,
                    p99_duration_ms=durations[p99_idx] if durations else None,
                )
            )
        return PipelineMetricsView(
            pipeline_name=pipeline_name,
            total_runs=len(runs),
            success_count=success_count,
            failure_count=failure_count,
            cancel_count=cancel_count,
            stage_metrics=stage_metrics_views,
        )

    def get_telemetry_overview(
        self,
        actor: Actor,
        organisation_id: str | None = None,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
    ) -> TelemetryOverviewView:
        resolved_org = organisation_id or actor.organisation_id
        if resolved_org is None:
            raise domain_error(
                "Organisation ID is required for telemetry",
                code="SS-ADMIN-050",
                status_code=400,
            )
        return self._analytics.get_telemetry_overview(
            organisation_id=resolved_org,
            from_date=from_date,
            to_date=to_date,
        )

    def list_telemetry_traces(
        self,
        actor: Actor,
        organisation_id: str | None = None,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> TelemetryTraceListView:
        resolved_org = organisation_id or actor.organisation_id
        if resolved_org is None:
            raise domain_error(
                "Organisation ID is required for telemetry",
                code="SS-ADMIN-051",
                status_code=400,
            )
        return self._analytics.list_telemetry_traces(
            organisation_id=resolved_org,
            from_date=from_date,
            to_date=to_date,
            offset=offset,
            limit=limit,
        )

    def get_telemetry_trace(
        self,
        actor: Actor,
        trace_id: str,
    ) -> TelemetryTraceView | None:
        resolved_org = actor.organisation_id
        if resolved_org is None:
            raise domain_error(
                "Organisation ID is required for telemetry",
                code="SS-ADMIN-052",
                status_code=400,
            )
        trace = self._analytics.get_telemetry_trace(trace_id)
        if trace is None:
            return None
        if trace.organisation_id and trace.organisation_id != resolved_org:
            trace_ids = self._analytics._organisation_trace_ids(
                self._session_factory().__call__(), resolved_org
            )
            if trace_id not in trace_ids:
                raise domain_error(
                    "Trace not found",
                    code="SS-ADMIN-053",
                    status_code=404,
                    details={"trace_id": trace_id},
                )
        return trace
