from __future__ import annotations

from pathlib import Path

import pytest
from alembic.config import Config

from alembic import command
from soft_skills_backend.modules.practice.domain.practice import AssessmentDraft
from soft_skills_backend.modules.practice.workflows.assessment import (
    AssessmentTransformPayload,
    ResolvedAttemptPayload,
)
from soft_skills_backend.platform.db.models import (
    AssessmentRecord,
    AttemptRecord,
    PracticeSessionRecord,
    ScenarioRecord,
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


async def _bootstrap_admin_and_learner(client) -> tuple[dict[str, object], dict[str, object]]:
    admin = await _register_user(
        client,
        email="admin-runtime@example.com",
        display_name="Admin Runtime",
    )
    bootstrap_response = await client.post(
        "/api/skills/bootstrap-canon",
        headers={"X-User-ID": admin["id"]},
    )
    assert bootstrap_response.status_code == 200
    learner = await _register_user(
        client,
        email="learner-runtime@example.com",
        display_name="Learner Runtime",
    )
    return admin, learner


async def _create_collection(
    client,
    *,
    learner_id: str,
    title: str,
    content_format_mix: list[str],
    rubric_ids: list[str],
    target_skill_slugs: list[str],
    target_competency_slugs: list[str],
) -> dict[str, object]:
    response = await client.post(
        "/api/collections",
        headers={"X-User-ID": learner_id},
        json={
            "title": title,
            "summary": "Runtime coverage collection.",
            "target_audience": "Early-career consultants",
            "difficulty": "intermediate",
            "content_format_mix": content_format_mix,
            "target_skill_slugs": target_skill_slugs,
            "target_competency_slugs": target_competency_slugs,
            "rubric_ids": rubric_ids,
        },
    )
    assert response.status_code == 200
    return response.json()["data"]


async def _seed_interview_prompt(client) -> tuple[dict[str, object], dict[str, object]]:
    _, learner = await _bootstrap_admin_and_learner(client)
    collection = await _create_collection(
        client,
        learner_id=str(learner["id"]),
        title="Behavioral Interview Pack",
        content_format_mix=["interview_prompt"],
        rubric_ids=["interview_text@v1"],
        target_skill_slugs=["active-listening", "decision-justification"],
        target_competency_slugs=["adaptability"],
    )
    prompt_response = await client.post(
        f"/api/collections/{collection['id']}/prompt-items",
        headers={"X-User-ID": learner["id"]},
        json={
            "prompt_type": "interview_prompt",
            "title": "Leading through ambiguity",
            "prompt_text": "Tell me about a time you had to lead a decision with incomplete information.",
            "difficulty": "intermediate",
            "target_skill_slugs": ["active-listening", "decision-justification"],
            "rubric_id": "interview_text@v1",
        },
    )
    assert prompt_response.status_code == 200
    return learner, prompt_response.json()["data"]


async def _seed_scenario(client) -> tuple[dict[str, object], dict[str, object]]:
    _, learner = await _bootstrap_admin_and_learner(client)
    collection = await _create_collection(
        client,
        learner_id=str(learner["id"]),
        title="Stakeholder Pressure Scenarios",
        content_format_mix=["scenario_step"],
        rubric_ids=["scenario_text@v1"],
        target_skill_slugs=["expectation-setting", "prioritization-under-pressure"],
        target_competency_slugs=["managing-ambiguity"],
    )
    scenario_response = await client.post(
        f"/api/collections/{collection['id']}/scenarios",
        headers={"X-User-ID": learner["id"]},
        json={
            "title": "Escalating launch risk",
            "business_context": "An AI feature launch is at risk after legal review surfaced new concerns.",
            "learner_objective": "Re-align the executive sponsor without hiding the delivery risk.",
            "constraints": ["The launch date is on the board agenda tomorrow."],
            "stakeholder_tensions": ["Legal wants a delay, sales wants the current date."],
            "target_skill_slugs": [
                "expectation-setting",
                "prioritization-under-pressure",
            ],
            "rubric_id": "scenario_text@v1",
            "mock_company": {
                "name": "Northstar AI",
                "industry": "Enterprise SaaS",
                "operating_context": "Scaling fast with heavy board scrutiny.",
            },
            "mock_people": [
                {
                    "name": "Maya Chen",
                    "role": "VP Sales",
                    "goals": ["Hit the quarterly launch target"],
                    "communication_style": "Direct and urgent",
                    "relationship_to_scenario": "Primary escalation partner",
                },
                {
                    "name": "Jordan Singh",
                    "role": "Legal Counsel",
                    "goals": ["Reduce regulatory exposure"],
                    "communication_style": "Precise and cautious",
                    "relationship_to_scenario": "Risk owner blocking launch approval",
                },
            ],
        },
    )
    assert scenario_response.status_code == 200
    return learner, scenario_response.json()["data"]


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
                    "overall_score": 4,
                    "rationale": "The response addressed the core pressure points with a credible next step.",
                    "skill_scores": [
                        {
                            "skill_slug": slug,
                            "score": 4,
                            "rationale": f"The response demonstrated {slug}.",
                        }
                        for slug in prompt_payload.prompt.target_skill_slugs
                    ],
                    "evidence": [
                        {
                            "skill_slug": slug,
                            "quote": prompt_payload.response_text,
                            "explanation": f"The response text provided direct evidence for {slug}.",
                        }
                        for slug in prompt_payload.prompt.target_skill_slugs
                    ],
                    "strengths": ["Stayed grounded in the actual prompt and stakeholder risk."],
                    "weaknesses": ["Could have added one clearer follow-up checkpoint."],
                    "next_actions": ["Practice closing with a concrete owner and deadline."],
                }
            ),
            raw_payload={"ok": True, "practice_type": prompt_payload.prompt.practice_type.value},
            model_slug="gpt-4.1-mini",
            schema_version="quick-practice-assessment-output.v1",
        )


@pytest.mark.asyncio
async def test_interview_runtime_reuses_shared_assessment_backbone(
    app, client, test_settings
) -> None:
    _migrate(test_settings)
    learner, prompt = await _seed_interview_prompt(client)
    app.state.container.practice_service._assessment_marker = FakeSuccessMarker()

    start_response = await client.post(
        "/api/attempts/interview/sessions",
        headers={"X-User-ID": learner["id"]},
        json={
            "prompt_item_id": prompt["id"],
            "competency_context": "Focus on tradeoffs, communication, and ownership.",
            "interviewer_perspective": "You are speaking to a consulting manager hiring for a client-facing role.",
        },
    )
    assert start_response.status_code == 200
    session_payload = start_response.json()["data"]
    assert session_payload["prompt"]["practice_type"] == "interview"
    assert session_payload["prompt"]["prompt_type"] == "interview_prompt"
    assert session_payload["prompt"]["interview_context"]["competency_context"].startswith(
        "Focus on tradeoffs"
    )

    submit_response = await client.post(
        f"/api/attempts/{session_payload['attempt_id']}/submit",
        headers={"X-User-ID": learner["id"]},
        json={
            "response_text": (
                "I clarified the ambiguous constraints with the team, explained the tradeoff to the sponsor, "
                "and proposed a decision checkpoint for the next morning."
            )
        },
    )
    assert submit_response.status_code == 200
    attempt_payload = submit_response.json()["data"]
    assert attempt_payload["status"] == "assessed"
    assert attempt_payload["prompt"]["practice_type"] == "interview"

    with app.state.container.session_factory() as session:
        session_record = session.get(PracticeSessionRecord, session_payload["session_id"])
        attempt_record = session.get(AttemptRecord, session_payload["attempt_id"])
        assessment_record = session.get(
            AssessmentRecord, attempt_payload["assessment"]["assessment_id"]
        )
        event_types = {record.event_type for record in session.query(WorkflowEventRecord).all()}

    assert session_record is not None and session_record.practice_type == "interview"
    assert attempt_record is not None and attempt_record.practice_type == "interview"
    assert assessment_record is not None and assessment_record.practice_type == "interview"
    assert "assessment.started.v1" in event_types
    assert "assessment.validated.v1" in event_types


@pytest.mark.asyncio
async def test_scenario_runtime_persists_rich_context_and_artifacts(
    app, client, test_settings
) -> None:
    _migrate(test_settings)
    learner, scenario = await _seed_scenario(client)
    app.state.container.practice_service._assessment_marker = FakeSuccessMarker()

    start_response = await client.post(
        "/api/attempts/scenario/sessions",
        headers={"X-User-ID": learner["id"]},
        json={
            "scenario_id": scenario["id"],
            "artifacts": [
                {
                    "artifact_type": "email",
                    "title": "CEO escalation note",
                    "body": "The board expects a crisp recommendation before 9am.",
                }
            ],
        },
    )
    assert start_response.status_code == 200
    session_payload = start_response.json()["data"]
    assert session_payload["prompt"]["practice_type"] == "scenario"
    assert session_payload["prompt"]["scenario_context"]["mock_people"][0]["name"] == "Jordan Singh"
    assert session_payload["prompt"]["scenario_context"]["artifacts"][0]["title"] == (
        "CEO escalation note"
    )

    submit_response = await client.post(
        f"/api/attempts/{session_payload['attempt_id']}/submit",
        headers={"X-User-ID": learner["id"]},
        json={
            "response_text": (
                "I would tell the sponsor we need a controlled one-day delay, explain the legal risk directly, "
                "and propose a 7am checkpoint with sales and legal before the board discussion."
            )
        },
    )
    assert submit_response.status_code == 200
    attempt_payload = submit_response.json()["data"]
    assert attempt_payload["status"] == "assessed"
    assert attempt_payload["prompt"]["practice_type"] == "scenario"

    with app.state.container.session_factory() as session:
        session_record = session.get(PracticeSessionRecord, session_payload["session_id"])
        attempt_record = session.get(AttemptRecord, session_payload["attempt_id"])
        assessment_record = session.get(
            AssessmentRecord, attempt_payload["assessment"]["assessment_id"]
        )
        event_types = {record.event_type for record in session.query(WorkflowEventRecord).all()}

    assert session_record is not None and session_record.practice_type == "scenario"
    assert attempt_record is not None and attempt_record.practice_type == "scenario"
    assert assessment_record is not None and assessment_record.practice_type == "scenario"
    assert (
        session_record.prompt_payload["scenario_context"]["artifacts"][0]["artifact_type"]
        == "email"
    )
    assert "practice.session_started.v1" in event_types
    assert "assessment.validated.v1" in event_types


@pytest.mark.asyncio
async def test_quick_practice_session_rejects_interview_prompt(client, test_settings) -> None:
    _migrate(test_settings)
    learner, prompt = await _seed_interview_prompt(client)

    response = await client.post(
        "/api/attempts/quick-practice/sessions",
        headers={"X-User-ID": learner["id"]},
        json={"prompt_item_id": prompt["id"]},
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "SS-VALIDATION-021"


@pytest.mark.asyncio
async def test_scenario_session_rejects_invalid_rubric_mapping(app, client, test_settings) -> None:
    _migrate(test_settings)
    learner, scenario = await _seed_scenario(client)

    with app.state.container.session_factory() as session:
        record = session.get(ScenarioRecord, scenario["id"])
        assert record is not None
        record.rubric_id = "quick_practice_text@v1"
        session.commit()

    response = await client.post(
        "/api/attempts/scenario/sessions",
        headers={"X-User-ID": learner["id"]},
        json={"scenario_id": scenario["id"]},
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "SS-VALIDATION-027"
