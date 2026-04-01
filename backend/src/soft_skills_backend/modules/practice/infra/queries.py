"""Practice query and guard helpers."""

from __future__ import annotations

from sqlalchemy.orm import Session, sessionmaker

from soft_skills_backend.modules.catalog.domain.constants import resolve_rubric_id
from soft_skills_backend.modules.practice.domain.practice import (
    PRACTICE_DELIVERY_VERSIONS,
    AttemptStatus,
    PracticeType,
    ensure_attempt_transition,
)
from soft_skills_backend.modules.practice.models import (
    AttemptGuardPayload,
    PromptContextPayload,
    StartInputPayload,
)
from soft_skills_backend.modules.practice.workflows.assessment.models import (
    LearnerContextPayload,
    PracticePromptView,
    ResolvedAttemptPayload,
    ScenarioActorView,
    ScenarioCompanyView,
    ScenarioContextView,
)
from soft_skills_backend.platform.db.models import (
    AttemptRecord,
    CollectionRecord,
    MockCompanyRecord,
    MockPersonRecord,
    PromptItemRecord,
    RubricRecord,
    RubricVersionRecord,
    ScenarioRecord,
)
from soft_skills_backend.platform.workflows.stageflow import StageflowStageResult
from soft_skills_backend.shared.auth import Actor
from soft_skills_backend.shared.errors import auth_error, domain_error, validation_error

from ..contracts.views import can_use_collection

PROMPT_TYPES_BY_PRACTICE: dict[PracticeType, str] = {
    PracticeType.QUICK_PRACTICE: "quick_practice_prompt",
    PracticeType.INTERVIEW: "interview_prompt",
}


def load_start_prompt_context(
    session_factory: sessionmaker[Session],
    actor: Actor,
    start_input: StartInputPayload,
) -> StageflowStageResult:
    with session_factory() as session:
        if start_input.practice_type == PracticeType.SCENARIO:
            return _load_scenario_context(session, actor, start_input)
        return _load_prompt_item_context(session, actor, start_input)


def _load_prompt_item_context(
    session: Session,
    actor: Actor,
    start_input: StartInputPayload,
) -> StageflowStageResult:
    prompt = session.get(PromptItemRecord, start_input.content_item_id)
    if prompt is None:
        raise domain_error(
            "Prompt item was not found",
            code="SS-DOMAIN-011",
            status_code=404,
            details={"prompt_item_id": start_input.content_item_id},
        )

    expected_prompt_type = PROMPT_TYPES_BY_PRACTICE[start_input.practice_type]
    if prompt.prompt_type != expected_prompt_type:
        raise validation_error(
            "Prompt item does not match the requested practice mode",
            code="SS-VALIDATION-021",
            details={
                "practice_type": start_input.practice_type.value,
                "prompt_type": prompt.prompt_type,
                "expected_prompt_type": expected_prompt_type,
            },
        )

    collection = session.get(CollectionRecord, prompt.collection_id)
    if collection is None:
        raise domain_error(
            "Prompt item collection was not found",
            code="SS-DOMAIN-012",
            status_code=404,
            details={"collection_id": prompt.collection_id},
        )
    if not can_use_collection(actor, collection):
        raise auth_error(
            "Prompt item is not visible to this actor",
            code="SS-AUTH-008",
            status_code=403,
            details={"prompt_item_id": prompt.id},
        )

    rubric_id = resolve_rubric_id(prompt.prompt_type, prompt.rubric_id)
    rubric = session.get(RubricRecord, rubric_id)
    if rubric is None:
        raise validation_error(
            "Prompt item rubric was not found",
            code="SS-VALIDATION-022",
            details={"rubric_id": rubric_id},
        )
    if rubric.content_type != prompt.prompt_type:
        raise validation_error(
            "Prompt item rubric mapping is invalid",
            code="SS-VALIDATION-023",
            details={"prompt_item_id": prompt.id, "rubric_id": rubric.id},
        )

    rubric_version_record = (
        session.query(RubricVersionRecord)
        .filter(
            RubricVersionRecord.rubric_id == rubric.id,
            RubricVersionRecord.status == "published",
        )
        .order_by(RubricVersionRecord.version.desc())
        .first()
    )
    rubric_version = rubric_version_record.version if rubric_version_record else "v1"

    prompt_view = PracticePromptView(
        practice_type=start_input.practice_type,
        content_item_id=prompt.id,
        content_item_type=prompt.prompt_type,
        prompt_type=prompt.prompt_type,
        title=prompt.title,
        prompt_text=prompt.prompt_text,
        difficulty=prompt.difficulty,
        delivery_version=PRACTICE_DELIVERY_VERSIONS[start_input.practice_type],
        response_mode="text",
        target_skill_slugs=list(prompt.target_skill_slugs),
        rubric_id=rubric.id,
        rubric_version=rubric_version,
        interview_context=start_input.interview_context,
    )
    return StageflowStageResult(
        payload=PromptContextPayload(prompt=prompt_view),
        summary={
            "content_item_id": prompt.id,
            "practice_type": start_input.practice_type.value,
            "rubric_id": rubric.id,
        },
    )


def _load_scenario_context(
    session: Session,
    actor: Actor,
    start_input: StartInputPayload,
) -> StageflowStageResult:
    scenario = session.get(ScenarioRecord, start_input.content_item_id)
    if scenario is None:
        raise domain_error(
            "Scenario was not found",
            code="SS-DOMAIN-015",
            status_code=404,
            details={"scenario_id": start_input.content_item_id},
        )

    collection = session.get(CollectionRecord, scenario.collection_id)
    if collection is None:
        raise domain_error(
            "Scenario collection was not found",
            code="SS-DOMAIN-016",
            status_code=404,
            details={"collection_id": scenario.collection_id},
        )
    if not can_use_collection(actor, collection):
        raise auth_error(
            "Scenario is not visible to this actor",
            code="SS-AUTH-009",
            status_code=403,
            details={"scenario_id": scenario.id},
        )

    rubric_id = resolve_rubric_id("scenario_step", scenario.rubric_id)
    rubric = session.get(RubricRecord, rubric_id)
    if rubric is None:
        raise validation_error(
            "Scenario rubric was not found",
            code="SS-VALIDATION-026",
            details={"rubric_id": rubric_id},
        )
    if rubric.content_type != "scenario_step":
        raise validation_error(
            "Scenario rubric mapping is invalid",
            code="SS-VALIDATION-027",
            details={"scenario_id": scenario.id, "rubric_id": rubric.id},
        )

    rubric_version_record = (
        session.query(RubricVersionRecord)
        .filter(
            RubricVersionRecord.rubric_id == rubric.id,
            RubricVersionRecord.status == "published",
        )
        .order_by(RubricVersionRecord.version.desc())
        .first()
    )
    rubric_version = rubric_version_record.version if rubric_version_record else "v1"

    company_record = (
        session.query(MockCompanyRecord)
        .filter(MockCompanyRecord.scenario_id == scenario.id)
        .one_or_none()
    )
    people_records = (
        session.query(MockPersonRecord)
        .filter(MockPersonRecord.scenario_id == scenario.id)
        .order_by(MockPersonRecord.name.asc())
        .all()
    )
    scenario_context = ScenarioContextView(
        prompt_text=scenario.prompt_text,
        business_context=scenario.business_context,
        learner_objective=scenario.learner_objective,
        constraints=list(scenario.constraints),
        stakeholder_tensions=list(scenario.stakeholder_tensions),
        mock_company=(
            None
            if company_record is None
            else ScenarioCompanyView(
                name=company_record.name,
                industry=company_record.industry,
                operating_context=company_record.operating_context,
            )
        ),
        mock_people=[
            ScenarioActorView(
                name=person.name,
                role=person.role,
                goals=list(person.goals),
                communication_style=person.communication_style,
                relationship_to_scenario=person.relationship_to_scenario,
            )
            for person in people_records
        ],
        artifacts=list(start_input.artifacts),
    )
    prompt_view = PracticePromptView(
        practice_type=PracticeType.SCENARIO,
        content_item_id=scenario.id,
        content_item_type="scenario_step",
        prompt_type="scenario_step",
        title=scenario.title,
        prompt_text=scenario.prompt_text,
        difficulty=collection.difficulty,
        delivery_version=PRACTICE_DELIVERY_VERSIONS[PracticeType.SCENARIO],
        response_mode="text",
        target_skill_slugs=list(scenario.target_skill_slugs),
        rubric_id=rubric.id,
        rubric_version=rubric_version,
        scenario_context=scenario_context,
    )
    return StageflowStageResult(
        payload=PromptContextPayload(prompt=prompt_view),
        summary={
            "content_item_id": scenario.id,
            "practice_type": PracticeType.SCENARIO.value,
            "rubric_id": rubric.id,
            "stakeholder_count": len(scenario_context.mock_people),
            "artifact_count": len(scenario_context.artifacts),
        },
    )


def load_learner_context(
    session_factory: sessionmaker[Session],
    user_id: str,
) -> StageflowStageResult:
    from soft_skills_backend.platform.db.models import LearnerProfileRecord

    with session_factory() as session:
        profile = session.get(LearnerProfileRecord, user_id)
        if profile is None:
            raise domain_error(
                "Learner profile is missing",
                code="SS-DOMAIN-004",
                status_code=500,
                details={"user_id": user_id},
            )
        prior_assessed_attempts = (
            session.query(AttemptRecord)
            .filter(
                AttemptRecord.user_id == user_id,
                AttemptRecord.status == AttemptStatus.ASSESSED.value,
            )
            .count()
        )
        return StageflowStageResult(
            payload=LearnerContextPayload(
                target_role=profile.target_role,
                goals=list(profile.goals),
                prior_assessed_attempts=prior_assessed_attempts,
            ),
            summary={"prior_assessed_attempts": prior_assessed_attempts},
        )


def load_attempt_ownership(
    session_factory: sessionmaker[Session], attempt_id: str
) -> AttemptRecord:
    with session_factory() as session:
        attempt = session.get(AttemptRecord, attempt_id)
        if attempt is None:
            raise domain_error(
                "Attempt was not found",
                code="SS-DOMAIN-010",
                status_code=404,
                details={"attempt_id": attempt_id},
            )
        return attempt


def load_submit_guard(
    session_factory: sessionmaker[Session],
    *,
    actor: Actor,
    attempt_id: str,
    response_text: str,
) -> StageflowStageResult:
    with session_factory() as session:
        attempt = session.get(AttemptRecord, attempt_id)
        if attempt is None:
            raise domain_error(
                "Attempt was not found",
                code="SS-DOMAIN-010",
                status_code=404,
                details={"attempt_id": attempt_id},
            )
        if attempt.user_id != actor.user_id:
            raise auth_error(
                "Attempt submission is only allowed for the owning learner",
                code="SS-AUTH-012",
                status_code=403,
                details={"attempt_id": attempt_id},
            )
        ensure_attempt_transition(attempt.status, AttemptStatus.SUBMITTED)
        payload = AttemptGuardPayload(
            attempt_id=attempt.id,
            session_id=attempt.session_id,
            workflow_id=attempt.workflow_id,
            response_text=response_text,
        )
        return StageflowStageResult(
            payload=payload,
            summary={"attempt_id": attempt.id, "session_id": attempt.session_id},
        )


def load_resolved_attempt(
    session_factory: sessionmaker[Session],
    guard: AttemptGuardPayload,
) -> StageflowStageResult:
    from soft_skills_backend.platform.db.models import PracticeSessionRecord

    with session_factory() as session:
        practice_session = session.get(PracticeSessionRecord, guard.session_id)
        if practice_session is None:
            raise domain_error(
                "Practice session was not found",
                code="SS-DOMAIN-013",
                status_code=404,
                details={"session_id": guard.session_id},
            )
        rubric = session.get(RubricRecord, practice_session.rubric_id)
        if rubric is None:
            raise validation_error(
                "Practice session rubric was not found",
                code="SS-VALIDATION-024",
                details={"rubric_id": practice_session.rubric_id},
            )

        rubric_version_record = (
            session.query(RubricVersionRecord)
            .filter(
                RubricVersionRecord.rubric_id == rubric.id,
                RubricVersionRecord.status == "published",
            )
            .order_by(RubricVersionRecord.version.desc())
            .first()
        )
        rubric_version = rubric_version_record.version if rubric_version_record else "v1"

        prompt = PracticePromptView.model_validate(practice_session.prompt_payload)
        if not prompt.rubric_version:
            raise validation_error(
                "Practice session prompt payload is missing rubric version metadata",
                code="SS-VALIDATION-025",
                details={"session_id": guard.session_id},
            )
        return StageflowStageResult(
            payload=ResolvedAttemptPayload(
                attempt_id=guard.attempt_id,
                session_id=guard.session_id,
                workflow_id=guard.workflow_id,
                response_text=guard.response_text,
                prompt=prompt.model_copy(update={"rubric_version": rubric_version}),
            ),
            summary={"attempt_id": guard.attempt_id, "rubric_id": rubric.id},
        )


def _build_scenario_prompt_text(context: ScenarioContextView) -> str:
    return context.prompt_text


def _join_items(values: list[str]) -> str:
    return "; ".join(value.strip() for value in values if value.strip())
