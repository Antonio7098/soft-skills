from __future__ import annotations

import json
from pathlib import Path

import pytest
from alembic.config import Config

from alembic import command
from soft_skills_backend.platform.db.models import (
    CollectionRecord,
    CollectionSaveRecord,
    ContentGenerationArtifactRecord,
    PipelineRunRecord,
    WorkflowEventRecord,
)
from soft_skills_backend.shared.ports.models import ProviderCompletion


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


class _FakeCatalogLLMProvider:
    def __init__(self, payloads: list[dict[str, object]]) -> None:
        self.provider_name = "test-provider"
        self.model_slug = "test-model"
        self._payloads = payloads

    async def complete_json(self, *, messages, call_context) -> ProviderCompletion:
        assert messages
        assert call_context.operation in {
            "catalog_structured_generation",
            "catalog_chat_generation",
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
    admin = await _register_user(
        client, email="admin2@example.com", display_name="Admin", role="admin"
    )
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
    admin = await _register_user(
        client, email="admin3@example.com", display_name="Admin", role="admin"
    )
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
    admin = await _register_user(
        client, email="admin4@example.com", display_name="Admin", role="admin"
    )
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
            "target_skill_slugs": ["active-listening"],
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
            "target_skill_slugs": ["active-listening", "expectation-setting"],
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
    assert update_scenario_response.json()["data"]["supporting_artifacts"][0]["artifact_type"] == "brief"

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
    assert verify_response.json()["data"]["collection"]["discovery_tier"] == "verified_public"

    verified_discovery_response = await client.get(
        "/api/collections",
        params={"discovery_tier": "verified_public", "include_private": "false"},
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
    admin = await _register_user(
        client, email="admin5@example.com", display_name="Admin", role="admin"
    )
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
                "target_audience": "Consultants",
                "difficulty": "intermediate",
                "content_format_mix": ["quick_practice_prompt", "scenario_step"],
                "target_skill_slugs": ["active-listening", "expectation-setting"],
                "target_competency_slugs": ["stakeholder-management"],
                "rubric_ids": ["quick_practice_text@v1", "scenario_text@v1"],
                "prompt_items": [
                    {
                        "prompt_type": "quick_practice_prompt",
                        "title": "Generated prompt",
                        "prompt_text": "A sponsor wants an impossible timeline. Respond.",
                        "difficulty": "intermediate",
                        "target_skill_slugs": ["active-listening", "expectation-setting"],
                        "rubric_id": "quick_practice_text@v1",
                    }
                ],
                "scenarios": [
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
                    }
                ],
            },
            {
                "prompt_version": test_settings.creator_chat_generation_prompt_version,
                "provider": "test-provider",
                "model_slug": "test-model",
                "title": "Generated Interview Collection",
                "summary": "Generated interview content.",
                "target_audience": "Consultants",
                "difficulty": "advanced",
                "content_format_mix": ["interview_prompt"],
                "target_skill_slugs": ["decision-justification"],
                "target_competency_slugs": ["problem-solving"],
                "rubric_ids": ["interview_text@v1"],
                "prompt_items": [
                    {
                        "prompt_type": "interview_prompt",
                        "title": "Generated interview prompt",
                        "prompt_text": "Tell me about a time you made a decision with incomplete data.",
                        "difficulty": "advanced",
                        "target_skill_slugs": ["decision-justification"],
                        "rubric_id": "interview_text@v1",
                    }
                ],
                "scenarios": [],
            },
            {
                "prompt_version": test_settings.creator_chat_generation_prompt_version,
                "provider": "test-provider",
                "model_slug": "test-model",
                "title": "Bad draft",
                "summary": "Bad metadata drift.",
                "target_audience": "Consultants",
                "difficulty": "advanced",
                "content_format_mix": ["interview_prompt"],
                "target_skill_slugs": ["executive-summary"],
                "target_competency_slugs": ["problem-solving"],
                "rubric_ids": ["interview_text@v1"],
                "prompt_items": [],
                "scenarios": [],
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
    assert structured_payload["generation_mode"] == "structured"
    assert structured_payload["collection"]["source_type"] == "generated_structured"
    assert structured_payload["collection"]["last_generation_artifact_id"] is not None

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
    assert chat_payload["generation_mode"] == "chat"
    assert chat_payload["collection"]["source_type"] == "generated_chat"

    drift_response = await client.post(
        "/api/collections/generate/chat",
        headers={"X-User-ID": creator["id"]},
        json={
            "prompt": "Create another interview draft.",
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
    assert drift_response.status_code == 422
    assert drift_response.json()["error"]["code"] == "SS-VALIDATION-051"

    with app.state.container.session_factory() as session:
        generation_artifacts = session.query(ContentGenerationArtifactRecord).all()
        event_types = {record.event_type for record in session.query(WorkflowEventRecord).all()}
        pipeline_names = {record.pipeline_name for record in session.query(PipelineRunRecord).all()}

    assert len(generation_artifacts) == 2
    assert "content.draft.generated.v1" in event_types
    assert "catalog_structured_generation" in pipeline_names
    assert "catalog_chat_generation" in pipeline_names
