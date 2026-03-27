from __future__ import annotations

from pathlib import Path

import pytest
from alembic.config import Config

from alembic import command
from soft_skills_backend.modules.practice.domain.practice import AssessmentDraft
from soft_skills_backend.modules.practice.workflows.assessment import (
    AssessmentTransformPayload,
    ResolvedAttemptPayload,
    StructuredOutputRejectionError,
)
from soft_skills_backend.platform.db.models import (
    AssessmentRecord,
    AttemptRecord,
    PipelineRunRecord,
    PracticeSessionRecord,
    ProgressionSnapshotRecord,
    RecommendationArtifactRecord,
    WorkflowEventRecord,
)
from soft_skills_backend.shared.errors import provider_error, validation_error


def _migrate(test_settings) -> None:
    alembic_config = Config(str(Path(__file__).resolve().parents[2] / "alembic.ini"))
    alembic_config.set_main_option("sqlalchemy.url", test_settings.database_url)
    command.upgrade(alembic_config, "head")


async def _register_user(client, *, email: str, display_name: str):
    response = await client.post(
        "/api/auth/register",
        json={
            "email": email,
            "display_name": display_name,
            "target_role": "Consultant",
            "goals": ["Improve stakeholder handling"],
            "practice_preferences": {"session_length": "short"},
        },
    )
    assert response.status_code == 200
    return response.json()["data"]


async def _seed_quick_practice_prompt(client) -> tuple[dict[str, object], dict[str, object]]:
    admin = await _register_user(
        client,
        email="admin-practice@example.com",
        display_name="Admin Practice",
    )
    bootstrap_response = await client.post(
        "/api/skills/bootstrap-canon",
        headers={"X-User-ID": admin["id"]},
    )
    assert bootstrap_response.status_code == 200

    learner = await _register_user(
        client,
        email="learner-practice@example.com",
        display_name="Learner Practice",
    )
    collection_response = await client.post(
        "/api/collections",
        headers={"X-User-ID": learner["id"]},
        json={
            "title": "Client Pushback Pack",
            "summary": "Quick practice prompts for tough stakeholder asks.",
            "target_audience": "Early-career consultants",
            "difficulty": "intermediate",
            "content_format_mix": ["quick_practice_prompt"],
            "target_skill_slugs": ["active-listening", "expectation-setting"],
            "target_competency_slugs": ["stakeholder-management"],
            "rubric_ids": ["quick_practice_reset_timeline@v1"],
        },
    )
    assert collection_response.status_code == 200
    collection = collection_response.json()["data"]

    prompt_response = await client.post(
        f"/api/collections/{collection['id']}/prompt-items",
        headers={"X-User-ID": learner["id"]},
        json={
            "prompt_type": "quick_practice_prompt",
            "title": "Reset the timeline",
            "prompt_text": (
                "A client asks for an impossible delivery date. Respond with empathy and a realistic next step."
            ),
            "difficulty": "intermediate",
            "target_skill_slugs": ["active-listening", "expectation-setting"],
            "rubric_id": "quick_practice_reset_timeline@v1",
        },
    )
    assert prompt_response.status_code == 200
    prompt = prompt_response.json()["data"]
    return learner, prompt


class FakeSuccessMarker:
    provider_name = "openai"
    model_slug = "gpt-4.1-mini"

    async def mark_attempt(
        self,
        *,
        prompt_payload: ResolvedAttemptPayload,
        learner_payload,
        call_context,
    ) -> AssessmentTransformPayload:
        del learner_payload, call_context
        return AssessmentTransformPayload(
            draft=AssessmentDraft.model_validate(
                {
                    "prompt_version": "assessment.quick-practice.v1",
                    "rubric_version": prompt_payload.prompt.rubric_version,
                    "provider": "openai",
                    "model_slug": "gpt-4.1-mini",
                    "overall_score": 2,
                    "rationale": "The response balanced empathy with a realistic commitment.",
                    "skill_scores": [
                        {
                            "skill_slug": "active-listening",
                            "score": 2,
                            "rationale": "It acknowledged the client concern directly.",
                        },
                        {
                            "skill_slug": "expectation-setting",
                            "score": 2,
                            "rationale": "It proposed a credible date and checkpoint.",
                        },
                    ],
                    "evidence": [
                        {
                            "skill_slug": "active-listening",
                            "quote": "I hear why the date matters to you",
                            "explanation": "The learner acknowledged the stakeholder concern.",
                        },
                        {
                            "skill_slug": "expectation-setting",
                            "quote": "The earliest realistic date is next Friday",
                            "explanation": "The learner set a realistic boundary.",
                        },
                    ],
                    "strengths": ["Acknowledged the client concern before resetting expectations."],
                    "weaknesses": ["Could have added one explicit risk if scope changed again."],
                    "next_actions": ["Practice pairing empathy with a contingency plan."],
                }
            ),
            raw_payload={"ok": True},
            model_slug="gpt-4.1-mini",
            schema_version="quick-practice-assessment-output.v1",
        )


class FakeMissingMetadataMarker:
    provider_name = "openai"
    model_slug = "gpt-4.1-mini"

    async def mark_attempt(
        self, *, prompt_payload, learner_payload, call_context
    ) -> AssessmentTransformPayload:
        del prompt_payload, learner_payload, call_context
        raise StructuredOutputRejectionError(
            app_error=validation_error(
                "Provider returned malformed structured output",
                code="SS-VALIDATION-019",
            ),
            raw_payload={"rubric_version": "v1", "provider": "openai"},
        )


class FakeProviderFailureMarker:
    provider_name = "openai"
    model_slug = "gpt-4.1-mini"

    async def mark_attempt(
        self, *, prompt_payload, learner_payload, call_context
    ) -> AssessmentTransformPayload:
        del prompt_payload, learner_payload, call_context
        raise provider_error(
            "Simulated provider outage",
            code="SS-PROVIDER-099",
        )


@pytest.mark.asyncio
async def test_quick_practice_start_submit_and_persist(app, client, test_settings) -> None:
    _migrate(test_settings)
    learner, prompt = await _seed_quick_practice_prompt(client)
    app.state.container.practice_service._assessment_marker = FakeSuccessMarker()

    start_response = await client.post(
        "/api/attempts/quick-practice/sessions",
        headers={"X-User-ID": learner["id"]},
        json={"prompt_item_id": prompt["id"]},
    )
    assert start_response.status_code == 200
    session_payload = start_response.json()["data"]
    attempt_id = session_payload["attempt_id"]

    submit_response = await client.post(
        f"/api/attempts/{attempt_id}/submit",
        headers={"X-User-ID": learner["id"]},
        json={
            "response_text": (
                "I hear why the date matters to you. The earliest realistic date is next Friday, "
                "and I can confirm scope with the team by tomorrow."
            )
        },
    )
    assert submit_response.status_code == 200
    attempt_payload = submit_response.json()["data"]
    assert attempt_payload["status"] == "assessed"
    assert attempt_payload["assessment"]["overall_score"] == 2
    assert attempt_payload["assessment"]["prompt_version"] == "assessment.quick-practice.v1"

    with app.state.container.session_factory() as session:
        session_record = session.get(PracticeSessionRecord, session_payload["session_id"])
        attempt_record = session.get(AttemptRecord, attempt_id)
        assessment_record = session.get(
            AssessmentRecord, attempt_payload["assessment"]["assessment_id"]
        )
        snapshot_record = (
            session.query(ProgressionSnapshotRecord)
            .filter(ProgressionSnapshotRecord.learner_id == learner["id"])
            .one_or_none()
        )
        recommendation_record = (
            session.query(RecommendationArtifactRecord)
            .filter(RecommendationArtifactRecord.learner_id == learner["id"])
            .one_or_none()
        )
        pipeline_run_names = {
            record.pipeline_name for record in session.query(PipelineRunRecord).all()
        }
        event_types = {record.event_type for record in session.query(WorkflowEventRecord).all()}

    assert session_record is not None and session_record.status == "completed"
    assert attempt_record is not None and attempt_record.status == "assessed"
    assert assessment_record is not None and assessment_record.validation_status == "validated"
    assert snapshot_record is None
    assert recommendation_record is None
    assert "quick_practice_session_start" in pipeline_run_names
    assert "quick_practice_assessment" in pipeline_run_names
    assert "practice.session_started.v1" in event_types
    assert "practice.prompt_delivered.v1" in event_types
    assert "practice.attempt_submitted.v1" in event_types
    assert "assessment.started.v1" in event_types
    assert "assessment.validated.v1" in event_types
    assert "progression.snapshot.created.v1" not in event_types
    assert "recommendation.generated.v1" not in event_types


@pytest.mark.asyncio
async def test_quick_practice_rejects_missing_version_metadata(client, app, test_settings) -> None:
    _migrate(test_settings)
    learner, prompt = await _seed_quick_practice_prompt(client)
    app.state.container.practice_service._assessment_marker = FakeMissingMetadataMarker()

    start_response = await client.post(
        "/api/attempts/quick-practice/sessions",
        headers={"X-User-ID": learner["id"]},
        json={"prompt_item_id": prompt["id"]},
    )
    attempt_id = start_response.json()["data"]["attempt_id"]

    submit_response = await client.post(
        f"/api/attempts/{attempt_id}/submit",
        headers={"X-User-ID": learner["id"]},
        json={
            "response_text": (
                "I hear why the date matters to you. The earliest realistic date is next Friday."
            )
        },
    )
    assert submit_response.status_code == 422
    assert submit_response.json()["error"]["code"] == "SS-VALIDATION-019"

    with app.state.container.session_factory() as session:
        attempt_record = session.get(AttemptRecord, attempt_id)
        assessment_record = session.get(AssessmentRecord, attempt_record.assessment_id)
        event_types = {record.event_type for record in session.query(WorkflowEventRecord).all()}

    assert attempt_record is not None and attempt_record.status == "assessment_rejected"
    assert assessment_record is not None and assessment_record.validation_status == "rejected"
    assert assessment_record.rejection_code == "SS-VALIDATION-019"
    assert "assessment.rejected.v1" in event_types


@pytest.mark.asyncio
async def test_quick_practice_session_start_is_idempotent_per_request_id(
    app, client, test_settings
) -> None:
    _migrate(test_settings)
    learner, prompt = await _seed_quick_practice_prompt(client)

    headers = {
        "X-User-ID": learner["id"],
        "X-Request-ID": "practice-start-fixed-request",
    }

    first_response = await client.post(
        "/api/attempts/quick-practice/sessions",
        headers=headers,
        json={"prompt_item_id": prompt["id"]},
    )
    second_response = await client.post(
        "/api/attempts/quick-practice/sessions",
        headers=headers,
        json={"prompt_item_id": prompt["id"]},
    )

    assert first_response.status_code == 200
    assert second_response.status_code == 200
    assert (
        first_response.json()["data"]["session_id"] == second_response.json()["data"]["session_id"]
    )
    assert (
        first_response.json()["data"]["attempt_id"] == second_response.json()["data"]["attempt_id"]
    )

    with app.state.container.session_factory() as session:
        sessions = session.query(PracticeSessionRecord).all()
        attempts = session.query(AttemptRecord).all()

    assert len(sessions) == 1
    assert len(attempts) == 1


@pytest.mark.asyncio
async def test_quick_practice_marks_attempt_failed_on_provider_error(
    client, app, test_settings
) -> None:
    _migrate(test_settings)
    learner, prompt = await _seed_quick_practice_prompt(client)
    app.state.container.practice_service._assessment_marker = FakeProviderFailureMarker()

    start_response = await client.post(
        "/api/attempts/quick-practice/sessions",
        headers={"X-User-ID": learner["id"]},
        json={"prompt_item_id": prompt["id"]},
    )
    attempt_id = start_response.json()["data"]["attempt_id"]

    submit_response = await client.post(
        f"/api/attempts/{attempt_id}/submit",
        headers={"X-User-ID": learner["id"]},
        json={
            "response_text": (
                "I hear why the date matters to you. The earliest realistic date is next Friday."
            )
        },
    )
    assert submit_response.status_code == 503
    assert submit_response.json()["error"]["code"] == "SS-PROVIDER-099"

    with app.state.container.session_factory() as session:
        attempt_record = session.get(AttemptRecord, attempt_id)
        event_types = {record.event_type for record in session.query(WorkflowEventRecord).all()}

    assert attempt_record is not None and attempt_record.status == "assessment_failed"
    assert attempt_record.last_error_code == "SS-PROVIDER-099"
    assert "error.provider.v1" in event_types
