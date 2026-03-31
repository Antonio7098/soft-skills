"""Catalog view builders."""

from __future__ import annotations

from sqlalchemy.orm import Session

from soft_skills_backend.modules.catalog.contracts.collection_views import CollectionView
from soft_skills_backend.modules.catalog.contracts.prompt_item_views import PromptItemView
from soft_skills_backend.modules.catalog.contracts.scenario_views import (
    MockCompanyView,
    MockPersonView,
    ScenarioSupportingArtifactView,
    ScenarioView,
)
from soft_skills_backend.modules.catalog.domain.validators import discovery_tier_for_collection
from soft_skills_backend.platform.db.models import (
    CollectionRatingRecord,
    CollectionRecord,
    CollectionSaveRecord,
    MockCompanyRecord,
    MockPersonRecord,
    PromptItemRecord,
    ScenarioRecord,
    ScenarioSupportingArtifactRecord,
)
from soft_skills_backend.shared.auth import Actor


def build_collection_view(
    session: Session,
    record: CollectionRecord,
    *,
    actor: Actor | None,
) -> CollectionView:
    """Build a collection view with prompt items, scenarios, and actor-specific discovery state."""

    prompt_items = [
        PromptItemView(
            id=item.id,
            prompt_type=item.prompt_type,
            title=item.title,
            prompt_text=item.prompt_text,
            difficulty=item.difficulty,
            lifecycle_state=item.lifecycle_state,
            target_skill_slugs=list(item.target_skill_slugs),
            rubric_id=item.rubric_id,
        )
        for item in session.query(PromptItemRecord)
        .filter(PromptItemRecord.collection_id == record.id)
        .order_by(PromptItemRecord.created_at)
        .all()
    ]
    scenarios: list[ScenarioView] = []
    scenario_records = (
        session.query(ScenarioRecord)
        .filter(ScenarioRecord.collection_id == record.id)
        .order_by(ScenarioRecord.created_at)
        .all()
    )
    for scenario in scenario_records:
        company_record = (
            session.query(MockCompanyRecord)
            .filter(MockCompanyRecord.scenario_id == scenario.id)
            .one_or_none()
        )
        people_records = (
            session.query(MockPersonRecord)
            .filter(MockPersonRecord.scenario_id == scenario.id)
            .order_by(MockPersonRecord.name)
            .all()
        )
        artifact_records = (
            session.query(ScenarioSupportingArtifactRecord)
            .filter(ScenarioSupportingArtifactRecord.scenario_id == scenario.id)
            .order_by(ScenarioSupportingArtifactRecord.created_at)
            .all()
        )
        scenarios.append(
            ScenarioView(
                id=scenario.id,
                title=scenario.title,
                business_context=scenario.business_context,
                learner_objective=scenario.learner_objective,
                constraints=list(scenario.constraints),
                stakeholder_tensions=list(scenario.stakeholder_tensions),
                questions=list(scenario.questions),
                lifecycle_state=scenario.lifecycle_state,
                target_skill_slugs=list(scenario.target_skill_slugs),
                rubric_id=scenario.rubric_id,
                supporting_artifacts=[
                    ScenarioSupportingArtifactView(
                        id=artifact.id,
                        artifact_type=artifact.artifact_type,
                        title=artifact.title,
                        body=artifact.body,
                    )
                    for artifact in artifact_records
                ],
                mock_company=None
                if company_record is None
                else MockCompanyView(
                    id=company_record.id,
                    name=company_record.name,
                    industry=company_record.industry,
                    operating_context=company_record.operating_context,
                ),
                mock_people=[
                    MockPersonView(
                        id=person.id,
                        name=person.name,
                        role=person.role,
                        goals=list(person.goals),
                        communication_style=person.communication_style,
                        relationship_to_scenario=person.relationship_to_scenario,
                    )
                    for person in people_records
                ],
            )
        )

    save_count = (
        session.query(CollectionSaveRecord)
        .filter(CollectionSaveRecord.collection_id == record.id)
        .count()
    )
    saved_by_actor = False
    rated_by_actor = None
    if actor is not None:
        saved_by_actor = (
            session.query(CollectionSaveRecord)
            .filter(
                CollectionSaveRecord.collection_id == record.id,
                CollectionSaveRecord.user_id == actor.user_id,
            )
            .count()
            > 0
        )
        rating_record = (
            session.query(CollectionRatingRecord)
            .filter(
                CollectionRatingRecord.collection_id == record.id,
                CollectionRatingRecord.user_id == actor.user_id,
            )
            .one_or_none()
        )
        if rating_record is not None:
            rated_by_actor = rating_record.rating

    return CollectionView(
        id=record.id,
        author_user_id=record.author_user_id,
        organisation_id=record.organisation_id,
        title=record.title,
        summary=record.summary,
        target_audience=record.target_audience,
        difficulty=record.difficulty,
        lifecycle_state=record.lifecycle_state,
        verification_state=record.verification_state,
        discovery_tier=discovery_tier_for_collection(record),
        source_type=record.source_type,
        content_format_mix=list(record.content_format_mix),
        target_skill_slugs=list(record.target_skill_slugs),
        target_competency_slugs=list(record.target_competency_slugs),
        rubric_ids=list(record.rubric_ids),
        save_count=save_count,
        saved_by_actor=saved_by_actor,
        avg_rating=record.avg_rating,
        rating_count=record.rating_count,
        rated_by_actor=rated_by_actor,
        last_generation_artifact_id=record.last_generation_artifact_id,
        prompt_items=prompt_items,
        scenarios=scenarios,
    )
