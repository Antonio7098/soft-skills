from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from soft_skills_backend.modules.progression.domain.progression import (
    AssessmentEvidenceSignal,
    AssessmentSignal,
    AssessmentSkillScoreSignal,
    CatalogCandidate,
    CompetencyDefinition,
    LearnerProfileInput,
    compute_progress_snapshot,
    compute_recommendation,
)
from soft_skills_backend.shared.errors import AppError


def _assessment(
    *,
    assessment_id: str,
    attempt_id: str,
    created_at: datetime,
    skill_scores: list[tuple[str, int]],
) -> AssessmentSignal:
    return AssessmentSignal(
        assessment_id=assessment_id,
        attempt_id=attempt_id,
        learner_id="learner-1",
        created_at=created_at,
        prompt_version="assessment.quick-practice.v1",
        rubric_version="v1",
        trace_id=f"trace-{assessment_id}",
        skill_scores=[
            AssessmentSkillScoreSignal(skill_slug=skill_slug, score=score)
            for skill_slug, score in skill_scores
        ],
        evidence=[
            AssessmentEvidenceSignal(
                skill_slug=skill_slug,
                quote=f"quote for {skill_slug}",
                explanation=f"evidence for {skill_slug}",
            )
            for skill_slug, _ in skill_scores
        ],
    )


def test_progress_snapshot_aggregates_confidence_and_competency_gating() -> None:
    now = datetime(2026, 3, 25, 12, 0, tzinfo=UTC)
    assessments = [
        _assessment(
            assessment_id="a1",
            attempt_id="t1",
            created_at=now - timedelta(days=10),
            skill_scores=[
                ("expectation-setting", 2),
                ("active-listening", 4),
                ("negotiation", 5),
                ("empathy", 4),
            ],
        ),
        _assessment(
            assessment_id="a2",
            attempt_id="t2",
            created_at=now - timedelta(days=2),
            skill_scores=[
                ("expectation-setting", 2),
                ("active-listening", 5),
                ("negotiation", 4),
                ("empathy", 4),
            ],
        ),
    ]

    snapshot = compute_progress_snapshot(
        assessments=assessments,
        skill_slugs=[
            "active-listening",
            "empathy",
            "expectation-setting",
            "negotiation",
        ],
        competency_definitions=[
            CompetencyDefinition(
                competency_slug="stakeholder-management",
                skill_weights={
                    "active-listening": 0.25,
                    "empathy": 0.25,
                    "expectation-setting": 0.25,
                    "negotiation": 0.25,
                },
            )
        ],
        previous_state=None,
        now=now,
    )

    expectation_setting = next(
        state for state in snapshot.skill_states if state.skill_slug == "expectation-setting"
    )
    stakeholder_management = next(
        state
        for state in snapshot.competency_states
        if state.competency_slug == "stakeholder-management"
    )

    assert expectation_setting.score < 0.35
    assert expectation_setting.confidence_band == "high"
    assert expectation_setting.recent_evidence_count == 2
    assert "expectation-setting" in snapshot.weak_skill_slugs
    assert stakeholder_management.gating_applied is True
    assert stakeholder_management.score == 0.6
    assert stakeholder_management.gating_reasons == ["expectation-setting_floor"]


def test_recommendation_prefers_weak_skill_alignment_and_goal_match() -> None:
    now = datetime(2026, 3, 25, 12, 0, tzinfo=UTC)
    snapshot = compute_progress_snapshot(
        assessments=[
            _assessment(
                assessment_id="a1",
                attempt_id="t1",
                created_at=now - timedelta(days=1),
                skill_scores=[
                    ("expectation-setting", 2),
                    ("active-listening", 4),
                ],
            )
        ],
        skill_slugs=["expectation-setting", "active-listening", "executive-summary"],
        competency_definitions=[],
        previous_state=None,
        now=now,
    )
    recommendation = compute_recommendation(
        learner=LearnerProfileInput(
            learner_id="learner-1",
            target_role="Consulting Manager",
            goals=["Improve expectation setting with clients"],
        ),
        snapshot=snapshot,
        candidates=[
            CatalogCandidate(
                content_id="content-1",
                content_type="quick_practice_prompt",
                collection_id="collection-1",
                title="Reset client expectations",
                summary="Consulting practice for stakeholder resets.",
                difficulty="intermediate",
                verification_state="verified",
                target_skill_slugs=["expectation-setting"],
                target_competency_slugs=["stakeholder-management"],
                rubric_id="quick_practice_text@v1",
                lifecycle_state="published_public",
            ),
            CatalogCandidate(
                content_id="content-2",
                content_type="quick_practice_prompt",
                collection_id="collection-2",
                title="Write an executive briefing",
                summary="Practice concise board updates.",
                difficulty="intermediate",
                verification_state="unverified",
                target_skill_slugs=["executive-summary"],
                target_competency_slugs=["communication"],
                rubric_id="quick_practice_text@v1",
                lifecycle_state="published_public",
            ),
        ],
        now=now,
    )

    assert recommendation.items[0].content_id == "content-1"
    assert "weak_skill:expectation-setting" in recommendation.items[0].reasons
    assert any(reason.startswith("goal_match:") for reason in recommendation.items[0].reasons)


def test_recommendation_fails_closed_on_empty_candidates() -> None:
    now = datetime(2026, 3, 25, 12, 0, tzinfo=UTC)
    snapshot = compute_progress_snapshot(
        assessments=[
            _assessment(
                assessment_id="a1",
                attempt_id="t1",
                created_at=now - timedelta(days=1),
                skill_scores=[("expectation-setting", 3)],
            )
        ],
        skill_slugs=["expectation-setting"],
        competency_definitions=[],
        previous_state=None,
        now=now,
    )

    with pytest.raises(AppError) as excinfo:
        compute_recommendation(
            learner=LearnerProfileInput(learner_id="learner-1"),
            snapshot=snapshot,
            candidates=[],
            now=now,
        )

    assert excinfo.value.code == "SS-VALIDATION-031"
