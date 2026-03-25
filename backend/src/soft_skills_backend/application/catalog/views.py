"""Catalog view builders."""

from __future__ import annotations

from sqlalchemy.orm import Session

from soft_skills_backend.application.catalog.collections.views import CollectionView
from soft_skills_backend.application.catalog.prompt_items.views import PromptItemView
from soft_skills_backend.application.catalog.scenarios.views import (
    MockCompanyView,
    MockPersonView,
    ScenarioView,
)
from soft_skills_backend.persistence.models import (
    CollectionRecord,
    MockCompanyRecord,
    MockPersonRecord,
    PromptItemRecord,
    ScenarioRecord,
)


def build_collection_view(session: Session, record: CollectionRecord) -> CollectionView:
    """Build a collection view with prompt items and scenarios."""

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
        scenarios.append(
            ScenarioView(
                id=scenario.id,
                title=scenario.title,
                business_context=scenario.business_context,
                learner_objective=scenario.learner_objective,
                constraints=list(scenario.constraints),
                stakeholder_tensions=list(scenario.stakeholder_tensions),
                lifecycle_state=scenario.lifecycle_state,
                target_skill_slugs=list(scenario.target_skill_slugs),
                rubric_id=scenario.rubric_id,
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

    return CollectionView(
        id=record.id,
        author_user_id=record.author_user_id,
        title=record.title,
        summary=record.summary,
        target_audience=record.target_audience,
        difficulty=record.difficulty,
        lifecycle_state=record.lifecycle_state,
        verification_state=record.verification_state,
        content_format_mix=list(record.content_format_mix),
        target_skill_slugs=list(record.target_skill_slugs),
        target_competency_slugs=list(record.target_competency_slugs),
        rubric_ids=list(record.rubric_ids),
        prompt_items=prompt_items,
        scenarios=scenarios,
    )
