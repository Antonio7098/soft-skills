from __future__ import annotations

from pathlib import Path

import pytest
from alembic.config import Config

from alembic import command
from soft_skills_backend.platform.db.models import (
    PipelineRunRecord,
    ProgressionSnapshotRecord,
    ProgressRecalculationRecord,
    RecommendationArtifactRecord,
    WorkflowEventRecord,
)


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


async def _seed_prompt(client) -> tuple[dict[str, object], dict[str, object], dict[str, object]]:
    admin = await _register_user(
        client,
        email="admin-progress@example.com",
        display_name="Admin Progress",
    )
    bootstrap_response = await client.post(
        "/api/skills/bootstrap-canon",
        headers={"X-User-ID": admin["id"]},
    )
    assert bootstrap_response.status_code == 200

    learner = await _register_user(
        client,
        email="learner-progress@example.com",
        display_name="Learner Progress",
    )
    collection_response = await client.post(
        "/api/collections",
        headers={"X-User-ID": learner["id"]},
        json={
            "title": "Stakeholder Recovery Pack",
            "summary": "Practice setting expectations when stakeholders push back.",
            "target_audience": "Consultant",
            "difficulty": "intermediate",
            "content_format_mix": ["interview_prompt"],
            "target_skill_slugs": ["active-listening", "decision-justification"],
            "target_competency_slugs": ["adaptability"],
            "rubric_ids": ["interview_text@v1"],
        },
    )
    assert collection_response.status_code == 200
    collection = collection_response.json()["data"]

    prompt_response = await client.post(
        f"/api/collections/{collection['id']}/prompt-items",
        headers={"X-User-ID": learner["id"]},
        json={
            "prompt_type": "interview_prompt",
            "title": "Lead through ambiguity",
            "prompt_text": "Tell me about a time you had to make a decision with incomplete information.",
            "difficulty": "intermediate",
            "target_skill_slugs": ["active-listening", "decision-justification"],
            "rubric_id": "interview_text@v1",
        },
    )
    assert prompt_response.status_code == 200
    return admin, learner, prompt_response.json()["data"]


class FakeSuccessMarker:
    provider_name = "openai"
    model_slug = "gpt-4.1-mini"

    async def mark_attempt(self, *, prompt_payload, learner_payload, call_context):
        from soft_skills_backend.modules.practice.domain.practice import AssessmentDraft
        from soft_skills_backend.modules.practice.workflows.assessment import (
            AssessmentTransformPayload,
        )

        del learner_payload, call_context
        return AssessmentTransformPayload(
            draft=AssessmentDraft.model_validate(
                {
                    "prompt_version": "assessment.quick-practice.v1",
                    "rubric_version": prompt_payload.prompt.rubric_version,
                    "provider": "openai",
                    "model_slug": "gpt-4.1-mini",
                    "overall_score": 4,
                    "rationale": "The response balanced listening with a defensible decision.",
                    "skill_scores": [
                        {
                            "skill_slug": "active-listening",
                            "score": 4,
                            "rationale": "It acknowledged the client concern directly.",
                        },
                        {
                            "skill_slug": "decision-justification",
                            "score": 4,
                            "rationale": "It supported the decision with clear reasoning.",
                        },
                    ],
                    "evidence": [
                        {
                            "skill_slug": "active-listening",
                            "quote": "I first aligned the team on the uncertainty",
                            "explanation": "The learner showed attention to stakeholder alignment.",
                        },
                        {
                            "skill_slug": "decision-justification",
                            "quote": "we chose the lower-risk option because the data was incomplete",
                            "explanation": "The learner justified the decision directly.",
                        },
                    ],
                    "strengths": ["Balanced alignment with a clear rationale."],
                    "weaknesses": ["Could have made the tradeoff framing even crisper."],
                    "next_actions": ["Practice making tradeoffs explicit under uncertainty."],
                }
            ),
            raw_payload={"ok": True},
            model_slug="gpt-4.1-mini",
            schema_version="quick-practice-assessment-output.v1",
        )


async def _submit_assessed_attempt(app, client, learner_id: str, prompt_id: str) -> None:
    app.state.container.practice_service._assessment_marker = FakeSuccessMarker()
    start_response = await client.post(
        "/api/attempts/interview/sessions",
        headers={"X-User-ID": learner_id},
        json={
            "prompt_item_id": prompt_id,
            "competency_context": "Assess structured communication and reasoning.",
            "interviewer_perspective": "Hiring manager at a consulting firm.",
        },
    )
    assert start_response.status_code == 200
    attempt_id = start_response.json()["data"]["attempt_id"]
    submit_response = await client.post(
        f"/api/attempts/{attempt_id}/submit",
        headers={"X-User-ID": learner_id},
        json={
            "response_text": (
                "I first aligned the team on the uncertainty, then we chose the lower-risk option "
                "because the data was incomplete and the downside of a rushed decision was higher."
            )
        },
    )
    assert submit_response.status_code == 200


@pytest.mark.asyncio
async def test_progress_dashboard_returns_latest_snapshot_and_recommendation(
    app, client, test_settings
) -> None:
    _migrate(test_settings)
    _admin, learner, prompt = await _seed_prompt(client)
    await _submit_assessed_attempt(app, client, learner["id"], prompt["id"])

    progress_response = await client.get(
        "/api/progress/me",
        headers={"X-User-ID": learner["id"]},
    )
    assert progress_response.status_code == 200
    payload = progress_response.json()["data"]

    assert payload["snapshot"]["learner_id"] == learner["id"]
    assert payload["snapshot"]["skill_states"]
    assert payload["recommendation"]["learner_id"] == learner["id"]
    assert payload["recommendation"]["items"]
    assert payload["recommendation"]["items"][0]["content_id"] == prompt["id"]

    recommendation_response = await client.get(
        "/api/progress/me/recommendations",
        headers={"X-User-ID": learner["id"]},
    )
    assert recommendation_response.status_code == 200
    assert recommendation_response.json()["data"]["items"]

    with app.state.container.session_factory() as session:
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
        pipeline_names = {record.pipeline_name for record in session.query(PipelineRunRecord).all()}
        event_types = {record.event_type for record in session.query(WorkflowEventRecord).all()}

    assert snapshot_record is not None
    assert recommendation_record is not None
    assert "progression_refresh" in pipeline_names
    assert "progression.snapshot.created.v1" in event_types
    assert "recommendation.generated.v1" in event_types


@pytest.mark.asyncio
async def test_progress_recalculate_creates_audit_record(app, client, test_settings) -> None:
    _migrate(test_settings)
    admin, learner, prompt = await _seed_prompt(client)
    await _submit_assessed_attempt(app, client, learner["id"], prompt["id"])

    recalc_response = await client.post(
        "/api/progress/recalculate",
        headers={"X-User-ID": admin["id"]},
        json={"learner_id": learner["id"], "reason": "verify replay determinism"},
    )
    assert recalc_response.status_code == 200
    payload = recalc_response.json()["data"]
    assert payload["learner_id"] == learner["id"]
    assert payload["status"] == "completed"
    assert payload["next_snapshot_id"]
    assert payload["next_recommendation_id"]

    with app.state.container.session_factory() as session:
        recalc_record = (
            session.query(ProgressRecalculationRecord)
            .filter(ProgressRecalculationRecord.learner_id == learner["id"])
            .one_or_none()
        )

    assert recalc_record is not None
    assert recalc_record.status == "completed"
