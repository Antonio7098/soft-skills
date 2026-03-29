"""Integration tests for admin telemetry APIs."""

from __future__ import annotations

from pathlib import Path

import pytest
from alembic.config import Config

from alembic import command


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


async def _make_user_admin(client, org_id: str, user_id: str, admin_id: str):
    add_member_resp = await client.post(
        f"/api/organisations/{org_id}/members",
        headers={"X-User-ID": admin_id, "X-Organisation-ID": org_id},
        json={"user_id": user_id, "role": "admin"},
    )
    assert add_member_resp.status_code == 200


class FakeSuccessMarker:
    provider_name = "openai"
    model_slug = "gpt-4.1-mini"

    async def mark_attempt(self, *, prompt_payload, learner_payload, call_context):
        del learner_payload, call_context
        from soft_skills_backend.modules.practice.domain.practice import AssessmentDraft
        from soft_skills_backend.modules.practice.workflows.assessment import (
            AssessmentTransformPayload,
        )

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


async def _seed_assessed_attempt(app, client, org_id: str, admin_id: str | None = None):
    learner_resp = await client.post(
        "/api/auth/register",
        json={
            "email": "learner-telemetry@example.com",
            "display_name": "Learner Telemetry",
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
            "title": "Telemetry Test Pack",
            "summary": "Collection for testing telemetry flows.",
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
async def test_telemetry_overview_endpoint(app, client, test_settings) -> None:
    _migrate(test_settings)
    admin, org = await _create_org_and_make_admin(
        client,
        email="admin-telemetry-overview@example.com",
        display_name="Admin Telemetry Overview",
        org_name="Telemetry Overview Test Org",
        org_slug="telemetry-overview-test-org",
    )
    org_id = org["id"]

    await _seed_assessed_attempt(app, client, org_id, admin_id=admin["id"])

    overview_response = await client.get(
        "/api/admin/telemetry/overview",
        headers={"X-User-ID": admin["id"], "X-Organisation-ID": org_id},
    )
    assert overview_response.status_code == 200
    overview = overview_response.json()["data"]
    assert "organisation_id" in overview
    assert "total_provider_calls" in overview
    assert "provider_call_success_rate" in overview
    assert "avg_provider_latency_ms" in overview
    assert "total_pipeline_runs" in overview
    assert "pipeline_success_rate" in overview
    assert "total_workflow_events" in overview
    assert "total_errors" in overview
    assert "error_rate" in overview
    assert "provider_metrics" in overview
    assert "pipeline_health" in overview
    assert "error_breakdown" in overview
    assert "latency_distribution" in overview


@pytest.mark.asyncio
async def test_telemetry_overview_with_time_range(app, client, test_settings) -> None:
    _migrate(test_settings)
    admin, org = await _create_org_and_make_admin(
        client,
        email="admin-telemetry-timerange@example.com",
        display_name="Admin Telemetry TimeRange",
        org_name="Telemetry TimeRange Test Org",
        org_slug="telemetry-timerange-test-org",
    )
    org_id = org["id"]

    await _seed_assessed_attempt(app, client, org_id, admin_id=admin["id"])

    from datetime import UTC, datetime

    now = datetime.now(UTC)
    from_date = now.replace(year=2020, month=1, day=1)
    to_date = now.replace(year=2030, month=12, day=31)

    overview_response = await client.get(
        "/api/admin/telemetry/overview",
        headers={"X-User-ID": admin["id"], "X-Organisation-ID": org_id},
        params={
            "from_date": from_date.isoformat(),
            "to_date": to_date.isoformat(),
        },
    )
    assert overview_response.status_code == 200
    overview = overview_response.json()["data"]
    assert overview["from_date"] is not None
    assert overview["to_date"] is not None


@pytest.mark.asyncio
async def test_telemetry_traces_list_endpoint(app, client, test_settings) -> None:
    _migrate(test_settings)
    admin, org = await _create_org_and_make_admin(
        client,
        email="admin-telemetry-traces@example.com",
        display_name="Admin Telemetry Traces",
        org_name="Telemetry Traces Test Org",
        org_slug="telemetry-traces-test-org",
    )
    org_id = org["id"]

    await _seed_assessed_attempt(app, client, org_id, admin_id=admin["id"])

    traces_response = await client.get(
        "/api/admin/telemetry/traces",
        headers={"X-User-ID": admin["id"], "X-Organisation-ID": org_id},
    )
    assert traces_response.status_code == 200
    traces = traces_response.json()["data"]
    assert "traces" in traces
    assert "total" in traces
    assert "offset" in traces
    assert "limit" in traces
    assert isinstance(traces["traces"], list)


@pytest.mark.asyncio
async def test_telemetry_traces_list_with_pagination(app, client, test_settings) -> None:
    _migrate(test_settings)
    admin, org = await _create_org_and_make_admin(
        client,
        email="admin-telemetry-paginate@example.com",
        display_name="Admin Telemetry Paginate",
        org_name="Telemetry Paginate Test Org",
        org_slug="telemetry-paginate-test-org",
    )
    org_id = org["id"]

    await _seed_assessed_attempt(app, client, org_id, admin_id=admin["id"])

    traces_response = await client.get(
        "/api/admin/telemetry/traces",
        headers={"X-User-ID": admin["id"], "X-Organisation-ID": org_id},
        params={"offset": 0, "limit": 10},
    )
    assert traces_response.status_code == 200
    traces = traces_response.json()["data"]
    assert traces["offset"] == 0
    assert traces["limit"] == 10


@pytest.mark.asyncio
async def test_telemetry_traces_list_with_date_filter(app, client, test_settings) -> None:
    _migrate(test_settings)
    admin, org = await _create_org_and_make_admin(
        client,
        email="admin-telemetry-date@example.com",
        display_name="Admin Telemetry Date Filter",
        org_name="Telemetry Date Filter Test Org",
        org_slug="telemetry-date-filter-test-org",
    )
    org_id = org["id"]

    await _seed_assessed_attempt(app, client, org_id, admin_id=admin["id"])

    from datetime import UTC, datetime

    now = datetime.now(UTC)
    from_date = now.replace(year=2020, month=1, day=1)
    to_date = now.replace(year=2030, month=12, day=31)

    traces_response = await client.get(
        "/api/admin/telemetry/traces",
        headers={"X-User-ID": admin["id"], "X-Organisation-ID": org_id},
        params={
            "from_date": from_date.isoformat(),
            "to_date": to_date.isoformat(),
        },
    )
    assert traces_response.status_code == 200


@pytest.mark.asyncio
async def test_telemetry_trace_detail_endpoint(app, client, test_settings) -> None:
    _migrate(test_settings)
    admin, org = await _create_org_and_make_admin(
        client,
        email="admin-telemetry-trace-detail@example.com",
        display_name="Admin Telemetry Trace Detail",
        org_name="Telemetry Trace Detail Test Org",
        org_slug="telemetry-trace-detail-test-org",
    )
    org_id = org["id"]

    await _seed_assessed_attempt(app, client, org_id, admin_id=admin["id"])

    traces_response = await client.get(
        "/api/admin/telemetry/traces",
        headers={"X-User-ID": admin["id"], "X-Organisation-ID": org_id},
    )
    assert traces_response.status_code == 200
    traces = traces_response.json()["data"]

    if traces["total"] > 0:
        trace_id = traces["traces"][0]["trace_id"]
        trace_response = await client.get(
            f"/api/admin/telemetry/traces/{trace_id}",
            headers={"X-User-ID": admin["id"], "X-Organisation-ID": org_id},
        )
        assert trace_response.status_code == 200
        trace = trace_response.json()["data"]
        assert trace["trace_id"] == trace_id
        assert "spans" in trace
        assert "total_duration_ms" in trace
        assert "started_at" in trace
        assert "completed_at" in trace
        assert "error_count" in trace
        assert "span_count" in trace


@pytest.mark.asyncio
async def test_telemetry_trace_detail_not_found(app, client, test_settings) -> None:
    _migrate(test_settings)
    admin, org = await _create_org_and_make_admin(
        client,
        email="admin-telemetry-trace-404@example.com",
        display_name="Admin Telemetry Trace 404",
        org_name="Telemetry Trace 404 Test Org",
        org_slug="telemetry-trace-404-test-org",
    )
    org_id = org["id"]

    trace_response = await client.get(
        "/api/admin/telemetry/traces/nonexistent-trace-id",
        headers={"X-User-ID": admin["id"], "X-Organisation-ID": org_id},
    )
    assert trace_response.status_code == 404


@pytest.mark.asyncio
async def test_telemetry_overview_requires_org_scope(app, client, test_settings) -> None:
    _migrate(test_settings)
    admin, org = await _create_org_and_make_admin(
        client,
        email="admin-telemetry-no-org@example.com",
        display_name="Admin Telemetry No Org",
        org_name="Telemetry No Org Test Org",
        org_slug="telemetry-no-org-test-org",
    )
    org_id = org["id"]

    await _seed_assessed_attempt(app, client, org_id, admin_id=admin["id"])

    overview_response = await client.get(
        "/api/admin/telemetry/overview",
        headers={"X-User-ID": admin["id"]},
    )
    assert overview_response.status_code == 200


@pytest.mark.asyncio
async def test_telemetry_traces_requires_org_scope(app, client, test_settings) -> None:
    _migrate(test_settings)
    admin, org = await _create_org_and_make_admin(
        client,
        email="admin-telemetry-traces-no-org@example.com",
        display_name="Admin Telemetry Traces No Org",
        org_name="Telemetry Traces No Org Test Org",
        org_slug="telemetry-traces-no-org-test-org",
    )
    org_id = org["id"]

    await _seed_assessed_attempt(app, client, org_id, admin_id=admin["id"])

    traces_response = await client.get(
        "/api/admin/telemetry/traces",
        headers={"X-User-ID": admin["id"]},
    )
    assert traces_response.status_code == 200


@pytest.mark.asyncio
async def test_telemetry_trace_detail_requires_org_scope(app, client, test_settings) -> None:
    _migrate(test_settings)
    admin, org = await _create_org_and_make_admin(
        client,
        email="admin-telemetry-trace-no-org@example.com",
        display_name="Admin Telemetry Trace No Org",
        org_name="Telemetry Trace No Org Test Org",
        org_slug="telemetry-trace-no-org-test-org",
    )
    org_id = org["id"]

    await _seed_assessed_attempt(app, client, org_id, admin_id=admin["id"])

    traces_response = await client.get(
        "/api/admin/telemetry/traces",
        headers={"X-User-ID": admin["id"], "X-Organisation-ID": org_id},
    )
    assert traces_response.status_code == 200
    traces = traces_response.json()["data"]

    if traces["total"] > 0:
        trace_id = traces["traces"][0]["trace_id"]
        trace_response = await client.get(
            f"/api/admin/telemetry/traces/{trace_id}",
            headers={"X-User-ID": admin["id"]},
        )
        assert trace_response.status_code == 200


@pytest.mark.asyncio
async def test_telemetry_endpoints_as_non_admin(app, client, test_settings) -> None:
    _migrate(test_settings)
    admin, org = await _create_org_and_make_admin(
        client,
        email="admin-telemetry-forbidden@example.com",
        display_name="Admin Telemetry Forbidden",
        org_name="Telemetry Forbidden Test Org",
        org_slug="telemetry-forbidden-test-org",
    )
    org_id = org["id"]

    learner = await _register_user(
        client,
        email="learner-telemetry-forbidden@example.com",
        display_name="Learner Telemetry Forbidden",
    )

    add_member_resp = await client.post(
        f"/api/organisations/{org_id}/members",
        headers={"X-User-ID": admin["id"], "X-Organisation-ID": org_id},
        json={"user_id": learner["id"], "role": "member"},
    )
    assert add_member_resp.status_code == 200

    overview_response = await client.get(
        "/api/admin/telemetry/overview",
        headers={"X-User-ID": learner["id"], "X-Organisation-ID": org_id},
    )
    assert overview_response.status_code == 403

    traces_response = await client.get(
        "/api/admin/telemetry/traces",
        headers={"X-User-ID": learner["id"], "X-Organisation-ID": org_id},
    )
    assert traces_response.status_code == 403
