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


@pytest.mark.asyncio
async def test_org_skills_crud(client, test_settings) -> None:
    _migrate(test_settings)
    admin, org = await _create_org_and_make_admin(
        client,
        email="org-skills@example.com",
        display_name="Org Skills Admin",
        org_name="Skills Test Org",
        org_slug="skills-test-org",
    )
    org_id = org["id"]
    headers = {"X-User-ID": admin["id"], "X-Organisation-ID": org_id}

    list_response = await client.get(f"/api/organisations/{org_id}/skills", headers=headers)
    assert list_response.status_code == 200
    assert list_response.json()["data"] == []

    create_response = await client.post(
        f"/api/organisations/{org_id}/skills",
        headers=headers,
        json={
            "slug": "custom-communication",
            "name": "Custom Communication",
            "description": "Org-specific communication skill",
            "category": "interpersonal",
        },
    )
    assert create_response.status_code == 200
    skill = create_response.json()["data"]
    assert skill["slug"] == "custom-communication"
    assert skill["name"] == "Custom Communication"
    assert skill["organisation_id"] == org_id

    get_response = await client.get(
        f"/api/organisations/{org_id}/skills/custom-communication", headers=headers
    )
    assert get_response.status_code == 200
    assert get_response.json()["data"]["slug"] == "custom-communication"

    update_response = await client.patch(
        f"/api/organisations/{org_id}/skills/custom-communication",
        headers=headers,
        json={
            "name": "Updated Custom Communication",
            "description": "Updated description",
        },
    )
    assert update_response.status_code == 200
    assert update_response.json()["data"]["name"] == "Updated Custom Communication"

    delete_response = await client.delete(
        f"/api/organisations/{org_id}/skills/custom-communication", headers=headers
    )
    assert delete_response.status_code == 200

    list_after_delete = await client.get(f"/api/organisations/{org_id}/skills", headers=headers)
    assert list_after_delete.status_code == 200
    assert list_after_delete.json()["data"] == []


@pytest.mark.asyncio
async def test_org_competencies_crud(client, test_settings) -> None:
    _migrate(test_settings)
    admin, org = await _create_org_and_make_admin(
        client,
        email="org-competencies@example.com",
        display_name="Org Competencies Admin",
        org_name="Competencies Test Org",
        org_slug="competencies-test-org",
    )
    org_id = org["id"]
    headers = {"X-User-ID": admin["id"], "X-Organisation-ID": org_id}

    list_response = await client.get(f"/api/organisations/{org_id}/competencies", headers=headers)
    assert list_response.status_code == 200
    assert list_response.json()["data"] == []

    create_response = await client.post(
        f"/api/organisations/{org_id}/competencies",
        headers=headers,
        json={
            "slug": "custom-leadership",
            "name": "Custom Leadership",
            "description": "Org-specific leadership competency",
        },
    )
    assert create_response.status_code == 200
    competency = create_response.json()["data"]
    assert competency["slug"] == "custom-leadership"
    assert competency["name"] == "Custom Leadership"
    assert competency["organisation_id"] == org_id

    get_response = await client.get(
        f"/api/organisations/{org_id}/competencies/custom-leadership", headers=headers
    )
    assert get_response.status_code == 200
    assert get_response.json()["data"]["slug"] == "custom-leadership"

    update_response = await client.patch(
        f"/api/organisations/{org_id}/competencies/custom-leadership",
        headers=headers,
        json={
            "name": "Updated Custom Leadership",
            "description": "Updated description",
        },
    )
    assert update_response.status_code == 200
    assert update_response.json()["data"]["name"] == "Updated Custom Leadership"

    delete_response = await client.delete(
        f"/api/organisations/{org_id}/competencies/custom-leadership", headers=headers
    )
    assert delete_response.status_code == 200

    list_after_delete = await client.get(
        f"/api/organisations/{org_id}/competencies", headers=headers
    )
    assert list_after_delete.status_code == 200
    assert list_after_delete.json()["data"] == []


@pytest.mark.asyncio
async def test_org_rubrics_crud(client, test_settings) -> None:
    _migrate(test_settings)
    admin, org = await _create_org_and_make_admin(
        client,
        email="org-rubrics@example.com",
        display_name="Org Rubrics Admin",
        org_name="Rubrics Test Org",
        org_slug="rubrics-test-org",
    )
    org_id = org["id"]
    headers = {"X-User-ID": admin["id"], "X-Organisation-ID": org_id}

    list_response = await client.get(f"/api/organisations/{org_id}/rubrics", headers=headers)
    assert list_response.status_code == 200
    assert list_response.json()["data"] == []

    create_response = await client.post(
        f"/api/organisations/{org_id}/rubrics",
        headers=headers,
        json={
            "rubric_id": "custom-quick-practice@v1",
            "family": "custom_quick_practice",
            "version": "v1",
            "content_type": "quick_practice_prompt",
            "schema_version": "v1",
            "name": "Custom Quick Practice Rubric",
            "criteria": ["custom-skill"],
        },
    )
    assert create_response.status_code == 200
    rubric = create_response.json()["data"]
    assert rubric["rubric_id"] == "custom-quick-practice@v1"
    assert rubric["name"] == "Custom Quick Practice Rubric"
    assert rubric["organisation_id"] == org_id

    get_response = await client.get(
        f"/api/organisations/{org_id}/rubrics/custom-quick-practice@v1", headers=headers
    )
    assert get_response.status_code == 200
    assert get_response.json()["data"]["rubric_id"] == "custom-quick-practice@v1"

    update_response = await client.patch(
        f"/api/organisations/{org_id}/rubrics/custom-quick-practice@v1",
        headers=headers,
        json={
            "name": "Updated Custom Quick Practice Rubric",
        },
    )
    assert update_response.status_code == 200
    assert update_response.json()["data"]["name"] == "Updated Custom Quick Practice Rubric"

    delete_response = await client.delete(
        f"/api/organisations/{org_id}/rubrics/custom-quick-practice@v1", headers=headers
    )
    assert delete_response.status_code == 200

    list_after_delete = await client.get(f"/api/organisations/{org_id}/rubrics", headers=headers)
    assert list_after_delete.status_code == 200
    assert list_after_delete.json()["data"] == []


@pytest.mark.asyncio
async def test_org_prompt_items_crud(client, test_settings) -> None:
    _migrate(test_settings)
    admin, org = await _create_org_and_make_admin(
        client,
        email="org-prompts@example.com",
        display_name="Org Prompts Admin",
        org_name="Prompts Test Org",
        org_slug="prompts-test-org",
    )
    org_id = org["id"]
    headers = {"X-User-ID": admin["id"], "X-Organisation-ID": org_id}

    list_response = await client.get(f"/api/organisations/{org_id}/prompt-items", headers=headers)
    assert list_response.status_code == 200
    assert list_response.json()["data"] == []

    await client.post("/api/skills/bootstrap-canon", headers={"X-User-ID": admin["id"]})

    create_response = await client.post(
        f"/api/organisations/{org_id}/prompt-items",
        headers=headers,
        json={
            "prompt_type": "quick_practice_prompt",
            "title": "Custom org prompt",
            "prompt_text": "A client asks for an impossible timeline. Respond.",
            "difficulty": "intermediate",
            "target_skill_slugs": [],
            "rubric_id": "quick_practice_text@v1",
        },
    )
    assert create_response.status_code == 200
    prompt_item = create_response.json()["data"]
    assert prompt_item["title"] == "Custom org prompt"
    assert prompt_item["organisation_id"] == org_id
    prompt_item_id = prompt_item["id"]

    get_response = await client.get(
        f"/api/organisations/{org_id}/prompt-items/{prompt_item_id}", headers=headers
    )
    assert get_response.status_code == 200
    assert get_response.json()["data"]["id"] == prompt_item_id

    update_response = await client.patch(
        f"/api/organisations/{org_id}/prompt-items/{prompt_item_id}",
        headers=headers,
        json={
            "title": "Updated custom org prompt",
        },
    )
    assert update_response.status_code == 200
    assert update_response.json()["data"]["title"] == "Updated custom org prompt"

    delete_response = await client.delete(
        f"/api/organisations/{org_id}/prompt-items/{prompt_item_id}", headers=headers
    )
    assert delete_response.status_code == 200

    list_after_delete = await client.get(
        f"/api/organisations/{org_id}/prompt-items", headers=headers
    )
    assert list_after_delete.status_code == 200
    assert list_after_delete.json()["data"] == []


@pytest.mark.asyncio
async def test_org_scenarios_crud(client, test_settings) -> None:
    _migrate(test_settings)
    admin, org = await _create_org_and_make_admin(
        client,
        email="org-scenarios@example.com",
        display_name="Org Scenarios Admin",
        org_name="Scenarios Test Org",
        org_slug="scenarios-test-org",
    )
    org_id = org["id"]
    headers = {"X-User-ID": admin["id"], "X-Organisation-ID": org_id}

    list_response = await client.get(f"/api/organisations/{org_id}/scenarios", headers=headers)
    assert list_response.status_code == 200
    assert list_response.json()["data"] == []

    await client.post("/api/skills/bootstrap-canon", headers={"X-User-ID": admin["id"]})

    create_response = await client.post(
        f"/api/organisations/{org_id}/scenarios",
        headers=headers,
        json={
            "title": "Custom org scenario",
            "business_context": "A product launch is behind schedule.",
            "learner_objective": "Align stakeholders on a realistic next step.",
            "constraints": ["Two-week deadline"],
            "stakeholder_tensions": ["Sales wants speed", "Engineering wants stability"],
            "target_skill_slugs": [],
            "rubric_id": "scenario_text@v1",
            "mock_company": {
                "name": "Custom Corp",
                "industry": "Enterprise SaaS",
                "operating_context": "Scaling quickly.",
            },
            "mock_people": [
                {
                    "name": "Ava",
                    "role": "VP Sales",
                    "goals": ["Close the quarter"],
                    "communication_style": "Direct",
                    "relationship_to_scenario": "Primary stakeholder",
                }
            ],
        },
    )
    assert create_response.status_code == 200
    scenario = create_response.json()["data"]
    assert scenario["title"] == "Custom org scenario"
    assert scenario["organisation_id"] == org_id
    scenario_id = scenario["id"]

    get_response = await client.get(
        f"/api/organisations/{org_id}/scenarios/{scenario_id}", headers=headers
    )
    assert get_response.status_code == 200
    assert get_response.json()["data"]["id"] == scenario_id

    update_response = await client.patch(
        f"/api/organisations/{org_id}/scenarios/{scenario_id}",
        headers=headers,
        json={
            "title": "Updated custom org scenario",
        },
    )
    assert update_response.status_code == 200
    assert update_response.json()["data"]["title"] == "Updated custom org scenario"

    delete_response = await client.delete(
        f"/api/organisations/{org_id}/scenarios/{scenario_id}", headers=headers
    )
    assert delete_response.status_code == 200

    list_after_delete = await client.get(f"/api/organisations/{org_id}/scenarios", headers=headers)
    assert list_after_delete.status_code == 200
    assert list_after_delete.json()["data"] == []


@pytest.mark.asyncio
async def test_org_skill_requires_admin_role(client, test_settings) -> None:
    _migrate(test_settings)
    admin, org = await _create_org_and_make_admin(
        client,
        email="org-admin@example.com",
        display_name="Org Admin",
        org_name="Admin Test Org",
        org_slug="admin-test-org",
    )
    org_id = org["id"]

    learner = await _register_user(
        client,
        email="org-learner@example.com",
        display_name="Org Learner",
    )
    learner_headers = {"X-User-ID": learner["id"], "X-Organisation-ID": org_id}

    create_response = await client.post(
        f"/api/organisations/{org_id}/skills",
        headers=learner_headers,
        json={
            "slug": "unauthorized-skill",
            "name": "Unauthorized Skill",
            "description": "Should fail",
            "category": "interpersonal",
        },
    )
    assert create_response.status_code == 403


@pytest.mark.asyncio
async def test_cannot_create_duplicate_org_skill(client, test_settings) -> None:
    _migrate(test_settings)
    admin, org = await _create_org_and_make_admin(
        client,
        email="org-dup@example.com",
        display_name="Org Dup Admin",
        org_name="Dup Test Org",
        org_slug="dup-test-org",
    )
    org_id = org["id"]
    headers = {"X-User-ID": admin["id"], "X-Organisation-ID": org_id}

    await client.post(
        f"/api/organisations/{org_id}/skills",
        headers=headers,
        json={
            "slug": "duplicate-skill",
            "name": "Duplicate Skill",
            "description": "First one",
            "category": "interpersonal",
        },
    )

    duplicate_response = await client.post(
        f"/api/organisations/{org_id}/skills",
        headers=headers,
        json={
            "slug": "duplicate-skill",
            "name": "Duplicate Skill",
            "description": "Second one should fail",
            "category": "interpersonal",
        },
    )
    assert duplicate_response.status_code == 409


@pytest.mark.asyncio
async def test_cannot_create_duplicate_org_competency(client, test_settings) -> None:
    _migrate(test_settings)
    admin, org = await _create_org_and_make_admin(
        client,
        email="org-comp-dup@example.com",
        display_name="Org Comp Dup Admin",
        org_name="Comp Dup Test Org",
        org_slug="comp-dup-test-org",
    )
    org_id = org["id"]
    headers = {"X-User-ID": admin["id"], "X-Organisation-ID": org_id}

    await client.post(
        f"/api/organisations/{org_id}/competencies",
        headers=headers,
        json={
            "slug": "duplicate-competency",
            "name": "Duplicate Competency",
            "description": "First one",
        },
    )

    duplicate_response = await client.post(
        f"/api/organisations/{org_id}/competencies",
        headers=headers,
        json={
            "slug": "duplicate-competency",
            "name": "Duplicate Competency",
            "description": "Second one should fail",
        },
    )
    assert duplicate_response.status_code == 409


@pytest.mark.asyncio
async def test_org_cannot_access_other_org_skills(client, test_settings) -> None:
    _migrate(test_settings)
    admin1, org1 = await _create_org_and_make_admin(
        client,
        email="org1-admin@example.com",
        display_name="Org1 Admin",
        org_name="Org1",
        org_slug="org-1",
    )
    admin2, org2 = await _create_org_and_make_admin(
        client,
        email="org2-admin@example.com",
        display_name="Org2 Admin",
        org_name="Org2",
        org_slug="org-2",
    )

    await client.post(
        f"/api/organisations/{org1['id']}/skills",
        headers={"X-User-ID": admin1["id"], "X-Organisation-ID": org1["id"]},
        json={
            "slug": "org1-only-skill",
            "name": "Org1 Only Skill",
            "description": "Should not be visible to org2",
            "category": "interpersonal",
        },
    )

    list_org2_response = await client.get(
        f"/api/organisations/{org2['id']}/skills",
        headers={"X-User-ID": admin2["id"], "X-Organisation-ID": org2["id"]},
    )
    assert list_org2_response.status_code == 200
    assert list_org2_response.json()["data"] == []

    get_org2_response = await client.get(
        f"/api/organisations/{org2['id']}/skills/org1-only-skill",
        headers={"X-User-ID": admin2["id"], "X-Organisation-ID": org2["id"]},
    )
    assert get_org2_response.status_code == 404
