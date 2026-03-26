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
            "content_format_mix": ["quick_practice_prompt"],
            "target_skill_slugs": ["active-listening", "expectation-setting"],
            "target_competency_slugs": ["stakeholder-management"],
            "rubric_ids": ["quick_practice_text@v1"],
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
            "rubric_id": "quick_practice_text@v1",
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
                    "rationale": "The response balanced empathy with a realistic commitment.",
                    "skill_scores": [
                        {
                            "skill_slug": "active-listening",
                            "score": 4,
                            "rationale": "It acknowledged the client concern directly.",
                        },
                        {
                            "skill_slug": "expectation-setting",
                            "score": 3,
                            "rationale": "It set a next step but could tighten the boundary.",
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
                    "weaknesses": ["Could have named a firmer checkpoint and owner."],
                    "next_actions": ["Practice tighter expectation-setting under pressure."],
                }
            ),
            raw_payload={"ok": True},
            model_slug="gpt-4.1-mini",
            schema_version="quick-practice-assessment-output.v1",
        )


async def _submit_assessed_attempt(app, client, learner_id: str, prompt_id: str) -> None:
    app.state.container.practice_service._assessment_marker = FakeSuccessMarker()
    start_response = await client.post(
        "/api/attempts/quick-practice/sessions",
        headers={"X-User-ID": learner_id},
        json={"prompt_item_id": prompt_id},
    )
    assert start_response.status_code == 200
    attempt_id = start_response.json()["data"]["attempt_id"]
    submit_response = await client.post(
        f"/api/attempts/{attempt_id}/submit",
        headers={"X-User-ID": learner_id},
        json={
            "response_text": (
                "I hear why the date matters to you. The earliest realistic date is next Friday, "
                "and I can confirm scope with the team by tomorrow."
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
