from __future__ import annotations

from unittest.mock import MagicMock

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from soft_skills_backend.modules.taxonomy.models import CompetencyView, SkillView, TaxonomySnapshot
from soft_skills_backend.modules.taxonomy.service import (
    COMMON_RUBRIC_CRITERIA,
    TaxonomyService,
    render_taxonomy_prompt_context,
)
from soft_skills_backend.platform.db.models import Base, RubricRecord, RubricVersionRecord


def test_render_taxonomy_prompt_context_includes_skills_and_competencies() -> None:
    snapshot = TaxonomySnapshot(
        skills=[
            SkillView(
                slug="active-listening",
                name="Active Listening",
                description="Listen carefully and respond to stakeholder signals.",
            )
        ],
        competencies=[
            CompetencyView(
                slug="stakeholder-management",
                name="Stakeholder Management",
                description="Manage stakeholder relationships.",
                skill_slugs=["active-listening"],
            )
        ],
        rubrics=[],
    )

    rendered = render_taxonomy_prompt_context(snapshot)

    assert "Skills: active-listening" in rendered
    assert "Competencies:" in rendered
    assert "- stakeholder-management: [active-listening]" in rendered
    assert "Use these slugs exactly" in rendered


def test_bootstrap_repairs_stale_seeded_rubric_versions() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, expire_on_commit=False)

    with session_factory() as session:
        session.add(
            RubricRecord(
                id="scenario_text@v1",
                skill_slug="general",
                name="Scenario Text Rubric",
                content_type="scenario_step",
                schema_version="v1",
            )
        )
        session.add(
            RubricVersionRecord(
                rubric_id="scenario_text@v1",
                version="v1",
                status="published",
                criteria=[
                    {
                        "criterion_ref": "stakeholder-analysis",
                        "skill_slug": "stakeholder-analysis",
                        "title": "Stakeholder Analysis",
                        "description": "Old stale criterion",
                        "weight": 1.0,
                        "required": True,
                        "position": 1,
                        "levels": [{"level_1": {"description": "Poor", "examples": []}}],
                    }
                ],
            )
        )
        session.commit()

    service = TaxonomyService(
        session_factory=session_factory,
        workflow_events=MagicMock(),
    )

    service.bootstrap()

    with session_factory() as session:
        version = (
            session.query(RubricVersionRecord)
            .filter(
                RubricVersionRecord.rubric_id == "scenario_text@v1",
                RubricVersionRecord.version == "v1",
            )
            .one()
        )

    assert version.status == "published"
    assert [criterion["criterion_ref"] for criterion in version.criteria] == [
        criterion.criterion_ref for criterion in COMMON_RUBRIC_CRITERIA
    ]
