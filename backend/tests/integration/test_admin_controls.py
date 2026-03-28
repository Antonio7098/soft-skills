from __future__ import annotations

from pathlib import Path

import pytest
from alembic.config import Config

from alembic import command
from soft_skills_backend.modules.practice.domain.practice import AssessmentDraft
from soft_skills_backend.modules.practice.workflows.assessment import AssessmentTransformPayload
from soft_skills_backend.platform.db.models import (
    CollectionVerificationReviewRecord,
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


class FakeSuccessMarker:
    provider_name = "openai"
    model_slug = "gpt-4.1-mini"

    async def mark_attempt(self, *, prompt_payload, learner_payload, call_context):
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
                            "rationale": "It set a realistic next step and boundary.",
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


async def _seed_public_collection(client, org_id: str, admin_id: str | None = None):
    learner = await _register_user(
        client,
        email="learner-controls@example.com",
        display_name="Learner Controls",
    )
    print(f"Learner created: {learner['id']}")
    bootstrap_resp = await client.post(
        "/api/skills/bootstrap-canon", headers={"X-User-ID": learner["id"]}
    )
    print(f"Bootstrap: {bootstrap_resp.status_code}")

    # Add learner to org as member (only admins can add members)
    if admin_id is None:
        # Fallback: assume the learner is already an admin (for backwards compatibility)
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
            "title": "Admin Review Pack",
            "summary": "Collection used to test admin review flows.",
            "target_audience": "Consultant",
            "difficulty": "intermediate",
            "content_format_mix": ["quick_practice_prompt"],
            "target_skill_slugs": ["active-listening", "expectation-setting"],
            "target_competency_slugs": ["stakeholder-management"],
            "rubric_ids": ["quick_practice_reset_timeline@v1"],
            "organisation_id": org_id,
        },
    )
    if collection_response.status_code != 200:
        print(f"Collection error: {collection_response.status_code} {collection_response.json()}")
    assert collection_response.status_code == 200, (
        f"Collection creation failed: {collection_response.json()}"
    )
    collection_id = collection_response.json()["data"]["id"]
    print(f"Collection created: {collection_id}")
    prompt_response = await client.post(
        f"/api/collections/{collection_id}/prompt-items",
        headers={"X-User-ID": learner["id"], "X-Organisation-ID": org_id},
        json={
            "prompt_type": "quick_practice_prompt",
            "title": "Reset expectations",
            "prompt_text": "A client asks for an impossible timeline. Respond.",
            "difficulty": "intermediate",
            "target_skill_slugs": [],
            "rubric_id": "quick_practice_reset_timeline@v1",
        },
    )
    assert prompt_response.status_code == 200, prompt_response.json()
    publish_response = await client.patch(
        f"/api/collections/{collection_id}/lifecycle",
        headers={"X-User-ID": learner["id"], "X-Organisation-ID": org_id},
        json={"lifecycle_state": "published_public"},
    )
    if publish_response.status_code != 200:
        print(f"Publish error: {publish_response.status_code} {publish_response.json()}")
    assert publish_response.status_code == 200
    return learner, collection_response.json()["data"], prompt_response.json()["data"]


async def _seed_assessed_attempt(app, client, org_id: str, admin_id: str | None = None):
    learner, collection, prompt = await _seed_public_collection(client, org_id, admin_id=admin_id)
    app.state.container.practice_service._assessment_marker = FakeSuccessMarker()
    start_response = await client.post(
        "/api/attempts/quick-practice/sessions",
        headers={"X-User-ID": learner["id"]},
        json={"prompt_item_id": prompt["id"]},
    )
    assert start_response.status_code == 200, start_response.json()
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
    assert submit_response.status_code == 200, submit_response.json()
    return learner, collection, prompt, submit_response.json()["data"]


@pytest.mark.asyncio
async def test_admin_verification_workflow_persists_history(app, client, test_settings) -> None:
    _migrate(test_settings)
    admin, org = await _create_org_and_make_admin(
        client,
        email="admin-controls@example.com",
        display_name="Admin Controls",
        org_name="Test Org",
        org_slug="test-org",
    )
    org_id = org["id"]

    _, collection, _prompt = await _seed_public_collection(client, org_id, admin_id=admin["id"])

    queue_response = await client.get(
        "/api/admin/collections/verification-queue",
        headers={"X-User-ID": admin["id"], "X-Organisation-ID": org_id},
    )
    assert queue_response.status_code == 200
    assert [item["collection_id"] for item in queue_response.json()["data"]] == [collection["id"]]

    verify_response = await client.post(
        f"/api/admin/collections/{collection['id']}/verification",
        headers={"X-User-ID": admin["id"], "X-Organisation-ID": org_id},
        json={"verification_state": "verified", "note": "Strong structure and mapping quality."},
    )
    assert verify_response.status_code == 200
    payload = verify_response.json()["data"]
    assert payload["collection"]["discovery_tier"] == "org_public"
    assert payload["latest_review"]["next_verification_state"] == "verified"

    with app.state.container.session_factory() as session:
        review_record = (
            session.query(CollectionVerificationReviewRecord)
            .filter(CollectionVerificationReviewRecord.collection_id == collection["id"])
            .one_or_none()
        )
        event_types = {record.event_type for record in session.query(WorkflowEventRecord).all()}

    assert review_record is not None
    assert review_record.note == "Strong structure and mapping quality."
    assert "catalog.collection.verification_changed.v1" in event_types


@pytest.mark.asyncio
async def test_admin_prompt_registry_seeds_builtins_and_supports_crud(
    app, client, test_settings
) -> None:
    del app
    _migrate(test_settings)
    admin, org = await _create_org_and_make_admin(
        client,
        email="admin-prompts@example.com",
        display_name="Admin Prompts",
        org_name="Prompt Admin Org",
        org_slug="prompt-admin-org",
    )
    headers = {"X-User-ID": admin["id"], "X-Organisation-ID": org["id"]}

    list_response = await client.get("/api/admin/prompts", headers=headers)
    assert list_response.status_code == 200
    prompt_names = {item["name"] for item in list_response.json()["data"]}
    assert "assistant_orchestrator" in prompt_names
    assert "creator-collection-structured-blueprint" in prompt_names

    create_response = await client.post(
        "/api/admin/prompts",
        headers=headers,
        json={
            "name": "admin-test-prompt",
            "version": "v1",
            "prompt_type": "generation",
            "template": "Write about {topic} for {audience}.",
            "variables_schema": {
                "type": "object",
                "properties": {
                    "topic": {"type": "string"},
                    "audience": {"type": "string"},
                },
                "required": ["topic", "audience"],
            },
        },
    )
    assert create_response.status_code == 200
    created = create_response.json()["data"]
    assert created["status"] == "draft"

    publish_response = await client.post(
        "/api/admin/prompts/admin-test-prompt/versions/v1/publish",
        headers=headers,
        json={},
    )
    assert publish_response.status_code == 200
    assert publish_response.json()["data"]["status"] == "published"

    version_response = await client.get(
        "/api/admin/prompts/admin-test-prompt/versions/v1",
        headers=headers,
    )
    assert version_response.status_code == 200
    assert version_response.json()["data"]["name"] == "admin-test-prompt"

    analytics_response = await client.get(
        "/api/admin/prompts/admin-test-prompt/versions/v1/analytics",
        headers=headers,
    )
    assert analytics_response.status_code == 200
    analytics = analytics_response.json()["data"]
    assert analytics["render_count"] == 0
    assert analytics["failure_count"] == 0


@pytest.mark.asyncio
async def test_admin_analytics_and_audit_are_redacted_and_admin_only(
    app, client, test_settings
) -> None:
    _migrate(test_settings)
    admin, org = await _create_org_and_make_admin(
        client,
        email="admin-controls@example.com",
        display_name="Admin Controls",
        org_name="Test Org Analytics",
        org_slug="test-org-analytics",
    )
    org_id = org["id"]

    learner, _collection, prompt, attempt = await _seed_assessed_attempt(
        app, client, org_id, admin_id=admin["id"]
    )
    attempt_id = attempt["id"]
    own_attempt_response = await client.get(
        f"/api/attempts/{attempt_id}",
        headers={"X-User-ID": learner["id"]},
    )
    assert own_attempt_response.status_code == 200
    assert own_attempt_response.json()["data"]["response_text"]

    forbidden_attempt_response = await client.get(
        f"/api/attempts/{attempt_id}",
        headers={"X-User-ID": admin["id"]},
    )
    assert forbidden_attempt_response.status_code == 403
    assert forbidden_attempt_response.json()["error"]["code"] == "SS-AUTH-011"

    forbidden_submit_response = await client.post(
        f"/api/attempts/{attempt_id}/submit",
        headers={"X-User-ID": admin["id"]},
        json={"response_text": "Admin should not be able to submit this."},
    )
    assert forbidden_submit_response.status_code == 403
    assert forbidden_submit_response.json()["error"]["code"] == "SS-AUTH-012"

    learner_analytics_response = await client.get(
        f"/api/admin/learners/{learner['id']}/analytics",
        headers={"X-User-ID": admin["id"], "X-Organisation-ID": org_id},
    )
    assert learner_analytics_response.status_code == 200
    learner_payload = learner_analytics_response.json()["data"]
    assert learner_payload["usage"]["total_attempts"] >= 1
    assert learner_payload["recent_attempts"][0]["attempt_id"] == attempt_id

    cohort_analytics_response = await client.get(
        "/api/admin/cohorts/analytics",
        headers={"X-User-ID": admin["id"], "X-Organisation-ID": org_id},
        params={"target_role": "Consultant"},
    )
    assert cohort_analytics_response.status_code == 200
    assert cohort_analytics_response.json()["data"]["learner_count"] >= 1

    audit_response = await client.get(
        f"/api/admin/attempts/{attempt_id}/audit",
        headers={"X-User-ID": admin["id"], "X-Organisation-ID": org_id},
    )
    assert audit_response.status_code == 200
    audit_payload = audit_response.json()["data"]
    assert audit_payload["response_visibility"] == "redacted_without_relationship_mapping"
    assert audit_payload["attempt"]["attempt_id"] == attempt_id
    assert "response_text" not in audit_payload["attempt"]
    assert audit_payload["prompt"]["title"] == prompt["title"]
    assert audit_payload["assessment"]["pipeline_run_id"]
    assert audit_payload["workflow_events"]
    assert audit_payload["pipeline_runs"]

    relationship_response = await client.put(
        f"/api/admin/learners/{learner['id']}/relationship",
        headers={"X-User-ID": admin["id"], "X-Organisation-ID": org_id},
        json={"relationship_type": "manager"},
    )
    assert relationship_response.status_code == 200
    assert relationship_response.json()["data"]["relationship_type"] == "manager"

    full_audit_response = await client.get(
        f"/api/admin/attempts/{attempt_id}/audit",
        headers={"X-User-ID": admin["id"], "X-Organisation-ID": org_id},
    )
    assert full_audit_response.status_code == 200
    full_audit_payload = full_audit_response.json()["data"]
    assert full_audit_payload["response_visibility"] == "full_via_manager_relationship"
    assert full_audit_payload["access_relationship"]["relationship_type"] == "manager"
    assert full_audit_payload["response_text"]
    assert full_audit_payload["assessment"]["evidence_quotes"]

    delete_relationship_response = await client.delete(
        f"/api/admin/learners/{learner['id']}/relationship",
        headers={"X-User-ID": admin["id"], "X-Organisation-ID": org_id},
    )
    assert delete_relationship_response.status_code == 200
