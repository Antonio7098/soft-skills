"""Practice view builders and shared helpers."""

from __future__ import annotations

from collections import defaultdict
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from soft_skills_backend.modules.practice.domain.practice import (
    AssessmentValidationStatus,
    AttemptStatus,
    EvidenceItem,
    PracticeRunStatus,
    PracticeType,
    SkillScore,
    is_attempt_terminal,
)
from soft_skills_backend.modules.practice.models import (
    AttemptView,
    PracticeAssessmentView,
    PracticeRunItemView,
    PracticeRunListItemView,
    PracticeRunSkillBreakdownView,
    PracticeRunSummaryView,
    PracticeRunTypeBreakdownView,
    PracticeRunView,
)
from soft_skills_backend.modules.practice.workflows.assessment.models import PracticePromptView
from soft_skills_backend.platform.db.models import (
    AssessmentRecord,
    AttemptRecord,
    CollectionRecord,
    PracticeRunRecord,
    PracticeSessionRecord,
)
from soft_skills_backend.shared.auth import Actor
from soft_skills_backend.shared.errors import domain_error


def build_attempt_view(session: Session, attempt: AttemptRecord) -> AttemptView:
    """Build an API view from persisted attempt records."""

    practice_session = session.get(PracticeSessionRecord, attempt.session_id)
    if practice_session is None:
        raise domain_error(
            "Practice session was not found",
            code="SS-DOMAIN-013",
            status_code=404,
            details={"session_id": attempt.session_id},
        )
    prompt = PracticePromptView.model_validate(practice_session.prompt_payload)
    assessment: PracticeAssessmentView | None
    if attempt.assessment_id is None:
        assessment = None
    else:
        record = session.get(AssessmentRecord, attempt.assessment_id)
        assessment = None if record is None else _assessment_record_to_view(record)
    return AttemptView(
        id=attempt.id,
        session_id=attempt.session_id,
        workflow_id=attempt.workflow_id,
        status=AttemptStatus(attempt.status),
        response_mode=attempt.response_mode,
        response_text=attempt.response_text,
        last_error_code=attempt.last_error_code,
        submitted_at=None if attempt.submitted_at is None else attempt.submitted_at.isoformat(),
        assessed_at=None if attempt.assessed_at is None else attempt.assessed_at.isoformat(),
        prompt=prompt,
        assessment=assessment,
    )


def build_practice_run_view(session: Session, run: PracticeRunRecord) -> PracticeRunView:
    """Build a full aggregate run view from persisted records."""

    items = _load_practice_run_items(session, run.id)
    current_attempt_id = next(
        (item.attempt.id for item in items if not is_attempt_terminal(item.attempt.status)),
        None,
    )
    summary = _build_practice_run_summary(items)
    return PracticeRunView(
        run_id=run.id,
        workflow_id=run.workflow_id,
        status=PracticeRunStatus(run.status),
        total_items=run.total_items,
        completed_items=run.completed_items,
        validated_items=run.validated_items,
        failed_items=run.failed_items,
        current_attempt_id=current_attempt_id,
        started_at=run.created_at.isoformat(),
        completed_at=None if run.completed_at is None else run.completed_at.isoformat(),
        items=items,
        summary=summary,
    )


def build_practice_run_list_item(session: Session, run: PracticeRunRecord) -> PracticeRunListItemView:
    """Build a compact history row for one aggregate run."""

    items = _load_practice_run_items(session, run.id)
    summary = _build_practice_run_summary(items)
    practice_types: list[PracticeType] = []
    seen_practice_types: set[PracticeType] = set()
    for item in items:
        practice_type = item.attempt.prompt.practice_type
        if practice_type in seen_practice_types:
            continue
        seen_practice_types.add(practice_type)
        practice_types.append(practice_type)
    return PracticeRunListItemView(
        run_id=run.id,
        workflow_id=run.workflow_id,
        status=PracticeRunStatus(run.status),
        total_items=run.total_items,
        completed_items=run.completed_items,
        validated_items=run.validated_items,
        failed_items=run.failed_items,
        overall_score_average=summary.overall_score_average,
        practice_types=practice_types,
        started_at=run.created_at.isoformat(),
        completed_at=None if run.completed_at is None else run.completed_at.isoformat(),
    )


def _assessment_record_to_view(record: AssessmentRecord) -> PracticeAssessmentView:
    """Build the learner-facing assessment view."""

    return PracticeAssessmentView(
        assessment_id=record.id,
        attempt_id=record.attempt_id,
        session_id=record.session_id,
        validation_status=AssessmentValidationStatus(record.validation_status),
        prompt_version=record.prompt_version,
        rubric_id=record.rubric_id,
        rubric_version=record.rubric_version,
        schema_version=record.schema_version,
        config_version=record.config_version,
        provider=record.provider,
        model_slug=record.model_slug,
        overall_score=record.overall_score,
        skill_scores=[SkillScore.model_validate(item) for item in record.skill_scores],
        evidence=[EvidenceItem.model_validate(item) for item in record.evidence],
        rationale=record.rationale,
        strengths=list(record.strengths),
        weaknesses=list(record.weaknesses),
        next_actions=list(record.next_actions),
        trace_id=record.trace_id,
        pipeline_run_id=record.pipeline_run_id,
        rejection_code=record.rejection_code,
        created_at=record.created_at.isoformat(),
    )


def _load_practice_run_items(session: Session, run_id: str) -> list[PracticeRunItemView]:
    session_records = (
        session.query(PracticeSessionRecord)
        .filter(PracticeSessionRecord.practice_run_id == run_id)
        .order_by(PracticeSessionRecord.sequence_index.asc(), PracticeSessionRecord.created_at.asc())
        .all()
    )
    items: list[PracticeRunItemView] = []
    for index, practice_session in enumerate(session_records, start=1):
        attempt = _attempt_for_practice_session(session, practice_session)
        items.append(
            PracticeRunItemView(
                position=practice_session.sequence_index or index,
                attempt=build_attempt_view(session, attempt),
            )
        )
    return items


def _attempt_for_practice_session(session: Session, practice_session: PracticeSessionRecord) -> AttemptRecord:
    attempt: AttemptRecord | None = None
    if practice_session.last_attempt_id is not None:
        attempt = session.get(AttemptRecord, practice_session.last_attempt_id)
    if attempt is None:
        attempt = (
            session.query(AttemptRecord)
            .filter(AttemptRecord.session_id == practice_session.id)
            .order_by(AttemptRecord.created_at.asc())
            .one_or_none()
        )
    if attempt is None:
        raise domain_error(
            "Attempt was not found for practice session",
            code="SS-DOMAIN-017",
            status_code=404,
            details={"session_id": practice_session.id},
        )
    return attempt


def _build_practice_run_summary(items: list[PracticeRunItemView]) -> PracticeRunSummaryView:
    score_distribution = {str(score): 0 for score in range(1, 6)}
    skill_scores: dict[str, list[int]] = defaultdict(list)
    type_scores: dict[PracticeType, list[int]] = defaultdict(list)
    validated_attempt_count = 0
    failed_attempt_count = 0
    total_overall_score = 0

    for item in items:
        attempt = item.attempt
        if attempt.status in {AttemptStatus.ASSESSMENT_REJECTED, AttemptStatus.ASSESSMENT_FAILED}:
            failed_attempt_count += 1
        assessment = attempt.assessment
        if assessment is None or assessment.validation_status != AssessmentValidationStatus.VALIDATED:
            continue
        if assessment.overall_score is None:
            continue
        validated_attempt_count += 1
        total_overall_score += assessment.overall_score
        score_distribution[str(assessment.overall_score)] += 1
        type_scores[attempt.prompt.practice_type].append(assessment.overall_score)
        for skill_score in assessment.skill_scores:
            skill_scores[skill_score.skill_slug].append(skill_score.score)

    overall_score_average = None
    if validated_attempt_count > 0:
        overall_score_average = round(total_overall_score / validated_attempt_count, 2)

    return PracticeRunSummaryView(
        validated_attempt_count=validated_attempt_count,
        failed_attempt_count=failed_attempt_count,
        overall_score_average=overall_score_average,
        score_distribution=score_distribution,
        skill_breakdown=[
            PracticeRunSkillBreakdownView(
                skill_slug=skill_slug,
                average_score=round(sum(scores) / len(scores), 2),
                count=len(scores),
            )
            for skill_slug, scores in sorted(skill_scores.items())
        ],
        practice_type_breakdown=[
            PracticeRunTypeBreakdownView(
                practice_type=practice_type,
                average_score=round(sum(scores) / len(scores), 2),
                count=len(scores),
            )
            for practice_type, scores in sorted(type_scores.items(), key=lambda item: item[0].value)
        ],
    )


def can_use_collection(actor: Actor, collection: CollectionRecord) -> bool:
    """Return whether an actor can use a collection-backed prompt."""

    if collection.lifecycle_state == "published_public":
        return True
    return actor.is_admin or collection.author_user_id == actor.user_id


def utcnow() -> datetime:
    """Return the current UTC timestamp."""

    return datetime.now(UTC)


def utcnow_iso() -> str:
    """Return the current UTC timestamp in ISO-8601 format."""

    return utcnow().isoformat()
