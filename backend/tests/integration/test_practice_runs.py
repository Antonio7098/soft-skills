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
    PracticeRunRecord,
    PracticeSessionRecord,
    WorkflowEventRecord,
)
from soft_skills_backend.shared.errors import provider_error


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


async def _bootstrap_admin_and_learner(
    client, *, learner_email: str = "learner-practice-run@example.com"
) -> tuple[dict[str, object], dict[str, object]]:
    admin = await _register_user(
        client,
        email="admin-practice-run@example.com",
        display_name="Admin Practice Run",
    )
    bootstrap_response = await client.post(
        "/api/skills/bootstrap-canon",
        headers={"X-User-ID": admin["id"]},
    )
    assert bootstrap_response.status_code == 200
    learner = await _register_user(
        client,
        email=learner_email,
        display_name="Learner Practice Run",
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
            "summary": "Practice run coverage collection.",
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


async def _seed_quick_practice_prompt(client, learner_id: str) -> dict[str, object]:
    collection = await _create_collection(
        client,
        learner_id=learner_id,
        title="Quick Practice Run Pack",
        content_format_mix=["quick_practice_prompt"],
        rubric_ids=["quick_practice_reset_timeline@v1"],
        target_skill_slugs=["active-listening", "expectation-setting"],
        target_competency_slugs=["stakeholder-management"],
    )
    response = await client.post(
        f"/api/collections/{collection['id']}/prompt-items",
        headers={"X-User-ID": learner_id},
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
    assert response.status_code == 200
    return response.json()["data"]


async def _seed_interview_prompt(client, learner_id: str) -> dict[str, object]:
    collection = await _create_collection(
        client,
        learner_id=learner_id,
        title="Interview Practice Run Pack",
        content_format_mix=["interview_prompt"],
        rubric_ids=["interview_text@v1"],
        target_skill_slugs=["active-listening", "decision-justification"],
        target_competency_slugs=["adaptability"],
    )
    response = await client.post(
        f"/api/collections/{collection['id']}/prompt-items",
        headers={"X-User-ID": learner_id},
        json={
            "prompt_type": "interview_prompt",
            "title": "Lead through ambiguity",
            "prompt_text": "Tell me about a time you had to lead a decision with incomplete information.",
            "difficulty": "intermediate",
            "target_skill_slugs": ["active-listening", "decision-justification"],
            "rubric_id": "interview_text@v1",
        },
    )
    assert response.status_code == 200
    return response.json()["data"]


async def _seed_scenario(client, learner_id: str) -> dict[str, object]:
    collection = await _create_collection(
        client,
        learner_id=learner_id,
        title="Scenario Practice Run Pack",
        content_format_mix=["scenario_step"],
        rubric_ids=["scenario_text@v1"],
        target_skill_slugs=["expectation-setting", "prioritization-under-pressure"],
        target_competency_slugs=["managing-ambiguity"],
    )
    response = await client.post(
        f"/api/collections/{collection['id']}/scenarios",
        headers={"X-User-ID": learner_id},
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
    assert response.status_code == 200
    return response.json()["data"]


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
                    "overall_score": (
                        2 if prompt_payload.prompt.practice_type.value == "quick_practice" else 4
                    ),
                    "rationale": "The response addressed the prompt with a credible next step.",
                    "skill_scores": [
                        {
                            "skill_slug": slug,
                            "score": (
                                2
                                if prompt_payload.prompt.practice_type.value == "quick_practice"
                                else 4
                            ),
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
                    "strengths": ["Stayed grounded in the prompt and stakeholder context."],
                    "weaknesses": ["Could have added one clearer follow-up checkpoint."],
                    "next_actions": ["Practice closing with a concrete owner and deadline."],
                }
            ),
            raw_payload={"ok": True, "practice_type": prompt_payload.prompt.practice_type.value},
            model_slug="gpt-4.1-mini",
            schema_version="quick-practice-assessment-output.v1",
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
async def test_practice_run_start_submit_review_and_history(app, client, test_settings) -> None:
    _migrate(test_settings)
    _, learner = await _bootstrap_admin_and_learner(client)
    learner_id = learner["id"]
    quick_prompt = await _seed_quick_practice_prompt(client, learner_id)
    interview_prompt = await _seed_interview_prompt(client, learner_id)
    scenario = await _seed_scenario(client, learner_id)
    app.state.container.practice_service._assessment_marker = FakeSuccessMarker()

    start_response = await client.post(
        "/api/practice-runs",
        headers={"X-User-ID": learner_id},
        json={
            "items": [
                {"practice_type": "quick_practice", "prompt_item_id": quick_prompt["id"]},
                {
                    "practice_type": "interview",
                    "prompt_item_id": interview_prompt["id"],
                    "competency_context": "Focus on tradeoffs, ownership, and clarity.",
                    "interviewer_perspective": "You are responding to a consulting hiring manager.",
                },
                {
                    "practice_type": "scenario",
                    "scenario_id": scenario["id"],
                    "artifacts": [
                        {
                            "artifact_type": "email",
                            "title": "CEO escalation note",
                            "body": "The board expects a crisp recommendation before 9am.",
                        }
                    ],
                },
            ]
        },
    )
    assert start_response.status_code == 200
    run_payload = start_response.json()["data"]
    run_id = run_payload["run_id"]
    items = run_payload["items"]

    assert run_payload["status"] == "active"
    assert run_payload["total_items"] == 3
    assert run_payload["completed_items"] == 0
    assert run_payload["validated_items"] == 0
    assert run_payload["failed_items"] == 0
    assert run_payload["summary"]["validated_attempt_count"] == 0
    assert run_payload["summary"]["overall_score_average"] is None
    assert len(items) == 3
    assert items[0]["attempt"]["prompt"]["practice_type"] == "quick_practice"
    assert items[1]["attempt"]["prompt"]["practice_type"] == "interview"
    assert items[2]["attempt"]["prompt"]["practice_type"] == "scenario"
    assert run_payload["current_attempt_id"] == items[0]["attempt"]["id"]

    first_attempt_id = items[0]["attempt"]["id"]
    second_attempt_id = items[1]["attempt"]["id"]
    third_attempt_id = items[2]["attempt"]["id"]

    first_submit = await client.post(
        f"/api/attempts/{first_attempt_id}/submit",
        headers={"X-User-ID": learner_id},
        json={
            "response_text": (
                "I hear why the date matters to you. The earliest realistic date is next Friday, "
                "and I can confirm the scope tradeoffs with the team by tomorrow."
            )
        },
    )
    assert first_submit.status_code == 200

    mid_run_response = await client.get(
        f"/api/practice-runs/{run_id}",
        headers={"X-User-ID": learner_id},
    )
    assert mid_run_response.status_code == 200
    mid_run_payload = mid_run_response.json()["data"]
    assert mid_run_payload["status"] == "active"
    assert mid_run_payload["completed_items"] == 1
    assert mid_run_payload["validated_items"] == 1
    assert mid_run_payload["failed_items"] == 0
    assert mid_run_payload["summary"]["validated_attempt_count"] == 1
    assert mid_run_payload["summary"]["overall_score_average"] == 2.0
    assert mid_run_payload["current_attempt_id"] == second_attempt_id

    second_submit = await client.post(
        f"/api/attempts/{second_attempt_id}/submit",
        headers={"X-User-ID": learner_id},
        json={
            "response_text": (
                "I clarified the tradeoff, explained the risk to the sponsor, "
                "and set a named owner for the next-morning checkpoint."
            )
        },
    )
    assert second_submit.status_code == 200

    third_submit = await client.post(
        f"/api/attempts/{third_attempt_id}/submit",
        headers={"X-User-ID": learner_id},
        json={
            "response_text": (
                "I would recommend a one-day delay, explain the legal risk directly, "
                "and propose a 7am checkpoint with sales and legal before the board discussion."
            )
        },
    )
    assert third_submit.status_code == 200

    complete_run_response = await client.get(
        f"/api/practice-runs/{run_id}",
        headers={"X-User-ID": learner_id},
    )
    assert complete_run_response.status_code == 200
    complete_run_payload = complete_run_response.json()["data"]
    assert complete_run_payload["status"] == "completed"
    assert complete_run_payload["completed_items"] == 3
    assert complete_run_payload["validated_items"] == 3
    assert complete_run_payload["failed_items"] == 0
    assert complete_run_payload["current_attempt_id"] is None
    assert complete_run_payload["summary"]["validated_attempt_count"] == 3
    assert complete_run_payload["summary"]["failed_attempt_count"] == 0
    assert complete_run_payload["summary"]["overall_score_average"] == 3.33
    assert complete_run_payload["summary"]["score_distribution"] == {
        "1": 0,
        "2": 1,
        "3": 0,
        "4": 2,
        "5": 0,
    }
    assert complete_run_payload["summary"]["practice_type_breakdown"] == [
        {"practice_type": "interview", "average_score": 4.0, "count": 1},
        {"practice_type": "quick_practice", "average_score": 2.0, "count": 1},
        {"practice_type": "scenario", "average_score": 4.0, "count": 1},
    ]
    assert complete_run_payload["summary"]["skill_breakdown"] == [
        {"skill_slug": "active-listening", "average_score": 3.0, "count": 2},
        {"skill_slug": "decision-justification", "average_score": 4.0, "count": 1},
        {"skill_slug": "expectation-setting", "average_score": 3.0, "count": 2},
        {"skill_slug": "prioritization-under-pressure", "average_score": 4.0, "count": 1},
    ]

    history_response = await client.get(
        "/api/practice-runs",
        headers={"X-User-ID": learner_id},
    )
    assert history_response.status_code == 200
    history_payload = history_response.json()["data"]
    assert len(history_payload) == 1
    assert history_payload[0]["run_id"] == run_id
    assert history_payload[0]["status"] == "completed"
    assert history_payload[0]["overall_score_average"] == 3.33
    assert history_payload[0]["practice_types"] == [
        "quick_practice",
        "interview",
        "scenario",
    ]

    other_learner = await _register_user(
        client,
        email="practice-run-other@example.com",
        display_name="Other Learner",
    )
    forbidden_response = await client.get(
        f"/api/practice-runs/{run_id}",
        headers={"X-User-ID": other_learner["id"]},
    )
    assert forbidden_response.status_code == 403
    other_history_response = await client.get(
        "/api/practice-runs",
        headers={"X-User-ID": other_learner["id"]},
    )
    assert other_history_response.status_code == 200
    assert other_history_response.json()["data"] == []

    with app.state.container.session_factory() as session:
        run_record = session.get(PracticeRunRecord, run_id)
        session_records = (
            session.query(PracticeSessionRecord)
            .filter(PracticeSessionRecord.practice_run_id == run_id)
            .order_by(PracticeSessionRecord.sequence_index.asc())
            .all()
        )
        attempt_records = (
            session.query(AttemptRecord)
            .filter(AttemptRecord.session_id.in_([record.id for record in session_records]))
            .all()
        )
        assessment_records = (
            session.query(AssessmentRecord)
            .filter(AssessmentRecord.session_id.in_([record.id for record in session_records]))
            .all()
        )
        event_types = {record.event_type for record in session.query(WorkflowEventRecord).all()}

    assert run_record is not None and run_record.status == "completed"
    assert run_record.completed_items == 3
    assert run_record.validated_items == 3
    assert run_record.failed_items == 0
    assert [record.sequence_index for record in session_records] == [1, 2, 3]
    assert all(record.status == "completed" for record in session_records)
    assert len(attempt_records) == 3 and all(
        record.status == "assessed" for record in attempt_records
    )
    assert len(assessment_records) == 3
    assert "practice.run_started.v1" in event_types
    assert "practice.session_started.v1" in event_types
    assert "assessment.validated.v1" in event_types


@pytest.mark.asyncio
async def test_practice_run_completes_with_failed_items_and_excludes_them_from_average(
    app, client, test_settings
) -> None:
    _migrate(test_settings)
    _, learner = await _bootstrap_admin_and_learner(
        client, learner_email="learner-practice-run-failure@example.com"
    )
    learner_id = learner["id"]
    quick_prompt = await _seed_quick_practice_prompt(client, learner_id)
    interview_prompt = await _seed_interview_prompt(client, learner_id)
    app.state.container.practice_service._assessment_marker = FakeSuccessMarker()

    start_response = await client.post(
        "/api/practice-runs",
        headers={"X-User-ID": learner_id},
        json={
            "items": [
                {"practice_type": "quick_practice", "prompt_item_id": quick_prompt["id"]},
                {"practice_type": "interview", "prompt_item_id": interview_prompt["id"]},
            ]
        },
    )
    assert start_response.status_code == 200
    run_payload = start_response.json()["data"]
    run_id = run_payload["run_id"]
    first_attempt_id = run_payload["items"][0]["attempt"]["id"]
    second_attempt_id = run_payload["items"][1]["attempt"]["id"]

    first_submit = await client.post(
        f"/api/attempts/{first_attempt_id}/submit",
        headers={"X-User-ID": learner_id},
        json={
            "response_text": (
                "I hear the concern, the earliest realistic date is next Friday, "
                "and I will confirm scope by tomorrow."
            )
        },
    )
    assert first_submit.status_code == 200

    app.state.container.practice_service._assessment_marker = FakeProviderFailureMarker()
    second_submit = await client.post(
        f"/api/attempts/{second_attempt_id}/submit",
        headers={"X-User-ID": learner_id},
        json={
            "response_text": (
                "I clarified the ambiguity, outlined the tradeoff, "
                "and proposed a checkpoint for the next morning."
            )
        },
    )
    assert second_submit.status_code == 503
    assert second_submit.json()["error"]["code"] == "SS-PROVIDER-099"

    run_response = await client.get(
        f"/api/practice-runs/{run_id}",
        headers={"X-User-ID": learner_id},
    )
    assert run_response.status_code == 200
    payload = run_response.json()["data"]
    assert payload["status"] == "completed"
    assert payload["completed_items"] == 2
    assert payload["validated_items"] == 1
    assert payload["failed_items"] == 1
    assert payload["summary"]["validated_attempt_count"] == 1
    assert payload["summary"]["failed_attempt_count"] == 1
    assert payload["summary"]["overall_score_average"] == 2.0
    assert payload["summary"]["score_distribution"] == {
        "1": 0,
        "2": 1,
        "3": 0,
        "4": 0,
        "5": 0,
    }
    assert payload["items"][1]["attempt"]["status"] == "assessment_failed"
    assert payload["items"][1]["attempt"]["assessment"] is None

    with app.state.container.session_factory() as session:
        run_record = session.get(PracticeRunRecord, run_id)
        failed_attempt = session.get(AttemptRecord, second_attempt_id)

    assert run_record is not None and run_record.failed_items == 1
    assert failed_attempt is not None and failed_attempt.status == "assessment_failed"


@pytest.mark.asyncio
async def test_practice_run_start_is_idempotent_per_request_id(app, client, test_settings) -> None:
    _migrate(test_settings)
    _, learner = await _bootstrap_admin_and_learner(
        client, learner_email="learner-practice-run-idempotent@example.com"
    )
    learner_id = learner["id"]
    quick_prompt = await _seed_quick_practice_prompt(client, learner_id)
    interview_prompt = await _seed_interview_prompt(client, learner_id)

    headers = {
        "X-User-ID": learner_id,
        "X-Request-ID": "practice-run-fixed-request",
    }
    body = {
        "items": [
            {"practice_type": "quick_practice", "prompt_item_id": quick_prompt["id"]},
            {"practice_type": "interview", "prompt_item_id": interview_prompt["id"]},
        ]
    }

    first_response = await client.post("/api/practice-runs", headers=headers, json=body)
    second_response = await client.post("/api/practice-runs", headers=headers, json=body)

    assert first_response.status_code == 200
    assert second_response.status_code == 200
    first_payload = first_response.json()["data"]
    second_payload = second_response.json()["data"]
    assert first_payload["run_id"] == second_payload["run_id"]
    assert first_payload["workflow_id"] == second_payload["workflow_id"]
    assert [item["attempt"]["id"] for item in first_payload["items"]] == [
        item["attempt"]["id"] for item in second_payload["items"]
    ]
