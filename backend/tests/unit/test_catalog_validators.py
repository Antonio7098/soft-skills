from __future__ import annotations

import pytest

from soft_skills_backend.modules.catalog.domain.models import (
    CollectionGenerationCounts,
    CollectionListFilters,
    MockPersonInput,
    ScenarioCreateCommand,
    ScenarioSupportingArtifactInput,
)
from soft_skills_backend.modules.catalog.domain.validators import (
    discovery_tier_for_collection,
    validate_collection_filters,
    validate_mock_world,
    validate_supporting_artifacts,
)
from soft_skills_backend.platform.db.models import CollectionRecord


def test_collection_generation_counts_require_at_least_one_item() -> None:
    with pytest.raises(ValueError):
        CollectionGenerationCounts(
            quick_practice_prompt_count=0,
            interview_prompt_count=0,
            scenario_count=0,
            scenario_artifact_count=0,
        )


def test_validate_supporting_artifacts_rejects_unknown_type() -> None:
    with pytest.raises(Exception) as exc_info:
        validate_supporting_artifacts(
            [
                ScenarioSupportingArtifactInput(
                    artifact_type="spreadsheet",
                    title="Bad artifact",
                    body="Unsupported type",
                )
            ]
        )

    assert "SS-VALIDATION-044" in str(exc_info.value)


def test_validate_mock_world_requires_company_when_people_exist() -> None:
    command = ScenarioCreateCommand(
        title="Scenario",
        business_context="Context",
        learner_objective="Objective",
        constraints=[],
        stakeholder_tensions=[],
        target_skill_slugs=["expectation-setting"],
        rubric_id="scenario_text@v1",
        mock_people=[
            MockPersonInput(
                name="Mia",
                role="VP Sales",
                goals=["Ship faster"],
                communication_style="Direct",
                relationship_to_scenario="Sponsor",
            )
        ],
    )

    with pytest.raises(Exception) as exc_info:
        validate_mock_world(command)

    assert "SS-VALIDATION-045" in str(exc_info.value)


def test_discovery_tier_and_filter_validation_are_explicit() -> None:
    collection = CollectionRecord(
        id="collection-1",
        author_user_id="user-1",
        title="Title",
        summary="Summary",
        target_audience="Audience",
        difficulty="intermediate",
        lifecycle_state="published_public",
        verification_state="verified",
        source_type="manual",
        last_generation_artifact_id=None,
        content_format_mix=["quick_practice_prompt"],
        target_skill_slugs=["active-listening"],
        target_competency_slugs=["stakeholder-management"],
        rubric_ids=["quick_practice_text@v1"],
    )
    assert discovery_tier_for_collection(collection) == "verified_public"

    with pytest.raises(Exception) as exc_info:
        validate_collection_filters(CollectionListFilters(discovery_tier="unknown"))

    assert "SS-VALIDATION-034" in str(exc_info.value)
