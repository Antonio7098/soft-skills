"""Progression repository facade."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker
from stageflow.core import StageContext

from soft_skills_backend.modules.catalog.domain.validators import can_view_collection
from soft_skills_backend.modules.progression.contracts.views import (
    ProgressDashboardView,
    ProgressRecalculationView,
    ProgressSnapshotView,
    RecommendationView,
)
from soft_skills_backend.modules.progression.domain.progression import (
    PROGRESSION_CONFIG_VERSION,
    PROGRESSION_ENGINE_VERSION,
    PROGRESSION_EVIDENCE_LEDGER_SCHEMA_VERSION,
    PROGRESSION_SCHEMA_VERSION,
    RECOMMENDATION_CONFIG_VERSION,
    RECOMMENDATION_ENGINE_VERSION,
    RECOMMENDATION_SCHEMA_VERSION,
    AssessmentEvidenceSignal,
    AssessmentSignal,
    AssessmentSkillScoreSignal,
    CatalogCandidate,
    CompetencyDefinition,
    ComputedProgressSnapshot,
    ComputedRecommendation,
    LearnerProfileInput,
    build_prior_progress_state,
    diff_summary,
)
from soft_skills_backend.platform.db.models import (
    AssessmentRecord,
    AttemptRecord,
    CollectionRecord,
    CompetencyRecord,
    CompetencySkillMapRecord,
    LearnerProfileRecord,
    OrganisationMembershipRecord,
    ProgressionSnapshotRecord,
    ProgressRecalculationRecord,
    PromptItemRecord,
    RecommendationArtifactRecord,
    ScenarioRecord,
    SkillRecord,
)
from soft_skills_backend.platform.db.repositories import SqlAlchemyWorkflowEventRepository
from soft_skills_backend.platform.workflows.stageflow import (
    metadata_value,
    request_id_from_context,
)
from soft_skills_backend.shared.auth import Actor
from soft_skills_backend.shared.errors import (
    auth_error,
    domain_error,
    persistence_error,
    validation_error,
)

from .events import ProgressionEventRecorder


def _utcnow() -> datetime:
    return datetime.now(UTC)


@dataclass(frozen=True, slots=True)
class ProgressionRefreshInput:
    """All inputs required for a progression refresh."""

    learner: LearnerProfileInput
    source_assessment: AssessmentSignal
    assessments: list[AssessmentSignal]
    skill_slugs: list[str]
    competency_definitions: list[CompetencyDefinition]
    previous_state_payload: dict[str, object] | None


@dataclass(frozen=True, slots=True)
class ProgressionPersistedArtifacts:
    """Persisted snapshot + recommendation pair."""

    snapshot: ProgressSnapshotView
    recommendation: RecommendationView


class ProgressionRepository:
    """Coordinate progression queries and persistence."""

    def __init__(
        self,
        *,
        session_factory: sessionmaker[Session],
        workflow_events: SqlAlchemyWorkflowEventRepository,
    ) -> None:
        self._session_factory = session_factory
        self._events = ProgressionEventRecorder(workflow_events)

    def load_refresh_input(self, assessment_id: str) -> ProgressionRefreshInput:
        with self._session_factory() as session:
            assessment_record = session.get(AssessmentRecord, assessment_id)
            if assessment_record is None:
                raise domain_error(
                    "Assessment was not found for progression refresh",
                    code="SS-DOMAIN-018",
                    status_code=404,
                    details={"assessment_id": assessment_id},
                )
            if assessment_record.validation_status != "validated":
                raise validation_error(
                    "Only validated assessments may update progression",
                    code="SS-VALIDATION-033",
                    details={"assessment_id": assessment_id},
                )
            if assessment_record.practice_type == "quick_practice":
                raise validation_error(
                    "Quick-practice assessments do not update progression",
                    code="SS-VALIDATION-074",
                    details={
                        "assessment_id": assessment_id,
                        "practice_type": assessment_record.practice_type,
                    },
                )
            learner_profile = session.get(LearnerProfileRecord, assessment_record.user_id)
            if learner_profile is None:
                raise domain_error(
                    "Learner profile is missing",
                    code="SS-DOMAIN-004",
                    status_code=500,
                    details={"user_id": assessment_record.user_id},
                )
            validated_assessments = (
                session.query(AssessmentRecord)
                .filter(
                    AssessmentRecord.user_id == assessment_record.user_id,
                    AssessmentRecord.validation_status == "validated",
                    AssessmentRecord.practice_type != "quick_practice",
                )
                .order_by(AssessmentRecord.created_at.asc())
                .all()
            )
            skill_slugs = [
                record.slug
                for record in session.query(SkillRecord).order_by(SkillRecord.slug.asc()).all()
            ]
            competency_records = (
                session.query(CompetencyRecord).order_by(CompetencyRecord.slug.asc()).all()
            )
            mapping_records = session.query(CompetencySkillMapRecord).all()
            weights_by_competency: dict[str, dict[str, float]] = {
                record.slug: {} for record in competency_records
            }
            raw_weights: dict[str, list[tuple[str, float]]] = {}
            for mapping in mapping_records:
                raw_weights.setdefault(mapping.competency_slug, []).append(
                    (mapping.skill_slug, mapping.weight)
                )
            for competency_slug, mappings in raw_weights.items():
                total = sum(weight for _, weight in mappings) or 1.0
                weights_by_competency[competency_slug] = {
                    skill_slug: weight / total for skill_slug, weight in mappings
                }
            latest_snapshot = (
                session.query(ProgressionSnapshotRecord)
                .filter(ProgressionSnapshotRecord.learner_id == assessment_record.user_id)
                .order_by(ProgressionSnapshotRecord.created_at.desc())
                .first()
            )
            return ProgressionRefreshInput(
                learner=LearnerProfileInput(
                    learner_id=learner_profile.user_id,
                    target_role=learner_profile.target_role,
                    goals=list(learner_profile.goals),
                ),
                source_assessment=self._to_assessment_signal(assessment_record),
                assessments=[
                    self._to_assessment_signal(record) for record in validated_assessments
                ],
                skill_slugs=skill_slugs,
                competency_definitions=[
                    CompetencyDefinition(
                        competency_slug=record.slug,
                        skill_weights=weights_by_competency.get(record.slug, {}),
                    )
                    for record in competency_records
                ],
                previous_state_payload=None
                if latest_snapshot is None
                else latest_snapshot.snapshot_payload,
            )

    def load_catalog_candidates(self, learner_id: str) -> list[CatalogCandidate]:
        with self._session_factory() as session:
            collections = session.query(CollectionRecord).all()
            candidates: list[CatalogCandidate] = []
            for collection in collections:
                actor = self._synthetic_actor(learner_id, session)
                if not can_view_collection(actor, collection, include_private=True):
                    continue
                prompt_items = (
                    session.query(PromptItemRecord)
                    .filter(PromptItemRecord.collection_id == collection.id)
                    .all()
                )
                scenarios = (
                    session.query(ScenarioRecord)
                    .filter(ScenarioRecord.collection_id == collection.id)
                    .all()
                )
                for prompt in prompt_items:
                    attempt_count, last_attempted_at = self._attempt_history(
                        session,
                        learner_id=learner_id,
                        content_item_id=prompt.id,
                    )
                    candidates.append(
                        CatalogCandidate(
                            content_id=prompt.id,
                            content_type=prompt.prompt_type,
                            collection_id=collection.id,
                            title=prompt.title,
                            summary=collection.summary,
                            difficulty=prompt.difficulty,
                            verification_state=collection.verification_state,
                            target_skill_slugs=list(prompt.target_skill_slugs),
                            target_competency_slugs=list(collection.target_competency_slugs),
                            rubric_id=prompt.rubric_id,
                            lifecycle_state=collection.lifecycle_state,
                            attempt_count=attempt_count,
                            last_attempted_at=last_attempted_at,
                        )
                    )
                for scenario in scenarios:
                    attempt_count, last_attempted_at = self._attempt_history(
                        session,
                        learner_id=learner_id,
                        content_item_id=scenario.id,
                    )
                    candidates.append(
                        CatalogCandidate(
                            content_id=scenario.id,
                            content_type="scenario_step",
                            collection_id=collection.id,
                            title=scenario.title,
                            summary=scenario.learner_objective,
                            difficulty=collection.difficulty,
                            verification_state=collection.verification_state,
                            target_skill_slugs=list(scenario.target_skill_slugs),
                            target_competency_slugs=list(collection.target_competency_slugs),
                            rubric_id=scenario.rubric_id,
                            lifecycle_state=collection.lifecycle_state,
                            attempt_count=attempt_count,
                            last_attempted_at=last_attempted_at,
                        )
                    )
            return candidates

    def latest_validated_assessment_id(self, learner_id: str) -> str:
        with self._session_factory() as session:
            record = (
                session.query(AssessmentRecord)
                .filter(
                    AssessmentRecord.user_id == learner_id,
                    AssessmentRecord.validation_status == "validated",
                    AssessmentRecord.practice_type != "quick_practice",
                )
                .order_by(AssessmentRecord.created_at.desc())
                .first()
            )
            if record is None:
                raise domain_error(
                    "Validated assessment history was not found",
                    code="SS-DOMAIN-021",
                    status_code=404,
                    details={"learner_id": learner_id},
                )
            return record.id

    def persist_snapshot(
        self,
        *,
        ctx: StageContext,
        learner_id: str,
        source_assessment_id: str,
        computed: ComputedProgressSnapshot,
    ) -> ProgressSnapshotView:
        snapshot_id = uuid4().hex
        created_at = _utcnow()
        view = ProgressSnapshotView(
            snapshot_id=snapshot_id,
            learner_id=learner_id,
            source_assessment_id=source_assessment_id,
            created_at=created_at.isoformat(),
            engine_version=PROGRESSION_ENGINE_VERSION,
            schema_version=PROGRESSION_SCHEMA_VERSION,
            config_version=PROGRESSION_CONFIG_VERSION,
            evidence_ledger_schema_version=PROGRESSION_EVIDENCE_LEDGER_SCHEMA_VERSION,
            trace_id=metadata_value(ctx, "trace_id"),
            weak_skill_slugs=list(computed.weak_skill_slugs),
            stagnating_skill_slugs=list(computed.stagnating_skill_slugs),
            coverage_gap_skill_slugs=list(computed.coverage_gap_skill_slugs),
            skill_states=list(computed.skill_states),
            competency_states=list(computed.competency_states),
        )
        try:
            with self._session_factory() as session:
                session.add(
                    ProgressionSnapshotRecord(
                        id=snapshot_id,
                        learner_id=learner_id,
                        source_assessment_id=source_assessment_id,
                        trace_id=metadata_value(ctx, "trace_id"),
                        workflow_id=metadata_value(ctx, "workflow_id"),
                        engine_version=PROGRESSION_ENGINE_VERSION,
                        schema_version=PROGRESSION_SCHEMA_VERSION,
                        config_version=PROGRESSION_CONFIG_VERSION,
                        evidence_ledger_schema_version=PROGRESSION_EVIDENCE_LEDGER_SCHEMA_VERSION,
                        snapshot_payload=view.model_dump(mode="json"),
                        created_at=created_at,
                    )
                )
                session.commit()
        except SQLAlchemyError as exc:
            raise persistence_error(
                "Progression snapshot could not be persisted",
                code="SS-PERSISTENCE-006",
                details={"learner_id": learner_id, "assessment_id": source_assessment_id},
            ) from exc
        self._events.record(
            event_type="progression.snapshot.created.v1",
            request_id=request_id_from_context(ctx),
            trace_id=metadata_value(ctx, "trace_id"),
            workflow_id=metadata_value(ctx, "workflow_id"),
            payload={
                "snapshot_id": snapshot_id,
                "learner_id": learner_id,
                "source_assessment_id": source_assessment_id,
                "weak_skill_slugs": list(computed.weak_skill_slugs),
            },
        )
        return view

    def persist_recommendation(
        self,
        *,
        ctx: StageContext,
        learner_id: str,
        snapshot_id: str,
        computed: ComputedRecommendation,
    ) -> RecommendationView:
        recommendation_id = uuid4().hex
        generated_at = _utcnow()
        view = RecommendationView(
            recommendation_id=recommendation_id,
            learner_id=learner_id,
            progress_snapshot_id=snapshot_id,
            generated_at=generated_at.isoformat(),
            engine_version=RECOMMENDATION_ENGINE_VERSION,
            schema_version=RECOMMENDATION_SCHEMA_VERSION,
            config_version=RECOMMENDATION_CONFIG_VERSION,
            trace_id=metadata_value(ctx, "trace_id"),
            context_snapshot_id=computed.context_snapshot_id,
            candidate_count=computed.candidate_count,
            items=list(computed.items),
            alternatives=list(computed.alternatives),
        )
        try:
            with self._session_factory() as session:
                session.add(
                    RecommendationArtifactRecord(
                        id=recommendation_id,
                        learner_id=learner_id,
                        progress_snapshot_id=snapshot_id,
                        trace_id=metadata_value(ctx, "trace_id"),
                        workflow_id=metadata_value(ctx, "workflow_id"),
                        engine_version=RECOMMENDATION_ENGINE_VERSION,
                        schema_version=RECOMMENDATION_SCHEMA_VERSION,
                        config_version=RECOMMENDATION_CONFIG_VERSION,
                        context_snapshot_id=computed.context_snapshot_id,
                        candidate_count=computed.candidate_count,
                        artifact_payload=view.model_dump(mode="json"),
                        created_at=generated_at,
                    )
                )
                session.commit()
        except SQLAlchemyError as exc:
            raise persistence_error(
                "Recommendation artifact could not be persisted",
                code="SS-PERSISTENCE-007",
                details={"learner_id": learner_id, "snapshot_id": snapshot_id},
            ) from exc
        self._events.record(
            event_type="recommendation.generated.v1",
            request_id=request_id_from_context(ctx),
            trace_id=metadata_value(ctx, "trace_id"),
            workflow_id=metadata_value(ctx, "workflow_id"),
            payload={
                "recommendation_id": recommendation_id,
                "learner_id": learner_id,
                "progress_snapshot_id": snapshot_id,
                "candidate_count": computed.candidate_count,
                "selected_content_ids": [item.content_id for item in computed.items],
            },
        )
        return view

    def create_recalculation_run(
        self,
        *,
        request_id: str,
        learner_id: str,
        reason: str,
        trace_id: str,
        workflow_id: str,
    ) -> str:
        run_id = uuid4().hex
        try:
            with self._session_factory() as session:
                session.add(
                    ProgressRecalculationRecord(
                        id=run_id,
                        learner_id=learner_id,
                        status="running",
                        reason=reason,
                        trace_id=trace_id,
                        workflow_id=workflow_id,
                        config_version=PROGRESSION_CONFIG_VERSION,
                        diff_summary={},
                        started_at=_utcnow(),
                        completed_at=None,
                        previous_snapshot_id=None,
                        next_snapshot_id=None,
                        next_recommendation_id=None,
                    )
                )
                session.commit()
        except SQLAlchemyError as exc:
            raise persistence_error(
                "Recalculation run could not be created",
                code="SS-PERSISTENCE-008",
                details={"learner_id": learner_id},
            ) from exc
        self._events.record(
            event_type="progression.recalculation.started.v1",
            request_id=request_id,
            trace_id=trace_id,
            workflow_id=workflow_id,
            payload={"recalculation_id": run_id, "learner_id": learner_id, "reason": reason},
        )
        return run_id

    def complete_recalculation_run(
        self,
        *,
        request_id: str,
        workflow_id: str,
        run_id: str,
        reason: str,
        learner_id: str,
        assessment_count: int,
        previous_state_payload: dict[str, object] | None,
        snapshot: ProgressSnapshotView,
        recommendation: RecommendationView,
    ) -> ProgressRecalculationView:
        summary = diff_summary(
            previous_state=build_prior_progress_state(previous_state_payload),
            snapshot=ComputedProgressSnapshot(
                weak_skill_slugs=list(snapshot.weak_skill_slugs),
                stagnating_skill_slugs=list(snapshot.stagnating_skill_slugs),
                coverage_gap_skill_slugs=list(snapshot.coverage_gap_skill_slugs),
                skill_states=list(snapshot.skill_states),
                competency_states=list(snapshot.competency_states),
            ),
        )
        started_at: datetime
        completed_at = _utcnow()
        previous_snapshot_id = None
        prior_state = build_prior_progress_state(previous_state_payload)
        if prior_state is not None:
            previous_snapshot_id = prior_state.snapshot_id
        try:
            with self._session_factory() as session:
                record = session.get(ProgressRecalculationRecord, run_id)
                if record is None:
                    raise persistence_error(
                        "Recalculation run was not found",
                        code="SS-PERSISTENCE-009",
                        details={"recalculation_id": run_id},
                    )
                started_at = record.started_at
                record.status = "completed"
                record.completed_at = completed_at
                record.previous_snapshot_id = previous_snapshot_id
                record.next_snapshot_id = snapshot.snapshot_id
                record.next_recommendation_id = recommendation.recommendation_id
                record.diff_summary = summary
                session.commit()
        except SQLAlchemyError as exc:
            raise persistence_error(
                "Recalculation run could not be completed",
                code="SS-PERSISTENCE-010",
                details={"recalculation_id": run_id},
            ) from exc
        self._events.record(
            event_type="progression.recalculation.completed.v1",
            request_id=request_id,
            trace_id=snapshot.trace_id,
            workflow_id=workflow_id,
            payload={
                "recalculation_id": run_id,
                "learner_id": learner_id,
                "assessment_count": assessment_count,
                "next_snapshot_id": snapshot.snapshot_id,
                "next_recommendation_id": recommendation.recommendation_id,
            },
        )
        return ProgressRecalculationView(
            recalculation_id=run_id,
            learner_id=learner_id,
            reason=reason,
            status="completed",
            started_at=started_at.isoformat(),
            completed_at=completed_at.isoformat(),
            assessment_count=assessment_count,
            previous_snapshot_id=previous_snapshot_id,
            next_snapshot_id=snapshot.snapshot_id,
            next_recommendation_id=recommendation.recommendation_id,
            config_version=PROGRESSION_CONFIG_VERSION,
            diff_summary=summary,
        )

    def get_dashboard(self, actor: Actor, learner_id: str) -> ProgressDashboardView:
        self._assert_access(actor, learner_id)
        with self._session_factory() as session:
            snapshot_record = (
                session.query(ProgressionSnapshotRecord)
                .filter(ProgressionSnapshotRecord.learner_id == learner_id)
                .order_by(ProgressionSnapshotRecord.created_at.desc())
                .first()
            )
            if snapshot_record is None:
                raise domain_error(
                    "Progress snapshot was not found",
                    code="SS-DOMAIN-019",
                    status_code=404,
                    details={"learner_id": learner_id},
                )
            recommendation_record = (
                session.query(RecommendationArtifactRecord)
                .filter(RecommendationArtifactRecord.learner_id == learner_id)
                .order_by(RecommendationArtifactRecord.created_at.desc())
                .first()
            )
            if recommendation_record is None:
                raise domain_error(
                    "Recommendation artifact was not found",
                    code="SS-DOMAIN-020",
                    status_code=404,
                    details={"learner_id": learner_id},
                )
            return ProgressDashboardView(
                snapshot=ProgressSnapshotView.model_validate(snapshot_record.snapshot_payload),
                recommendation=RecommendationView.model_validate(
                    recommendation_record.artifact_payload
                ),
            )

    def get_recommendation(self, actor: Actor, learner_id: str) -> RecommendationView:
        self._assert_access(actor, learner_id)
        with self._session_factory() as session:
            recommendation_record = (
                session.query(RecommendationArtifactRecord)
                .filter(RecommendationArtifactRecord.learner_id == learner_id)
                .order_by(RecommendationArtifactRecord.created_at.desc())
                .first()
            )
            if recommendation_record is None:
                raise domain_error(
                    "Recommendation artifact was not found",
                    code="SS-DOMAIN-020",
                    status_code=404,
                    details={"learner_id": learner_id},
                )
            return RecommendationView.model_validate(recommendation_record.artifact_payload)

    def _attempt_history(
        self,
        session: Session,
        *,
        learner_id: str,
        content_item_id: str,
    ) -> tuple[int, datetime | None]:
        attempts = (
            session.query(AttemptRecord)
            .filter(
                AttemptRecord.user_id == learner_id,
                AttemptRecord.content_item_id == content_item_id,
                AttemptRecord.status == "assessed",
            )
            .order_by(AttemptRecord.assessed_at.desc())
            .all()
        )
        last_attempted_at = attempts[0].assessed_at if attempts else None
        return len(attempts), last_attempted_at

    def _synthetic_actor(self, learner_id: str, session: Session | None = None) -> Actor:
        organisation_id = None
        organisation_role = None
        if session is not None:
            membership = (
                session.query(OrganisationMembershipRecord)
                .filter(OrganisationMembershipRecord.user_id == learner_id)
                .first()
            )
            if membership is not None:
                organisation_id = membership.organisation_id
                organisation_role = membership.role
        return Actor(
            user_id=learner_id,
            email="",
            organisation_id=organisation_id,
            organisation_role=organisation_role,
        )

    def _to_assessment_signal(self, record: AssessmentRecord) -> AssessmentSignal:
        return AssessmentSignal(
            assessment_id=record.id,
            attempt_id=record.attempt_id,
            learner_id=record.user_id,
            created_at=record.created_at,
            prompt_version=record.prompt_version,
            rubric_version=record.rubric_version,
            trace_id=record.trace_id,
            skill_scores=[
                AssessmentSkillScoreSignal.model_validate(item) for item in record.skill_scores
            ],
            evidence=[AssessmentEvidenceSignal.model_validate(item) for item in record.evidence],
        )

    def _assert_access(self, actor: Actor, learner_id: str) -> None:
        if actor.user_id == learner_id:
            return
        if actor.is_org_admin and actor.organisation_id is not None:
            with self._session_factory() as session:
                learner_membership = (
                    session.query(OrganisationMembershipRecord)
                    .filter(
                        OrganisationMembershipRecord.user_id == learner_id,
                        OrganisationMembershipRecord.organisation_id == actor.organisation_id,
                    )
                    .first()
                )
                if learner_membership is not None:
                    return
        raise auth_error(
            "Progress is not visible to this actor",
            code="SS-AUTH-010",
            status_code=403,
            details={"learner_id": learner_id},
        )
