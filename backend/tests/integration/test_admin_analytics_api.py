"""Integration tests for extended admin analytics APIs."""

from __future__ import annotations

from pathlib import Path

import pytest
from alembic.config import Config

from alembic import command


def _migrate(test_settings) -> None:
    alembic_config = Config(str(Path(__file__).resolve().parents[2] / "alembic.ini"))
    alembic_config.set_main_option("sqlalchemy.url", test_settings.database_url)
    command.upgrade(alembic_config, "heads")


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


async def _create_org_and_make_admin(
    client, *, email: str, display_name: str, org_name: str, org_slug: str
):
    user = await _register_user(client, email=email, display_name=display_name)
    org_response = await client.post(
        "/api/organisations",
        headers={"X-User-ID": user["id"]},
        json={"name": org_name, "slug": org_slug},
    )
    assert org_response.status_code == 200
    org = org_response.json()["data"]
    return user, org


ALL_SKILL_SLUGS = [
    "active-listening",
    "concise-explanation",
    "conflict-handling",
    "decision-justification",
    "empathy",
    "executive-summary",
    "expectation-setting",
    "negotiation",
    "prioritization-under-pressure",
    "structured-communication",
]

RUBRIC_SKILL_RATIONALES = {
    "active-listening": "It acknowledged the client concern directly.",
    "concise-explanation": "The explanation was clear and to the point.",
    "conflict-handling": "It addressed the conflict professionally.",
    "decision-justification": "The decision was well-reasoned and justified.",
    "empathy": "The response showed genuine understanding of the client's perspective.",
    "executive-summary": "The key points were summarized effectively.",
    "expectation-setting": "It set a next step but could tighten the boundary.",
    "negotiation": "It proposed a reasonable path forward.",
    "prioritization-under-pressure": "It appropriately prioritized the most urgent items.",
    "structured-communication": "The response was well-organized and structured.",
}


class FakeSuccessMarker:
    provider_name = "openai"
    model_slug = "gpt-4.1-mini"

    async def mark_attempt(self, *, prompt_payload, learner_payload, call_context):
        del learner_payload, call_context
        from soft_skills_backend.modules.practice.domain.practice import AssessmentDraft
        from soft_skills_backend.modules.practice.workflows.assessment import (
            AssessmentTransformPayload,
        )

        rubric_version = prompt_payload.prompt.rubric_version
        skill_scores = []
        evidence = []
        learner_response = "I hear why the date matters to you. The earliest realistic date is next Friday, and I can confirm scope with the team by tomorrow."
        for slug in ALL_SKILL_SLUGS:
            skill_scores.append(
                {
                    "skill_slug": slug,
                    "score": 3,
                    "rationale": RUBRIC_SKILL_RATIONALES.get(slug, "Assessed positively."),
                }
            )
            evidence.append(
                {
                    "skill_slug": slug,
                    "quote": learner_response,
                    "explanation": RUBRIC_SKILL_RATIONALES.get(slug, "Good response."),
                }
            )

        return AssessmentTransformPayload(
            draft=AssessmentDraft.model_validate(
                {
                    "prompt_version": "assessment.quick-practice.v1",
                    "rubric_version": rubric_version,
                    "provider": "openai",
                    "model_slug": "gpt-4.1-mini",
                    "overall_score": 4,
                    "rationale": "The response balanced empathy with a realistic commitment.",
                    "skill_scores": skill_scores,
                    "evidence": evidence,
                    "strengths": ["Acknowledged the client concern before resetting expectations."],
                    "weaknesses": ["Could have named a firmer checkpoint and owner."],
                    "next_actions": ["Practice tighter expectation-setting under pressure."],
                }
            ),
            raw_payload={"ok": True},
            model_slug="gpt-4.1-mini",
            schema_version="quick-practice-assessment-output.v1",
        )


async def _seed_assessed_attempt(app, client, org_id: str, admin_id: str | None = None):
    learner_resp = await client.post(
        "/api/auth/register",
        json={
            "email": "learner-analytics@example.com",
            "display_name": "Learner Analytics",
            "target_role": "Consultant",
            "goals": ["Improve stakeholder handling"],
            "practice_preferences": {"session_length": "short"},
        },
    )
    assert learner_resp.status_code == 200
    learner = learner_resp.json()["data"]

    bootstrap_resp = await client.post(
        "/api/skills/bootstrap-canon", headers={"X-User-ID": learner["id"]}
    )
    print(f"Bootstrap: {bootstrap_resp.status_code}")

    if admin_id is None:
        admin_id = learner["id"]
    add_member_resp = await client.post(
        f"/api/organisations/{org_id}/members",
        headers={"X-User-ID": admin_id, "X-Organisation-ID": org_id},
        json={"user_id": learner["id"], "role": "member"},
    )
    print(f"Add member: {add_member_resp.status_code}")

    collection_response = await client.post(
        "/api/collections",
        headers={"X-User-ID": learner["id"], "X-Organisation-ID": org_id},
        json={
            "title": "Analytics Test Pack",
            "summary": "Collection for testing analytics flows.",
            "target_audience": "Consultant",
            "difficulty": "intermediate",
            "content_format_mix": ["quick_practice_prompt"],
            "target_skill_slugs": ["active-listening", "expectation-setting"],
            "target_competency_slugs": ["stakeholder-management"],
            "rubric_ids": ["quick_practice_text@v1"],
            "organisation_id": org_id,
        },
    )
    assert collection_response.status_code == 200
    collection = collection_response.json()["data"]
    collection_id = collection["id"]

    prompt_response = await client.post(
        f"/api/collections/{collection_id}/prompt-items",
        headers={"X-User-ID": learner["id"], "X-Organisation-ID": org_id},
        json={
            "prompt_type": "quick_practice_prompt",
            "title": "Reset expectations",
            "prompt_text": "A client asks for an impossible timeline. Respond.",
            "difficulty": "intermediate",
            "target_skill_slugs": ["active-listening", "expectation-setting"],
            "rubric_id": "quick_practice_text@v1",
        },
    )
    assert prompt_response.status_code == 200
    prompt = prompt_response.json()["data"]

    app.state.container.practice_service._assessment_marker = FakeSuccessMarker()
    start_response = await client.post(
        "/api/attempts/quick-practice/sessions",
        headers={"X-User-ID": learner["id"]},
        json={"prompt_item_id": prompt["id"]},
    )
    assert start_response.status_code == 200
    attempt_id = start_response.json()["data"]["attempt_id"]

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
    return learner, collection, prompt, submit_response.json()["data"]


@pytest.mark.asyncio
async def test_analytics_overview_endpoint(app, client, test_settings) -> None:
    _migrate(test_settings)
    admin, org = await _create_org_and_make_admin(
        client,
        email="admin-overview@example.com",
        display_name="Admin Overview",
        org_name="Overview Test Org",
        org_slug="overview-test-org",
    )
    org_id = org["id"]

    await _seed_assessed_attempt(app, client, org_id, admin_id=admin["id"])

    overview_response = await client.get(
        "/api/admin/analytics/overview",
        headers={"X-User-ID": admin["id"], "X-Organisation-ID": org_id},
    )
    assert overview_response.status_code == 200
    overview = overview_response.json()["data"]
    assert "total_learners" in overview
    assert "active_learners_30d" in overview
    assert "total_sessions" in overview
    assert "total_attempts" in overview
    assert "overall_usage_trend" in overview
    assert "top_weak_skills" in overview
    assert "cohort_breakdown" in overview
    assert "provider_summary" in overview


@pytest.mark.asyncio
async def test_analytics_overview_with_time_range(app, client, test_settings) -> None:
    _migrate(test_settings)
    admin, org = await _create_org_and_make_admin(
        client,
        email="admin-timerange@example.com",
        display_name="Admin TimeRange",
        org_name="TimeRange Test Org",
        org_slug="timerange-test-org",
    )
    org_id = org["id"]

    await _seed_assessed_attempt(app, client, org_id, admin_id=admin["id"])

    from datetime import datetime, timezone

    now = datetime.now(timezone.utc)
    from_date = now.replace(year=2020, month=1, day=1)
    to_date = now.replace(year=2030, month=12, day=31)

    overview_response = await client.get(
        "/api/admin/analytics/overview",
        headers={"X-User-ID": admin["id"], "X-Organisation-ID": org_id},
        params={
            "from_date": from_date.isoformat(),
            "to_date": to_date.isoformat(),
        },
    )
    assert overview_response.status_code == 200


@pytest.mark.asyncio
async def test_cohort_comparison_endpoint(app, client, test_settings) -> None:
    _migrate(test_settings)
    admin, org = await _create_org_and_make_admin(
        client,
        email="admin-comparison@example.com",
        display_name="Admin Comparison",
        org_name="Comparison Test Org",
        org_slug="comparison-test-org",
    )
    org_id = org["id"]

    await _seed_assessed_attempt(app, client, org_id, admin_id=admin["id"])

    comparison_response = await client.get(
        "/api/admin/cohorts/comparison",
        headers={"X-User-ID": admin["id"], "X-Organisation-ID": org_id},
        params={"cohort_keys": "Consultant,Engineer"},
    )
    assert comparison_response.status_code == 200
    comparison = comparison_response.json()["data"]
    assert "cohorts" in comparison
    assert "comparison_timestamp" in comparison
    assert isinstance(comparison["cohorts"], list)


@pytest.mark.asyncio
async def test_learner_analytics_with_time_range(app, client, test_settings) -> None:
    _migrate(test_settings)
    admin, org = await _create_org_and_make_admin(
        client,
        email="admin-learner-timerange@example.com",
        display_name="Admin Learner TimeRange",
        org_name="Learner TimeRange Test Org",
        org_slug="learner-timerange-test-org",
    )
    org_id = org["id"]

    learner, _, _, _ = await _seed_assessed_attempt(app, client, org_id, admin_id=admin["id"])

    from datetime import datetime, timezone

    now = datetime.now(timezone.utc)
    from_date = now.replace(year=2020, month=1, day=1)
    to_date = now.replace(year=2030, month=12, day=31)

    analytics_response = await client.get(
        f"/api/admin/learners/{learner['id']}/analytics",
        headers={"X-User-ID": admin["id"], "X-Organisation-ID": org_id},
        params={
            "from_date": from_date.isoformat(),
            "to_date": to_date.isoformat(),
        },
    )
    assert analytics_response.status_code == 200


@pytest.mark.asyncio
async def test_cohort_analytics_with_time_range(app, client, test_settings) -> None:
    _migrate(test_settings)
    admin, org = await _create_org_and_make_admin(
        client,
        email="admin-cohort-timerange@example.com",
        display_name="Admin Cohort TimeRange",
        org_name="Cohort TimeRange Test Org",
        org_slug="cohort-timerange-test-org",
    )
    org_id = org["id"]

    await _seed_assessed_attempt(app, client, org_id, admin_id=admin["id"])

    from datetime import datetime, timezone

    now = datetime.now(timezone.utc)
    from_date = now.replace(year=2020, month=1, day=1)
    to_date = now.replace(year=2030, month=12, day=31)

    analytics_response = await client.get(
        "/api/admin/cohorts/analytics",
        headers={"X-User-ID": admin["id"], "X-Organisation-ID": org_id},
        params={
            "target_role": "Consultant",
            "from_date": from_date.isoformat(),
            "to_date": to_date.isoformat(),
        },
    )
    assert analytics_response.status_code == 200


@pytest.mark.asyncio
async def test_analytics_export_json(app, client, test_settings) -> None:
    _migrate(test_settings)
    admin, org = await _create_org_and_make_admin(
        client,
        email="admin-export@example.com",
        display_name="Admin Export",
        org_name="Export Test Org",
        org_slug="export-test-org",
    )
    org_id = org["id"]

    await _seed_assessed_attempt(app, client, org_id, admin_id=admin["id"])

    export_response = await client.get(
        "/api/admin/analytics/export",
        headers={"X-User-ID": admin["id"], "X-Organisation-ID": org_id},
        params={"format": "json"},
    )
    assert export_response.status_code == 200
    assert export_response.headers["content-type"] == "application/json"


@pytest.mark.asyncio
async def test_analytics_export_csv(app, client, test_settings) -> None:
    _migrate(test_settings)
    admin, org = await _create_org_and_make_admin(
        client,
        email="admin-csv-export@example.com",
        display_name="Admin CSV Export",
        org_name="CSV Export Test Org",
        org_slug="csv-export-test-org",
    )
    org_id = org["id"]

    await _seed_assessed_attempt(app, client, org_id, admin_id=admin["id"])

    export_response = await client.get(
        "/api/admin/analytics/export",
        headers={"X-User-ID": admin["id"], "X-Organisation-ID": org_id},
        params={"format": "csv"},
    )
    assert export_response.status_code == 200
    assert export_response.headers["content-type"] == "text/csv; charset=utf-8"


@pytest.mark.asyncio
async def test_drilldown_to_attempt_from_learner_analytics(app, client, test_settings) -> None:
    _migrate(test_settings)
    admin, org = await _create_org_and_make_admin(
        client,
        email="admin-drilldown@example.com",
        display_name="Admin Drilldown",
        org_name="Drilldown Test Org",
        org_slug="drilldown-test-org",
    )
    org_id = org["id"]

    learner, _collection, _prompt, attempt = await _seed_assessed_attempt(
        app, client, org_id, admin_id=admin["id"]
    )
    attempt_id = attempt["id"]

    learner_analytics_response = await client.get(
        f"/api/admin/learners/{learner['id']}/analytics",
        headers={"X-User-ID": admin["id"], "X-Organisation-ID": org_id},
    )
    assert learner_analytics_response.status_code == 200
    learner_payload = learner_analytics_response.json()["data"]
    assert len(learner_payload["recent_attempts"]) >= 1

    recent_attempt_id = learner_payload["recent_attempts"][0]["attempt_id"]
    assert recent_attempt_id == attempt_id

    audit_response = await client.get(
        f"/api/admin/attempts/{recent_attempt_id}/audit",
        headers={"X-User-ID": admin["id"], "X-Organisation-ID": org_id},
    )
    assert audit_response.status_code == 200
    audit_payload = audit_response.json()["data"]
    assert audit_payload["attempt"]["attempt_id"] == recent_attempt_id
    assert "assessment" in audit_payload
    assert "workflow_events" in audit_payload
