from __future__ import annotations

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from soft_skills_backend.modules.catalog.domain.validators import (
    require_existing_competencies,
    require_existing_rubrics,
    require_existing_skills,
    validate_mock_world,
    validate_supporting_artifacts,
)
from soft_skills_backend.modules.catalog.domain.models import (
    MockPersonInput,
    ScenarioCreateCommand,
    ScenarioSupportingArtifactInput,
)
from soft_skills_backend.platform.db.models import (
    CompetencyRecord,
    RubricRecord,
    RubricVersionRecord,
    SkillRecord,
    Base,
)


@pytest.fixture
def session() -> Session:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    return SessionLocal()


def test_require_existing_skills_with_null_org_id(session: Session) -> None:
    canon_skill = SkillRecord(
        slug="canon-skill",
        name="Canon Skill",
        description="A canon skill",
        organisation_id=None,
    )
    session.add(canon_skill)
    session.commit()

    require_existing_skills(session, ["canon-skill"], organisation_id=None)
    with pytest.raises(Exception) as exc_info:
        require_existing_skills(session, ["non-existent"], organisation_id=None)
    assert "SS-VALIDATION-013" in str(exc_info.value)


def test_require_existing_skills_with_org_id(session: Session) -> None:
    canon_skill = SkillRecord(
        slug="shared-skill",
        name="Shared Skill",
        description="A shared skill",
        organisation_id=None,
    )
    org_skill = SkillRecord(
        slug="org-skill",
        name="Org Skill",
        description="An org-specific skill",
        organisation_id="org-123",
    )
    session.add(canon_skill)
    session.add(org_skill)
    session.commit()

    require_existing_skills(session, ["shared-skill"], organisation_id="org-123")
    require_existing_skills(session, ["org-skill"], organisation_id="org-123")
    require_existing_skills(session, ["shared-skill", "org-skill"], organisation_id="org-123")

    with pytest.raises(Exception) as exc_info:
        require_existing_skills(session, ["org-skill"], organisation_id=None)
    assert "SS-VALIDATION-013" in str(exc_info.value)

    with pytest.raises(Exception) as exc_info:
        require_existing_skills(session, ["non-existent"], organisation_id="org-123")
    assert "SS-VALIDATION-013" in str(exc_info.value)


def test_require_existing_skills_other_org_rejected(session: Session) -> None:
    other_org_skill = SkillRecord(
        slug="other-org-skill",
        name="Other Org Skill",
        description="Skill from another org",
        organisation_id="other-org",
    )
    session.add(other_org_skill)
    session.commit()

    with pytest.raises(Exception) as exc_info:
        require_existing_skills(session, ["other-org-skill"], organisation_id="my-org")
    assert "SS-VALIDATION-013" in str(exc_info.value)


def test_require_existing_competencies_with_null_org_id(session: Session) -> None:
    canon_comp = CompetencyRecord(
        slug="canon-competency",
        name="Canon Competency",
        description="A canon competency",
        organisation_id=None,
    )
    session.add(canon_comp)
    session.commit()

    require_existing_competencies(session, ["canon-competency"], organisation_id=None)
    with pytest.raises(Exception) as exc_info:
        require_existing_competencies(session, ["non-existent"], organisation_id=None)
    assert "SS-VALIDATION-014" in str(exc_info.value)


def test_require_existing_competencies_with_org_id(session: Session) -> None:
    canon_comp = CompetencyRecord(
        slug="shared-competency",
        name="Shared Competency",
        description="A shared competency",
        organisation_id=None,
    )
    org_comp = CompetencyRecord(
        slug="org-competency",
        name="Org Competency",
        description="An org-specific competency",
        organisation_id="org-123",
    )
    session.add(canon_comp)
    session.add(org_comp)
    session.commit()

    require_existing_competencies(session, ["shared-competency"], organisation_id="org-123")
    require_existing_competencies(session, ["org-competency"], organisation_id="org-123")

    with pytest.raises(Exception) as exc_info:
        require_existing_competencies(session, ["org-competency"], organisation_id=None)
    assert "SS-VALIDATION-014" in str(exc_info.value)


def test_require_existing_rubrics_with_null_org_id(session: Session) -> None:
    canon_rubric = RubricRecord(
        id="canon-rubric@v1",
        skill_slug="active-listening",
        content_type="quick_practice_prompt",
        schema_version="v1",
        name="Canon Rubric",
        organisation_id=None,
    )
    session.add(canon_rubric)
    session.commit()

    require_existing_rubrics(session, ["canon-rubric@v1"], organisation_id=None)
    with pytest.raises(Exception) as exc_info:
        require_existing_rubrics(session, ["non-existent"], organisation_id=None)
    assert "SS-VALIDATION-015" in str(exc_info.value)


def test_require_existing_rubrics_with_org_id(session: Session) -> None:
    canon_rubric = RubricRecord(
        id="shared-rubric@v1",
        skill_slug="active-listening",
        content_type="quick_practice_prompt",
        schema_version="v1",
        name="Shared Rubric",
        organisation_id=None,
    )
    org_rubric = RubricRecord(
        id="org-rubric@v1",
        skill_slug="active-listening",
        content_type="quick_practice_prompt",
        schema_version="v1",
        name="Org Rubric",
        organisation_id="org-123",
    )
    session.add(canon_rubric)
    session.add(org_rubric)
    session.commit()

    require_existing_rubrics(session, ["shared-rubric@v1"], organisation_id="org-123")
    require_existing_rubrics(session, ["org-rubric@v1"], organisation_id="org-123")

    with pytest.raises(Exception) as exc_info:
        require_existing_rubrics(session, ["org-rubric@v1"], organisation_id=None)
    assert "SS-VALIDATION-015" in str(exc_info.value)


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
