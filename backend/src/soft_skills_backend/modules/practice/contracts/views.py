"""Practice view builders and shared helpers."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy.orm import Session

from soft_skills_backend.modules.practice.domain.practice import (
    AssessmentValidationStatus,
    AttemptStatus,
    EvidenceItem,
    SkillScore,
)
from soft_skills_backend.modules.practice.models import (
    AttemptView,
    PracticeAssessmentView,
)
from soft_skills_backend.modules.practice.workflows.assessment.models import PracticePromptView
from soft_skills_backend.platform.db.models import (
    AssessmentRecord,
    AttemptRecord,
    CollectionRecord,
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
