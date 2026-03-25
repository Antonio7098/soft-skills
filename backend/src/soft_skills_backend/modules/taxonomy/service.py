"""Taxonomy and rubric seed service."""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session, sessionmaker

from soft_skills_backend.modules.taxonomy.models import (
    CompetencyView,
    RubricView,
    SkillView,
    TaxonomySnapshot,
)
from soft_skills_backend.platform.db.models import (
    CompetencyRecord,
    CompetencySkillMapRecord,
    RubricRecord,
    SkillRecord,
)
from soft_skills_backend.platform.db.repositories import SqlAlchemyWorkflowEventRepository
from soft_skills_backend.platform.observability.events import WorkflowEvent


@dataclass(frozen=True, slots=True)
class CompetencySeed:
    slug: str
    name: str
    description: str
    skills: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class SkillSeed:
    slug: str
    name: str
    description: str


@dataclass(frozen=True, slots=True)
class RubricSeed:
    rubric_id: str
    family: str
    version: str
    content_type: str
    schema_version: str
    name: str


SKILL_SEEDS: tuple[SkillSeed, ...] = (
    SkillSeed(
        "active-listening",
        "Active Listening",
        "Listen carefully and respond to stakeholder signals.",
    ),
    SkillSeed("structured-communication", "Structured Communication", "Organize ideas clearly."),
    SkillSeed("concise-explanation", "Concise Explanation", "Explain decisions succinctly."),
    SkillSeed("empathy", "Empathy", "Acknowledge stakeholder concerns and emotion."),
    SkillSeed(
        "expectation-setting", "Expectation Setting", "Set realistic next steps and boundaries."
    ),
    SkillSeed(
        "prioritization-under-pressure",
        "Prioritization Under Pressure",
        "Choose effectively under constraints.",
    ),
    SkillSeed("conflict-handling", "Conflict Handling", "Address disagreement productively."),
    SkillSeed("negotiation", "Negotiation", "Trade off and align competing interests."),
    SkillSeed(
        "executive-summary", "Executive Summary", "Summarize clearly for senior stakeholders."
    ),
    SkillSeed(
        "decision-justification",
        "Decision Justification",
        "Back decisions with evidence and reasoning.",
    ),
)

COMPETENCY_SEEDS: tuple[CompetencySeed, ...] = (
    CompetencySeed(
        "stakeholder-management",
        "Stakeholder Management",
        "Manage stakeholder relationships.",
        ("active-listening", "empathy", "expectation-setting", "negotiation"),
    ),
    CompetencySeed(
        "communication",
        "Communication",
        "Communicate clearly and effectively.",
        ("structured-communication", "concise-explanation", "executive-summary"),
    ),
    CompetencySeed(
        "teamwork",
        "Teamwork",
        "Work constructively with others.",
        ("active-listening", "empathy", "conflict-handling"),
    ),
    CompetencySeed(
        "prioritization",
        "Prioritization",
        "Prioritize under constraints.",
        ("prioritization-under-pressure", "decision-justification", "executive-summary"),
    ),
    CompetencySeed(
        "professionalism",
        "Professionalism",
        "Behave credibly and reliably.",
        ("expectation-setting", "concise-explanation", "conflict-handling"),
    ),
    CompetencySeed(
        "problem-solving",
        "Problem Solving",
        "Diagnose and solve problems.",
        ("structured-communication", "decision-justification", "executive-summary"),
    ),
    CompetencySeed(
        "adaptability",
        "Adaptability",
        "Adjust appropriately as conditions change.",
        ("active-listening", "prioritization-under-pressure", "decision-justification"),
    ),
    CompetencySeed(
        "managing-ambiguity",
        "Managing Ambiguity",
        "Operate effectively with unclear inputs.",
        ("expectation-setting", "prioritization-under-pressure", "negotiation"),
    ),
)

RUBRIC_SEEDS: tuple[RubricSeed, ...] = (
    RubricSeed(
        "quick_practice_text@v1",
        "quick_practice_text",
        "v1",
        "quick_practice_prompt",
        "v1",
        "Quick Practice Text Rubric",
    ),
    RubricSeed(
        "scenario_text@v1", "scenario_text", "v1", "scenario_step", "v1", "Scenario Text Rubric"
    ),
    RubricSeed(
        "interview_text@v1",
        "interview_text",
        "v1",
        "interview_prompt",
        "v1",
        "Interview Text Rubric",
    ),
)


class TaxonomyService:
    """Seed and list the frozen Sprint 0 taxonomy and rubric model."""

    def __init__(
        self,
        *,
        session_factory: sessionmaker[Session],
        workflow_events: SqlAlchemyWorkflowEventRepository,
    ) -> None:
        self._session_factory = session_factory
        self._workflow_events = workflow_events

    def bootstrap(self) -> TaxonomySnapshot:
        with self._session_factory() as session:
            if session.query(SkillRecord).count() == 0:
                for skill_seed in SKILL_SEEDS:
                    session.add(
                        SkillRecord(
                            slug=skill_seed.slug,
                            name=skill_seed.name,
                            description=skill_seed.description,
                        )
                    )
            if session.query(CompetencyRecord).count() == 0:
                for competency_seed in COMPETENCY_SEEDS:
                    session.add(
                        CompetencyRecord(
                            slug=competency_seed.slug,
                            name=competency_seed.name,
                            description=competency_seed.description,
                        )
                    )
                    for skill_slug in competency_seed.skills:
                        session.add(
                            CompetencySkillMapRecord(
                                competency_slug=competency_seed.slug,
                                skill_slug=skill_slug,
                                weight=1.0,
                            )
                        )
            if session.query(RubricRecord).count() == 0:
                for rubric_seed in RUBRIC_SEEDS:
                    session.add(
                        RubricRecord(
                            rubric_id=rubric_seed.rubric_id,
                            family=rubric_seed.family,
                            version=rubric_seed.version,
                            content_type=rubric_seed.content_type,
                            schema_version=rubric_seed.schema_version,
                            name=rubric_seed.name,
                            criteria=["overall_score", "skill_scores", "evidence", "rationale"],
                        )
                    )
            session.commit()

        self._workflow_events.record(
            WorkflowEvent(
                event_type="taxonomy.catalog_seeded.v1",
                payload={
                    "skills": len(SKILL_SEEDS),
                    "competencies": len(COMPETENCY_SEEDS),
                    "rubrics": len(RUBRIC_SEEDS),
                },
            )
        )
        return self.snapshot()

    def snapshot(self) -> TaxonomySnapshot:
        with self._session_factory() as session:
            skills = [
                SkillView(slug=record.slug, name=record.name, description=record.description)
                for record in session.query(SkillRecord).order_by(SkillRecord.name).all()
            ]
            mappings = session.query(CompetencySkillMapRecord).all()
            competency_to_skills: dict[str, list[str]] = {}
            for mapping in mappings:
                competency_to_skills.setdefault(mapping.competency_slug, []).append(
                    mapping.skill_slug
                )
            competencies = [
                CompetencyView(
                    slug=record.slug,
                    name=record.name,
                    description=record.description,
                    skill_slugs=sorted(competency_to_skills.get(record.slug, [])),
                )
                for record in session.query(CompetencyRecord).order_by(CompetencyRecord.name).all()
            ]
            rubrics = [
                RubricView(
                    rubric_id=record.rubric_id,
                    family=record.family,
                    version=record.version,
                    content_type=record.content_type,
                    schema_version=record.schema_version,
                    name=record.name,
                )
                for record in session.query(RubricRecord).order_by(RubricRecord.rubric_id).all()
            ]
        return TaxonomySnapshot(skills=skills, competencies=competencies, rubrics=rubrics)
