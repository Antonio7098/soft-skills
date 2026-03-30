from __future__ import annotations

from soft_skills_backend.modules.taxonomy.models import CompetencyView, SkillView, TaxonomySnapshot
from soft_skills_backend.modules.taxonomy.service import render_taxonomy_prompt_context


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
