from __future__ import annotations

from pathlib import Path

import pytest
from alembic.config import Config

from alembic import command
from soft_skills_backend.persistence.models import WorkflowEventRecord


def _migrate(test_settings) -> None:
    alembic_config = Config(str(Path(__file__).resolve().parents[2] / "alembic.ini"))
    alembic_config.set_main_option("sqlalchemy.url", test_settings.database_url)
    command.upgrade(alembic_config, "head")


async def _register_user(client, *, email: str, display_name: str, role: str = "standard_user"):
    response = await client.post(
        "/api/auth/register",
        json={
            "email": email,
            "display_name": display_name,
            "role": role,
            "target_role": "Consultant",
            "goals": ["Improve stakeholder handling"],
            "practice_preferences": {"session_length": "short"},
        },
    )
    assert response.status_code == 200
    return response.json()["data"]


@pytest.mark.asyncio
async def test_identity_bootstrap_and_private_draft_authoring(app, client, test_settings) -> None:
    _migrate(test_settings)

    admin = await _register_user(
        client,
        email="admin@example.com",
        display_name="Admin",
        role="admin",
    )
    bootstrap_response = await client.post(
        "/api/skills/bootstrap-canon",
        headers={"X-User-ID": admin["id"]},
    )
    assert bootstrap_response.status_code == 200
    snapshot = bootstrap_response.json()["data"]
    assert len(snapshot["skills"]) == 10
    assert len(snapshot["competencies"]) == 8
    assert len(snapshot["rubrics"]) == 3

    learner = await _register_user(
        client,
        email="learner@example.com",
        display_name="Learner",
    )

    me_response = await client.get("/api/users/me", headers={"X-User-ID": learner["id"]})
    assert me_response.status_code == 200
    assert me_response.json()["data"]["profile"]["target_role"] == "Consultant"

    profile_update_response = await client.patch(
        "/api/users/me/profile",
        headers={"X-User-ID": learner["id"]},
        json={"goals": ["Improve prioritization"], "practice_preferences": {"mode": "scenario"}},
    )
    assert profile_update_response.status_code == 200
    assert profile_update_response.json()["data"]["profile"]["goals"] == ["Improve prioritization"]

    collection_response = await client.post(
        "/api/collections",
        headers={"X-User-ID": learner["id"]},
        json={
            "title": "Stakeholder Pressure Pack",
            "summary": "Draft collection for stakeholder practice.",
            "target_audience": "Early-career consultants",
            "difficulty": "intermediate",
            "content_format_mix": ["quick_practice_prompt", "scenario_step"],
            "target_skill_slugs": ["active-listening", "expectation-setting"],
            "target_competency_slugs": ["stakeholder-management"],
            "rubric_ids": ["quick_practice_text@v1", "scenario_text@v1"],
        },
    )
    assert collection_response.status_code == 200
    collection = collection_response.json()["data"]

    prompt_response = await client.post(
        f"/api/collections/{collection['id']}/prompt-items",
        headers={"X-User-ID": learner["id"]},
        json={
            "prompt_type": "quick_practice_prompt",
            "title": "Reset expectations",
            "prompt_text": "A client asks for an impossible deadline. Respond.",
            "difficulty": "intermediate",
            "target_skill_slugs": ["active-listening"],
            "rubric_id": "quick_practice_text@v1",
        },
    )
    assert prompt_response.status_code == 200

    scenario_response = await client.post(
        f"/api/collections/{collection['id']}/scenarios",
        headers={"X-User-ID": learner["id"]},
        json={
            "title": "Conflicting stakeholder asks",
            "business_context": "A product launch is behind schedule.",
            "learner_objective": "Align stakeholders on a realistic next step.",
            "constraints": ["Two-week deadline", "Limited engineering capacity"],
            "stakeholder_tensions": ["Sales wants speed", "Engineering wants stability"],
            "target_skill_slugs": ["expectation-setting"],
            "rubric_id": "scenario_text@v1",
            "mock_company": {
                "name": "Northstar Systems",
                "industry": "Enterprise SaaS",
                "operating_context": "Scaling quickly after new funding.",
            },
            "mock_people": [
                {
                    "name": "Ava",
                    "role": "VP Sales",
                    "goals": ["Close the quarter strongly"],
                    "communication_style": "Direct and urgent",
                    "relationship_to_scenario": "Primary stakeholder pushing for speed",
                }
            ],
        },
    )
    assert scenario_response.status_code == 200

    publish_response = await client.patch(
        f"/api/collections/{collection['id']}/lifecycle",
        headers={"X-User-ID": learner["id"]},
        json={"lifecycle_state": "published_private"},
    )
    assert publish_response.status_code == 200
    assert publish_response.json()["data"]["lifecycle_state"] == "published_private"

    list_response = await client.get(
        "/api/collections",
        headers={"X-User-ID": learner["id"]},
        params={"skill_slug": "active-listening"},
    )
    assert list_response.status_code == 200
    assert len(list_response.json()["data"]) == 1

    with app.state.container.session_factory() as session:
        event_types = {
            record.event_type for record in session.query(WorkflowEventRecord).all()
        }
    assert "identity.user_registered.v1" in event_types
    assert "taxonomy.catalog_seeded.v1" in event_types
    assert "catalog.collection.created.v1" in event_types
    assert "catalog.prompt_item.created.v1" in event_types
    assert "catalog.scenario.created.v1" in event_types


@pytest.mark.asyncio
async def test_catalog_rejects_invalid_mappings_and_requires_auth(client, test_settings) -> None:
    _migrate(test_settings)
    admin = await _register_user(client, email="admin2@example.com", display_name="Admin", role="admin")
    await client.post("/api/skills/bootstrap-canon", headers={"X-User-ID": admin["id"]})
    learner = await _register_user(client, email="learner2@example.com", display_name="Learner")

    unauthenticated_response = await client.post(
        "/api/collections",
        json={
            "title": "Unauthenticated",
            "summary": "Should fail",
            "target_audience": "Anyone",
            "difficulty": "intermediate",
            "content_format_mix": ["quick_practice_prompt"],
            "target_skill_slugs": ["active-listening"],
            "target_competency_slugs": ["stakeholder-management"],
            "rubric_ids": ["quick_practice_text@v1"],
        },
    )
    assert unauthenticated_response.status_code == 401

    invalid_mapping_response = await client.post(
        "/api/collections",
        headers={"X-User-ID": learner["id"]},
        json={
            "title": "Invalid mapping",
            "summary": "Should fail",
            "target_audience": "Anyone",
            "difficulty": "intermediate",
            "content_format_mix": ["quick_practice_prompt"],
            "target_skill_slugs": ["active-listening"],
            "target_competency_slugs": ["prioritization"],
            "rubric_ids": ["quick_practice_text@v1"],
        },
    )
    assert invalid_mapping_response.status_code == 422
    assert invalid_mapping_response.json()["error"]["code"] == "SS-VALIDATION-016"
