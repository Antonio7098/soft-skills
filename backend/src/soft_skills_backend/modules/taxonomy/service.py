"""Taxonomy and rubric seed service."""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import or_
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
    OrganisationSkillMapRecord,
    RubricRecord,
    RubricVersionRecord,
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
    criteria: tuple[RubricCriterionSeed, ...]


@dataclass(frozen=True, slots=True)
class RubricLevelSeed:
    level: int
    description: str
    examples: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class RubricCriterionSeed:
    criterion_ref: str
    skill_slug: str
    title: str
    description: str
    weight: float
    required: bool
    position: int
    levels: tuple[RubricLevelSeed, ...]


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


def _levels(
    *,
    skill_name: str,
    poor: str,
    adequate: str,
    excellent: str,
) -> tuple[RubricLevelSeed, ...]:
    return (
        RubricLevelSeed(1, poor, (f"No credible {skill_name.lower()} signal.",)),
        RubricLevelSeed(
            2,
            f"Shows limited {skill_name.lower()} with notable gaps.",
            (f"Weak {skill_name.lower()} signal with missed opportunities.",),
        ),
        RubricLevelSeed(
            3,
            adequate,
            (f"Adequate {skill_name.lower()} signal with partial coverage.",),
        ),
        RubricLevelSeed(
            4,
            f"Shows strong {skill_name.lower()} with minor gaps.",
            (f"Strong {skill_name.lower()} signal with small omissions.",),
        ),
        RubricLevelSeed(5, excellent, (f"Clear and consistent {skill_name.lower()} signal.",)),
    )


def _binary_levels(
    *,
    fail_description: str,
    pass_description: str,
    fail_example: str,
    pass_example: str,
) -> tuple[RubricLevelSeed, ...]:
    return (
        RubricLevelSeed(1, fail_description, (fail_example,)),
        RubricLevelSeed(2, pass_description, (pass_example,)),
    )


def _criterion(
    *,
    position: int,
    skill_slug: str,
    title: str,
    description: str,
    poor: str,
    adequate: str,
    excellent: str,
    weight: float = 1.0,
) -> RubricCriterionSeed:
    return RubricCriterionSeed(
        criterion_ref=skill_slug,
        skill_slug=skill_slug,
        title=title,
        description=description,
        weight=weight,
        required=True,
        position=position,
        levels=_levels(skill_name=title, poor=poor, adequate=adequate, excellent=excellent),
    )


def _binary_criterion(
    *,
    position: int,
    skill_slug: str,
    title: str,
    description: str,
    fail_description: str,
    pass_description: str,
    fail_example: str,
    pass_example: str,
    weight: float = 1.0,
) -> RubricCriterionSeed:
    return RubricCriterionSeed(
        criterion_ref=skill_slug,
        skill_slug=skill_slug,
        title=title,
        description=description,
        weight=weight,
        required=True,
        position=position,
        levels=_binary_levels(
            fail_description=fail_description,
            pass_description=pass_description,
            fail_example=fail_example,
            pass_example=pass_example,
        ),
    )


COMMON_RUBRIC_CRITERIA: tuple[RubricCriterionSeed, ...] = (
    _criterion(
        position=1,
        skill_slug="active-listening",
        title="Active Listening",
        description="Assess whether the learner reflects stakeholder signals and responds to them.",
        poor="Does not reflect stakeholder concerns or acknowledge what matters.",
        adequate="Partially reflects stakeholder concerns but misses important signals.",
        excellent="Clearly reflects stakeholder concerns, priorities, and emotional signals.",
    ),
    _criterion(
        position=2,
        skill_slug="structured-communication",
        title="Structured Communication",
        description="Assess whether the learner organizes the response clearly and logically.",
        poor="Response is disorganized and difficult to follow.",
        adequate="Response has some structure but sequencing or clarity is inconsistent.",
        excellent="Response is clear, well sequenced, and easy to follow.",
    ),
    _criterion(
        position=3,
        skill_slug="concise-explanation",
        title="Concise Explanation",
        description="Assess whether the learner explains the point efficiently without unnecessary sprawl.",
        poor="Response is verbose, vague, or indirect.",
        adequate="Response is understandable but could be tighter and more direct.",
        excellent="Response is direct, efficient, and appropriately concise.",
    ),
    _criterion(
        position=4,
        skill_slug="empathy",
        title="Empathy",
        description="Assess whether the learner acknowledges stakeholder concerns with care and credibility.",
        poor="Ignores or dismisses stakeholder concerns.",
        adequate="Acknowledges concerns at a surface level without much depth.",
        excellent="Acknowledges concerns credibly and responds with appropriate care.",
    ),
    _criterion(
        position=5,
        skill_slug="expectation-setting",
        title="Expectation Setting",
        description="Assess whether the learner sets realistic next steps, boundaries, or timing.",
        poor="Sets no clear expectations or makes unrealistic commitments.",
        adequate="Sets partial expectations but leaves ambiguity about next steps or timing.",
        excellent="Sets clear, realistic expectations, ownership, and next-step timing.",
    ),
    _criterion(
        position=6,
        skill_slug="prioritization-under-pressure",
        title="Prioritization Under Pressure",
        description="Assess whether the learner prioritizes well under constraints or urgency.",
        poor="Does not prioritize or chooses weak tradeoffs under pressure.",
        adequate="Makes a workable prioritization choice but misses some tradeoffs.",
        excellent="Makes strong prioritization decisions with clear tradeoff handling.",
    ),
    _criterion(
        position=7,
        skill_slug="conflict-handling",
        title="Conflict Handling",
        description="Assess whether the learner handles disagreement constructively.",
        poor="Escalates conflict or avoids it without resolving the issue.",
        adequate="Handles disagreement partly but leaves tension unresolved.",
        excellent="Handles disagreement constructively while moving toward resolution.",
    ),
    _criterion(
        position=8,
        skill_slug="negotiation",
        title="Negotiation",
        description="Assess whether the learner trades off positions to move stakeholders toward alignment.",
        poor="Does not negotiate or treats positions as fixed.",
        adequate="Attempts tradeoffs but misses leverage or alignment opportunities.",
        excellent="Uses tradeoffs well to move stakeholders toward workable alignment.",
    ),
    _criterion(
        position=9,
        skill_slug="executive-summary",
        title="Executive Summary",
        description="Assess whether the learner can summarize the key message for a senior audience.",
        poor="Does not surface the key takeaway clearly.",
        adequate="Surfaces a usable takeaway but with some clutter or missing emphasis.",
        excellent="Surfaces the key takeaway clearly, crisply, and at the right altitude.",
    ),
    _criterion(
        position=10,
        skill_slug="decision-justification",
        title="Decision Justification",
        description="Assess whether the learner justifies recommendations with reasoning and evidence.",
        poor="Makes assertions without clear reasoning.",
        adequate="Provides some reasoning but leaves important logic unstated.",
        excellent="Justifies recommendations with clear, defensible reasoning.",
    ),
)

QUICK_PRACTICE_RESET_TIMELINE_CRITERIA: tuple[RubricCriterionSeed, ...] = (
    _binary_criterion(
        position=1,
        skill_slug="active-listening",
        title="Acknowledge The Client Concern",
        description=(
            "Check whether the response directly acknowledges why the requested date matters "
            "to the stakeholder."
        ),
        fail_description="The response does not acknowledge the client concern or why the date matters.",
        pass_description="The response directly acknowledges the client concern and why the date matters.",
        fail_example="Jumps straight to logistics without recognizing the stakeholder concern.",
        pass_example="Explicitly recognizes the importance or pressure behind the requested date.",
    ),
    _binary_criterion(
        position=2,
        skill_slug="expectation-setting",
        title="Set A Realistic Next Step",
        description=(
            "Check whether the response sets a realistic next step, boundary, or timeline "
            "instead of making a vague or impossible commitment."
        ),
        fail_description="The response does not set a realistic next step or makes an unrealistic commitment.",
        pass_description="The response sets a clear and realistic next step, boundary, or timeline.",
        fail_example="Promises the impossible date without clarifying tradeoffs or next steps.",
        pass_example="Sets a realistic date, boundary, or follow-up action with concrete timing.",
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
        COMMON_RUBRIC_CRITERIA,
    ),
    RubricSeed(
        "quick_practice_reset_timeline@v1",
        "quick_practice_reset_timeline",
        "v1",
        "quick_practice_prompt",
        "v1",
        "Quick Practice Reset Timeline Rubric",
        QUICK_PRACTICE_RESET_TIMELINE_CRITERIA,
    ),
    RubricSeed(
        "scenario_text@v1",
        "scenario_text",
        "v1",
        "scenario_step",
        "v1",
        "Scenario Text Rubric",
        COMMON_RUBRIC_CRITERIA,
    ),
    RubricSeed(
        "interview_text@v1",
        "interview_text",
        "v1",
        "interview_prompt",
        "v1",
        "Interview Text Rubric",
        COMMON_RUBRIC_CRITERIA,
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
                    rubric_id = rubric_seed.rubric_id
                    criteria_data = [
                        {
                            "criterion_ref": criterion.criterion_ref,
                            "skill_slug": criterion.skill_slug,
                            "title": criterion.title,
                            "description": criterion.description,
                            "weight": criterion.weight,
                            "required": criterion.required,
                            "position": criterion.position,
                            "levels": [
                                {
                                    f"level_{level.level}": {
                                        "description": level.description,
                                        "examples": list(level.examples),
                                    }
                                }
                                for level in criterion.levels
                            ],
                        }
                        for criterion in rubric_seed.criteria
                    ]
                    session.add(
                        RubricRecord(
                            id=rubric_id,
                            skill_slug="general",
                            name=rubric_seed.name,
                            content_type=rubric_seed.content_type,
                            schema_version=rubric_seed.schema_version,
                        )
                    )
                    session.add(
                        RubricVersionRecord(
                            rubric_id=rubric_id,
                            version=rubric_seed.version,
                            criteria=criteria_data,
                            status="published",
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
                organisation_id="system",
            )
        )
        return self.snapshot()

    def snapshot(self, organisation_id: str | None = None) -> TaxonomySnapshot:
        with self._session_factory() as session:
            query_filters = []
            if organisation_id is not None:
                query_filters.append(
                    or_(
                        SkillRecord.organisation_id.is_(None),
                        SkillRecord.organisation_id == organisation_id,
                    )
                )
            elif organisation_id is None:
                query_filters.append(SkillRecord.organisation_id.is_(None))

            skills = [
                SkillView(
                    slug=record.slug,
                    name=record.name,
                    description=record.description,
                    organisation_id=record.organisation_id,
                )
                for record in session.query(SkillRecord)
                .filter(*query_filters)
                .order_by(SkillRecord.name)
                .all()
            ]

            if organisation_id is not None:
                org_skill_slugs = {s.slug for s in skills if s.organisation_id == organisation_id}
                canon_skill_slugs = {s.slug for s in skills if s.organisation_id is None}
                all_skill_slugs = org_skill_slugs | canon_skill_slugs

                org_maps = (
                    session.query(OrganisationSkillMapRecord)
                    .filter(OrganisationSkillMapRecord.organisation_id == organisation_id)
                    .all()
                )
                org_competency_to_skills: dict[str, list[str]] = {}
                for mapping in org_maps:
                    org_competency_to_skills.setdefault(mapping.competency_slug, []).append(
                        mapping.skill_slug
                    )

                mappings: list[CompetencySkillMapRecord] = (
                    session.query(CompetencySkillMapRecord)
                    .filter(CompetencySkillMapRecord.skill_slug.in_(all_skill_slugs))
                    .all()
                )
                canon_competency_to_skills: dict[str, list[str]] = {}
                for comp_skill_mapping in mappings:
                    canon_competency_to_skills.setdefault(
                        comp_skill_mapping.competency_slug, []
                    ).append(comp_skill_mapping.skill_slug)

                def get_skill_slugs_for_competency(comp_slug: str) -> list[str]:
                    if comp_slug in org_competency_to_skills:
                        return sorted(org_competency_to_skills[comp_slug])
                    return sorted(canon_competency_to_skills.get(comp_slug, []))

                comp_query_filters = []
                comp_query_filters.append(
                    or_(
                        CompetencyRecord.organisation_id.is_(None),
                        CompetencyRecord.organisation_id == organisation_id,
                    )
                )

                competencies = [
                    CompetencyView(
                        slug=record.slug,
                        name=record.name,
                        description=record.description,
                        skill_slugs=get_skill_slugs_for_competency(record.slug),
                        organisation_id=record.organisation_id,
                    )
                    for record in session.query(CompetencyRecord)
                    .filter(*comp_query_filters)
                    .order_by(CompetencyRecord.name)
                    .all()
                ]
            else:
                all_mappings: list[CompetencySkillMapRecord] = session.query(
                    CompetencySkillMapRecord
                ).all()
                competency_to_skills: dict[str, list[str]] = {}
                for comp_skill_mapping in all_mappings:
                    competency_to_skills.setdefault(comp_skill_mapping.competency_slug, []).append(
                        comp_skill_mapping.skill_slug
                    )
                competencies = [
                    CompetencyView(
                        slug=record.slug,
                        name=record.name,
                        description=record.description,
                        skill_slugs=sorted(competency_to_skills.get(record.slug, [])),
                        organisation_id=record.organisation_id,
                    )
                    for record in session.query(CompetencyRecord)
                    .filter(CompetencyRecord.organisation_id.is_(None))
                    .order_by(CompetencyRecord.name)
                    .all()
                ]

            rubric_filters = []
            if organisation_id is not None:
                rubric_filters.append(
                    or_(
                        RubricRecord.organisation_id.is_(None),
                        RubricRecord.organisation_id == organisation_id,
                    )
                )
            elif organisation_id is None:
                rubric_filters.append(RubricRecord.organisation_id.is_(None))

            rubrics = [
                RubricView(
                    rubric_id=record.id,
                    skill_slug=record.skill_slug,
                    content_type=record.content_type,
                    schema_version=record.schema_version,
                    name=record.name,
                    organisation_id=record.organisation_id,
                )
                for record in session.query(RubricRecord)
                .filter(*rubric_filters)
                .order_by(RubricRecord.id)
                .all()
            ]
        return TaxonomySnapshot(skills=skills, competencies=competencies, rubrics=rubrics)

    def render_prompt_context(self, organisation_id: str | None = None) -> str:
        return render_taxonomy_prompt_context(self.snapshot(organisation_id))


def render_taxonomy_prompt_context(snapshot: TaxonomySnapshot) -> str:
    skill_slugs = ", ".join(skill.slug for skill in snapshot.skills) or "none"
    sections: list[str] = [f"Skills: {skill_slugs}", "Competencies:"]
    for competency in snapshot.competencies:
        skills = ", ".join(competency.skill_slugs) if competency.skill_slugs else "none"
        sections.append(f"- {competency.slug}: [{skills}]")
    sections.append("Rules:")
    sections.append("- Use these slugs exactly when choosing skills or competencies.")
    sections.append("- Do not invent skills or competencies that are not listed above.")
    return "\n".join(sections)
