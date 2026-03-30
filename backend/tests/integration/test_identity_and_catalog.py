from __future__ import annotations

import json
from pathlib import Path

import pytest
from alembic.config import Config

from alembic import command
from soft_skills_backend.engines.config import load_catalog_generation_runtime_config
from soft_skills_backend.platform.db.models import (
    CollectionRecord,
    CollectionSaveRecord,
    ContentGenerationArtifactRecord,
    PipelineRunRecord,
    PromptItemRecord,
    RubricCriterionRecord,
    WorkflowEventRecord,
)
from soft_skills_backend.shared.ports.models import ProviderCompletion


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


class _FakeCatalogLLMProvider:
    def __init__(self, payloads: list[dict[str, object]]) -> None:
        self.provider_name = "test-provider"
        self.model_slug = "test-model"
        self._payloads = payloads

    async def complete_json(
        self,
        *,
        messages,
        call_context,
        response_schema=None,
        timeout_seconds=None,
    ) -> ProviderCompletion:
        del response_schema, timeout_seconds
        assert messages
        assert call_context.operation in {
            "catalog_structured_blueprint_generation",
            "catalog_chat_blueprint_generation",
            "catalog_prompt_item_worker_generation",
            "catalog_scenario_worker_generation",
            "catalog_prompt_item_structured_planning",
            "catalog_prompt_item_chat_planning",
        }
        payload = self._payloads.pop(0)
        return ProviderCompletion(
            content=json.loads(json.dumps(payload)),
            model_slug=self.model_slug,
            usage={"total_tokens": 42},
            raw_response={"provider": self.provider_name},
        )


@pytest.mark.asyncio
async def test_identity_bootstrap_and_private_draft_authoring(app, client, test_settings) -> None:
    _migrate(test_settings)

    admin = await _register_user(
        client,
        email="admin@example.com",
        display_name="Admin",
    )
    bootstrap_response = await client.post(
        "/api/skills/bootstrap-canon",
        headers={"X-User-ID": admin["id"]},
    )
    assert bootstrap_response.status_code == 200
    snapshot = bootstrap_response.json()["data"]
    assert len(snapshot["skills"]) == 10
    assert len(snapshot["competencies"]) == 8
    assert len(snapshot["rubrics"]) == 4

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
            "target_skill_slugs": [],
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
        pipeline_run_names = {
            record.pipeline_name for record in session.query(PipelineRunRecord).all()
        }
        event_types = {record.event_type for record in session.query(WorkflowEventRecord).all()}
    assert "catalog_collection_create" in pipeline_run_names
    assert "catalog_prompt_item_create" in pipeline_run_names
    assert "catalog_scenario_create" in pipeline_run_names
    assert "catalog_collection_lifecycle_update" in pipeline_run_names
    assert "identity.user_registered.v1" in event_types
    assert "taxonomy.catalog_seeded.v1" in event_types
    assert "catalog.collection.created.v1" in event_types
    assert "catalog.prompt_item.created.v1" in event_types
    assert "catalog.scenario.created.v1" in event_types


@pytest.mark.asyncio
async def test_catalog_rejects_invalid_mappings_and_requires_auth(client, test_settings) -> None:
    _migrate(test_settings)
    admin = await _register_user(client, email="admin2@example.com", display_name="Admin")
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


@pytest.mark.asyncio
async def test_catalog_create_collection_is_idempotent_per_request_id(
    app, client, test_settings
) -> None:
    _migrate(test_settings)
    admin = await _register_user(client, email="admin3@example.com", display_name="Admin")
    await client.post("/api/skills/bootstrap-canon", headers={"X-User-ID": admin["id"]})
    learner = await _register_user(client, email="learner3@example.com", display_name="Learner")

    headers = {
        "X-User-ID": learner["id"],
        "X-Request-ID": "catalog-create-fixed-request",
    }
    payload = {
        "title": "Idempotent Collection",
        "summary": "Should only persist once",
        "target_audience": "Anyone",
        "difficulty": "intermediate",
        "content_format_mix": ["quick_practice_prompt"],
        "target_skill_slugs": ["active-listening"],
        "target_competency_slugs": ["stakeholder-management"],
        "rubric_ids": ["quick_practice_text@v1"],
    }

    first_response = await client.post("/api/collections", headers=headers, json=payload)
    second_response = await client.post("/api/collections", headers=headers, json=payload)

    assert first_response.status_code == 200
    assert second_response.status_code == 200
    assert first_response.json()["data"]["id"] == second_response.json()["data"]["id"]

    with app.state.container.session_factory() as session:
        pipeline_runs = (
            session.query(PipelineRunRecord)
            .filter(PipelineRunRecord.pipeline_name == "catalog_collection_create")
            .count()
        )
        collection_events = (
            session.query(WorkflowEventRecord)
            .filter(WorkflowEventRecord.event_type == "catalog.collection.created.v1")
            .count()
        )
        collections = session.query(CollectionRecord).all()

    assert pipeline_runs == 2
    assert collection_events == 1
    assert len(collections) == 1


@pytest.mark.asyncio
async def test_catalog_supports_updates_save_reuse_and_verified_discovery(
    app, client, test_settings
) -> None:
    _migrate(test_settings)
    admin = await _register_user(client, email="admin4@example.com", display_name="Admin")
    await client.post("/api/skills/bootstrap-canon", headers={"X-User-ID": admin["id"]})
    author = await _register_user(client, email="author@example.com", display_name="Author")
    saver = await _register_user(client, email="saver@example.com", display_name="Saver")

    collection_response = await client.post(
        "/api/collections",
        headers={"X-User-ID": author["id"]},
        json={
            "title": "Creator Flow Draft",
            "summary": "Initial draft.",
            "target_audience": "Consultants",
            "difficulty": "intermediate",
            "content_format_mix": ["quick_practice_prompt", "scenario_step"],
            "target_skill_slugs": ["active-listening", "expectation-setting"],
            "target_competency_slugs": ["stakeholder-management"],
            "rubric_ids": ["quick_practice_text@v1", "scenario_text@v1"],
        },
    )
    assert collection_response.status_code == 200
    collection_id = collection_response.json()["data"]["id"]

    prompt_response = await client.post(
        f"/api/collections/{collection_id}/prompt-items",
        headers={"X-User-ID": author["id"]},
        json={
            "prompt_type": "quick_practice_prompt",
            "title": "Initial prompt",
            "prompt_text": "A client pushes for speed over realism. Respond.",
            "difficulty": "intermediate",
            "target_skill_slugs": [],
            "rubric_id": "quick_practice_text@v1",
        },
    )
    assert prompt_response.status_code == 200
    prompt_id = prompt_response.json()["data"]["id"]

    scenario_response = await client.post(
        f"/api/collections/{collection_id}/scenarios",
        headers={"X-User-ID": author["id"]},
        json={
            "title": "Initial scenario",
            "business_context": "A sponsor wants to ship before legal is ready.",
            "learner_objective": "Reset expectations without losing trust.",
            "constraints": ["Board review tomorrow"],
            "stakeholder_tensions": ["Sales wants speed", "Legal wants certainty"],
            "target_skill_slugs": ["expectation-setting"],
            "rubric_id": "scenario_text@v1",
            "mock_company": {
                "name": "Northstar Labs",
                "industry": "B2B SaaS",
                "operating_context": "Scaling under deadline pressure.",
            },
            "mock_people": [
                {
                    "name": "Mia",
                    "role": "VP Sales",
                    "goals": ["Hit the launch date"],
                    "communication_style": "Direct and impatient",
                    "relationship_to_scenario": "Commercial sponsor",
                }
            ],
            "supporting_artifacts": [
                {
                    "artifact_type": "email",
                    "title": "Sponsor escalation",
                    "body": "The board expects a clear recommendation before 9am.",
                }
            ],
        },
    )
    assert scenario_response.status_code == 200
    scenario_id = scenario_response.json()["data"]["id"]
    assert len(scenario_response.json()["data"]["supporting_artifacts"]) == 1

    update_collection_response = await client.patch(
        f"/api/collections/{collection_id}",
        headers={"X-User-ID": author["id"]},
        json={
            "title": "Creator Flow Final Draft",
            "summary": "Updated draft before publication.",
            "target_audience": "Early-career consultants",
            "difficulty": "advanced",
            "content_format_mix": ["quick_practice_prompt", "scenario_step"],
            "target_skill_slugs": ["active-listening", "expectation-setting"],
            "target_competency_slugs": ["stakeholder-management"],
            "rubric_ids": ["quick_practice_text@v1", "scenario_text@v1"],
        },
    )
    assert update_collection_response.status_code == 200
    assert update_collection_response.json()["data"]["difficulty"] == "advanced"

    update_prompt_response = await client.patch(
        f"/api/collections/{collection_id}/prompt-items/{prompt_id}",
        headers={"X-User-ID": author["id"]},
        json={
            "prompt_type": "quick_practice_prompt",
            "title": "Updated prompt",
            "prompt_text": "A sponsor pushes for speed over quality. Respond with empathy and a boundary.",
            "difficulty": "advanced",
            "target_skill_slugs": [],
            "rubric_id": "quick_practice_text@v1",
        },
    )
    assert update_prompt_response.status_code == 200
    assert update_prompt_response.json()["data"]["title"] == "Updated prompt"

    update_scenario_response = await client.patch(
        f"/api/collections/{collection_id}/scenarios/{scenario_id}",
        headers={"X-User-ID": author["id"]},
        json={
            "title": "Updated scenario",
            "business_context": "A product launch is at risk because legal review is incomplete.",
            "learner_objective": "Negotiate a credible next step across sales and legal.",
            "constraints": ["Board review tomorrow", "Only one engineering team is free"],
            "stakeholder_tensions": ["Sales wants speed", "Legal wants certainty"],
            "target_skill_slugs": ["expectation-setting"],
            "rubric_id": "scenario_text@v1",
            "mock_company": {
                "name": "Northstar Labs",
                "industry": "B2B SaaS",
                "operating_context": "Scaling under deadline pressure.",
            },
            "mock_people": [
                {
                    "name": "Mia",
                    "role": "VP Sales",
                    "goals": ["Hit the launch date"],
                    "communication_style": "Direct and impatient",
                    "relationship_to_scenario": "Commercial sponsor",
                }
            ],
            "supporting_artifacts": [
                {
                    "artifact_type": "brief",
                    "title": "Risk brief",
                    "body": "Legal approval is still pending on one customer commitment.",
                }
            ],
        },
    )
    assert update_scenario_response.status_code == 200
    assert (
        update_scenario_response.json()["data"]["supporting_artifacts"][0]["artifact_type"]
        == "brief"
    )

    publish_response = await client.patch(
        f"/api/collections/{collection_id}/lifecycle",
        headers={"X-User-ID": author["id"]},
        json={"lifecycle_state": "published_public"},
    )
    assert publish_response.status_code == 200
    assert publish_response.json()["data"]["discovery_tier"] == "standard_public"

    save_response = await client.post(
        f"/api/collections/{collection_id}/save",
        headers={"X-User-ID": saver["id"]},
    )
    assert save_response.status_code == 200
    assert save_response.json()["data"]["saved_by_actor"] is True
    assert save_response.json()["data"]["save_count"] == 1

    saved_only_response = await client.get(
        "/api/collections",
        headers={"X-User-ID": saver["id"]},
        params={"saved_only": "true"},
    )
    assert saved_only_response.status_code == 200
    assert [item["id"] for item in saved_only_response.json()["data"]] == [collection_id]

    standard_discovery_response = await client.get(
        "/api/collections",
        params={"discovery_tier": "standard_public", "include_private": "false"},
    )
    assert standard_discovery_response.status_code == 200
    assert [item["id"] for item in standard_discovery_response.json()["data"]] == [collection_id]

    verify_response = await client.post(
        f"/api/admin/collections/{collection_id}/verification",
        headers={"X-User-ID": admin["id"]},
        json={"verification_state": "verified", "note": "Strong metadata and mapping quality."},
    )
    assert verify_response.status_code == 200
    assert verify_response.json()["data"]["collection"]["discovery_tier"] == "global_public"

    verified_discovery_response = await client.get(
        "/api/collections",
        params={"discovery_tier": "global_public", "include_private": "false"},
    )
    assert verified_discovery_response.status_code == 200
    assert [item["id"] for item in verified_discovery_response.json()["data"]] == [collection_id]

    unsave_response = await client.delete(
        f"/api/collections/{collection_id}/save",
        headers={"X-User-ID": saver["id"]},
    )
    assert unsave_response.status_code == 200
    assert unsave_response.json()["data"]["saved_by_actor"] is False

    with app.state.container.session_factory() as session:
        event_types = {record.event_type for record in session.query(WorkflowEventRecord).all()}
        save_records = session.query(CollectionSaveRecord).all()

    assert "catalog.collection.updated.v1" in event_types
    assert "catalog.prompt_item.updated.v1" in event_types
    assert "catalog.scenario.updated.v1" in event_types
    assert "catalog.collection.saved.v1" in event_types
    assert "catalog.collection.unsaved.v1" in event_types
    assert "content.published.v1" in event_types
    assert save_records == []


@pytest.mark.asyncio
async def test_catalog_generation_flows_persist_artifacts_and_fail_on_drift(
    app, client, test_settings
) -> None:
    _migrate(test_settings)
    admin = await _register_user(client, email="admin5@example.com", display_name="Admin")
    await client.post("/api/skills/bootstrap-canon", headers={"X-User-ID": admin["id"]})
    creator = await _register_user(client, email="creator@example.com", display_name="Creator")

    app.state.container.catalog_service._generation._llm_provider = _FakeCatalogLLMProvider(
        [
            {
                "prompt_version": test_settings.creator_structured_generation_prompt_version,
                "provider": "test-provider",
                "model_slug": "test-model",
                "title": "Generated Stakeholder Collection",
                "summary": "Generated content for stakeholder pressure practice.",
                "prompt_items": [
                    {
                        "prompt_type": "quick_practice_prompt",
                        "title_hint": "Generated prompt",
                        "generation_brief": "A sponsor wants an impossible timeline. The learner must reset expectations while preserving trust.",
                        "difficulty": "intermediate",
                        "target_skill_slugs": [],
                        "rubric_id": "quick_practice_text@v1",
                    }
                ],
                "scenarios": [
                    {
                        "title_hint": "Generated scenario",
                        "generation_brief": "A launch is at risk after legal review and conflicting stakeholder expectations.",
                        "target_skill_slugs": ["expectation-setting"],
                        "rubric_id": "scenario_text@v1",
                        "supporting_artifact_count": 1,
                    }
                ],
            },
            {
                "prompt_type": "quick_practice_prompt",
                "title": "Generated prompt",
                "prompt_text": "A sponsor wants an impossible timeline. Respond.",
                "difficulty": "intermediate",
                "target_skill_slugs": [],
                "rubric_id": "quick_practice_text@v1",
                "generated_rubric": {
                    "title": "Generated prompt rubric",
                    "criteria": [
                        {
                            "criterion_ref": "active-listening",
                            "skill_slug": "active-listening",
                            "title": "Acknowledge the sponsor concern",
                            "description": "Check whether the response directly acknowledges the sponsor concern.",
                            "levels": [
                                {
                                    "level": 1,
                                    "description": "Fails to acknowledge the sponsor concern.",
                                    "examples": ["Ignores why the timeline matters."],
                                },
                                {
                                    "level": 2,
                                    "description": "Directly acknowledges the sponsor concern.",
                                    "examples": ["Recognizes the timeline pressure explicitly."],
                                },
                            ],
                        },
                        {
                            "criterion_ref": "expectation-setting",
                            "skill_slug": "expectation-setting",
                            "title": "Set a realistic next step",
                            "description": "Check whether the response sets a realistic boundary or next step.",
                            "levels": [
                                {
                                    "level": 1,
                                    "description": "Fails to set a realistic next step.",
                                    "examples": ["Makes an unrealistic commitment."],
                                },
                                {
                                    "level": 2,
                                    "description": "Sets a realistic next step or boundary.",
                                    "examples": ["Gives a credible follow-up timeline."],
                                },
                            ],
                        },
                    ],
                },
            },
            {
                "title": "Generated scenario",
                "business_context": "A launch is at risk after legal review.",
                "learner_objective": "Reset expectations without damaging trust.",
                "constraints": ["Board review tomorrow"],
                "stakeholder_tensions": ["Sales wants speed", "Legal wants certainty"],
                "target_skill_slugs": ["expectation-setting"],
                "rubric_id": "scenario_text@v1",
                "mock_company": {
                    "name": "Northstar AI",
                    "industry": "Enterprise SaaS",
                    "operating_context": "Scaling under board scrutiny.",
                },
                "mock_people": [
                    {
                        "name": "Jordan Singh",
                        "role": "Legal Counsel",
                        "goals": ["Reduce regulatory exposure"],
                        "communication_style": "Precise and cautious",
                        "relationship_to_scenario": "Risk owner",
                    }
                ],
                "supporting_artifacts": [
                    {
                        "artifact_type": "email",
                        "title": "Escalation note",
                        "body": "The board expects a recommendation by 9am.",
                    }
                ],
            },
            {
                "prompt_version": test_settings.creator_chat_generation_prompt_version,
                "provider": "test-provider",
                "model_slug": "test-model",
                "title": "Generated Interview Collection",
                "summary": "Generated interview content.",
                "prompt_items": [
                    {
                        "prompt_type": "interview_prompt",
                        "title_hint": "Generated interview prompt",
                        "generation_brief": "Tell me about a time you made a decision with incomplete data and had to justify the tradeoffs.",
                        "difficulty": "advanced",
                        "target_skill_slugs": ["decision-justification"],
                        "rubric_id": "interview_text@v1",
                    }
                ],
                "scenarios": [],
            },
            {
                "prompt_type": "interview_prompt",
                "title": "Generated interview prompt",
                "prompt_text": "Tell me about a time you made a decision with incomplete data.",
                "difficulty": "advanced",
                "target_skill_slugs": ["decision-justification"],
                "rubric_id": "interview_text@v1",
            },
            {
                "prompt_version": test_settings.creator_chat_generation_prompt_version,
                "provider": "test-provider",
                "model_slug": "test-model",
                "title": "Bad draft",
                "summary": "Bad metadata drift.",
                "prompt_items": [],
                "scenarios": [],
            },
            {
                "prompt_type": "interview_prompt",
                "title": "Bad interview prompt",
                "prompt_text": "Summarize an executive decision in one sentence.",
                "difficulty": "advanced",
                "target_skill_slugs": ["executive-summary"],
                "rubric_id": "interview_text@v1",
            },
        ]
    )

    structured_response = await client.post(
        "/api/collections/generate/structured",
        headers={"X-User-ID": creator["id"]},
        json={
            "title_hint": "Stakeholder realism pack",
            "target_audience": "Consultants",
            "difficulty": "intermediate",
            "content_format_mix": ["quick_practice_prompt", "scenario_step"],
            "target_skill_slugs": ["active-listening", "expectation-setting"],
            "target_competency_slugs": ["stakeholder-management"],
            "rubric_ids": ["quick_practice_text@v1", "scenario_text@v1"],
            "domain": "Enterprise SaaS",
            "workplace_context": "A product launch is under time pressure.",
            "scenario_theme": "Conflicting stakeholder expectations",
            "realism_notes": ["Avoid generic filler"],
            "counts": {
                "quick_practice_prompt_count": 1,
                "interview_prompt_count": 0,
                "scenario_count": 1,
                "scenario_artifact_count": 1,
            },
        },
    )
    assert structured_response.status_code == 200
    structured_payload = structured_response.json()["data"]
    assert structured_payload

    chat_response = await client.post(
        "/api/collections/generate/chat",
        headers={"X-User-ID": creator["id"]},
        json={
            "prompt": "Create a realistic interview draft about making a difficult decision.",
            "target_audience": "Consultants",
            "difficulty": "advanced",
            "content_format_mix": ["interview_prompt"],
            "target_skill_slugs": ["decision-justification"],
            "target_competency_slugs": ["problem-solving"],
            "rubric_ids": ["interview_text@v1"],
            "counts": {
                "quick_practice_prompt_count": 0,
                "interview_prompt_count": 1,
                "scenario_count": 0,
                "scenario_artifact_count": 0,
            },
        },
    )
    assert chat_response.status_code == 200
    chat_payload = chat_response.json()["data"]
    assert chat_payload


@pytest.mark.asyncio
async def test_catalog_generates_prompt_items_for_existing_collections(
    app, client, test_settings
) -> None:
    _migrate(test_settings)
    generation_config = load_catalog_generation_runtime_config()
    admin = await _register_user(client, email="admin6@example.com", display_name="Admin")
    await client.post("/api/skills/bootstrap-canon", headers={"X-User-ID": admin["id"]})
    creator = await _register_user(client, email="creator2@example.com", display_name="Creator")

    collection_response = await client.post(
        "/api/collections",
        headers={"X-User-ID": creator["id"]},
        json={
            "title": "Existing Interview Collection",
            "summary": "Practice tough stakeholder and interview conversations.",
            "target_audience": "Consultants",
            "difficulty": "advanced",
            "content_format_mix": ["quick_practice_prompt", "interview_prompt"],
            "target_skill_slugs": ["active-listening", "decision-justification"],
            "target_competency_slugs": ["stakeholder-management", "problem-solving"],
            "rubric_ids": ["quick_practice_text@v1", "interview_text@v1"],
        },
    )
    assert collection_response.status_code == 200
    collection_id = collection_response.json()["data"]["id"]

    existing_prompt_response = await client.post(
        f"/api/collections/{collection_id}/prompt-items",
        headers={"X-User-ID": creator["id"]},
        json={
            "prompt_type": "quick_practice_prompt",
            "title": "Existing reset expectations prompt",
            "prompt_text": "A client asks for an unrealistic deadline. Respond with empathy and a boundary.",
            "difficulty": "advanced",
            "target_skill_slugs": [],
            "rubric_id": "quick_practice_text@v1",
        },
    )
    assert existing_prompt_response.status_code == 200

    app.state.container.catalog_service._generation._llm_provider = _FakeCatalogLLMProvider(
        [
            {
                "prompt_version": generation_config.prompt_item_structured_prompt_version,
                "provider": "test-provider",
                "model_slug": "test-model",
                "prompt_items": [
                    {
                        "prompt_type": "quick_practice_prompt",
                        "title_hint": "Escalation reset",
                        "generation_brief": "A sponsor escalates a timeline conflict and the learner must reset expectations while staying collaborative.",
                        "difficulty": "advanced",
                        "target_skill_slugs": [],
                        "rubric_id": "quick_practice_text@v1",
                    }
                ],
            },
            {
                "prompt_type": "quick_practice_prompt",
                "title": "Escalation reset",
                "prompt_text": "A sponsor escalates a timeline conflict. Respond with empathy, clarity, and a credible next step.",
                "difficulty": "advanced",
                "target_skill_slugs": [],
                "rubric_id": "quick_practice_text@v1",
                "generated_rubric": {
                    "title": "Escalation reset rubric",
                    "criteria": [
                        {
                            "criterion_ref": "active-listening",
                            "skill_slug": "active-listening",
                            "title": "Acknowledge the escalation",
                            "description": "Check whether the response acknowledges the stakeholder pressure in the escalation.",
                            "levels": [
                                {
                                    "level": 1,
                                    "description": "Does not acknowledge the escalation pressure.",
                                    "examples": [
                                        "Responds mechanically without recognizing the pressure."
                                    ],
                                },
                                {
                                    "level": 2,
                                    "description": "Acknowledges the escalation pressure directly.",
                                    "examples": ["Explicitly recognizes the urgency or concern."],
                                },
                            ],
                        }
                    ],
                },
            },
            {
                "prompt_version": generation_config.prompt_item_chat_prompt_version,
                "provider": "test-provider",
                "model_slug": "test-model",
                "prompt_items": [
                    {
                        "prompt_type": "interview_prompt",
                        "title_hint": "Tradeoff interview",
                        "generation_brief": "Ask for a concrete story about making a decision with incomplete data and defending the tradeoffs.",
                        "difficulty": "advanced",
                        "target_skill_slugs": ["decision-justification"],
                        "rubric_id": "interview_text@v1",
                    }
                ],
            },
            {
                "prompt_type": "interview_prompt",
                "title": "Tradeoff interview",
                "prompt_text": "Tell me about a time you made a decision with incomplete data and had to defend the tradeoffs.",
                "difficulty": "advanced",
                "target_skill_slugs": ["decision-justification"],
                "rubric_id": "interview_text@v1",
            },
            {
                "prompt_version": generation_config.prompt_item_chat_prompt_version,
                "provider": "test-provider",
                "model_slug": "test-model",
                "prompt_items": [
                    {
                        "prompt_type": "interview_prompt",
                        "title_hint": "Duplicate interview",
                        "generation_brief": "Ask for the same decision story again.",
                        "difficulty": "advanced",
                        "target_skill_slugs": ["decision-justification"],
                        "rubric_id": "interview_text@v1",
                    }
                ],
            },
            {
                "prompt_type": "interview_prompt",
                "title": "Tradeoff interview",
                "prompt_text": "Tell me about a time you made a decision with incomplete data and had to defend the tradeoffs.",
                "difficulty": "advanced",
                "target_skill_slugs": ["decision-justification"],
                "rubric_id": "interview_text@v1",
            },
        ]
    )

    structured_generation_response = await client.post(
        f"/api/collections/{collection_id}/generate/prompt-items/structured",
        headers={"X-User-ID": creator["id"]},
        json={
            "title_hint": "Escalation realism pack",
            "workplace_context": "The engagement is slipping and sponsor patience is thin.",
            "generation_focus": "Generate one realistic quick practice prompt about resetting expectations.",
            "realism_notes": ["Keep the stakes concrete"],
            "target_skill_slugs": ["active-listening"],
            "counts": {
                "quick_practice_prompt_count": 1,
                "interview_prompt_count": 0,
            },
        },
    )
    assert structured_generation_response.status_code == 200
    structured_generation_payload = structured_generation_response.json()["data"]
    assert (
        structured_generation_payload.get("generation_mode", "prompt_items_structured")
        == "prompt_items_structured"
    )
    assert len(structured_generation_payload["prompt_items"]) == 1
    assert structured_generation_payload["prompt_items"][0]["title"] == "Escalation reset"
    assert structured_generation_payload["prompt_items"][0]["rubric_id"] != "quick_practice_text@v1"

    chat_generation_response = await client.post(
        f"/api/collections/{collection_id}/generate/prompt-items/chat",
        headers={"X-User-ID": creator["id"]},
        json={
            "prompt": "Add an interview prompt about defending a decision made with incomplete data.",
            "target_skill_slugs": ["decision-justification"],
            "counts": {
                "quick_practice_prompt_count": 0,
                "interview_prompt_count": 1,
            },
        },
    )
    assert chat_generation_response.status_code == 200
    chat_generation_payload = chat_generation_response.json()["data"]
    assert (
        chat_generation_payload.get("generation_mode", "prompt_items_chat") == "prompt_items_chat"
    )
    assert len(chat_generation_payload["prompt_items"]) == 1
    assert chat_generation_payload["prompt_items"][0]["title"] == "Tradeoff interview"

    duplicate_generation_response = await client.post(
        f"/api/collections/{collection_id}/generate/prompt-items/chat",
        headers={"X-User-ID": creator["id"]},
        json={
            "prompt": "Add that same interview prompt again.",
            "target_skill_slugs": ["decision-justification"],
            "counts": {
                "quick_practice_prompt_count": 0,
                "interview_prompt_count": 1,
            },
        },
    )
    assert duplicate_generation_response.status_code == 422
    assert duplicate_generation_response.json()["error"]["code"] == "SS-VALIDATION-065"

    with app.state.container.session_factory() as session:
        prompt_records = (
            session.query(ContentGenerationArtifactRecord)
            .filter(ContentGenerationArtifactRecord.collection_id == collection_id)
            .all()
        )
        generated_prompt_record = (
            session.query(PromptItemRecord)
            .filter(
                PromptItemRecord.collection_id == collection_id,
                PromptItemRecord.title == "Escalation reset",
            )
            .one()
        )
        generated_criteria_count = (
            session.query(RubricCriterionRecord)
            .filter(RubricCriterionRecord.rubric_id == generated_prompt_record.rubric_id)
            .count()
        )
        pipeline_names = {record.pipeline_name for record in session.query(PipelineRunRecord).all()}

    assert len(prompt_records) == 2
    assert generated_criteria_count == 1
    assert "catalog_prompt_items_structured_generation" in pipeline_names
    assert "catalog_prompt_items_chat_generation" in pipeline_names
    assert "catalog_prompt_item_worker" in pipeline_names
