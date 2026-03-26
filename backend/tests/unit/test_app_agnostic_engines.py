from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from soft_skills_backend.engines.config import (
    load_catalog_generation_runtime_config,
    load_marking_runtime_config,
    load_progression_engine_config,
    load_recommendation_engine_config,
)
from soft_skills_backend.engines.marking import (
    CandidateResponse,
    CriterionJudgment,
    CriterionResultInput,
    EvidenceReference,
    MarkingDecision,
    PromptContract,
    RubricCriterion,
    RubricDefinition,
    RubricScale,
    build_marking_decision,
    validate_marking_decision,
)
from soft_skills_backend.engines.progression import (
    AggregateDefinition,
    AggregateGateRule,
    AssessmentDimensionScore,
    AssessmentEvent,
    AssessmentEvidenceReference,
    ConfidenceProfileConfig,
    DecayProfileConfig,
    ProgressionEngineConfig,
    compute_progression_snapshot,
)
from soft_skills_backend.engines.recommendation import (
    CandidateItem,
    LearnerContext,
    RecommendationEngineConfig,
    RecommendationWeights,
    compute_recommendation,
)
from soft_skills_backend.shared.errors import AppError


def test_engine_configs_load_from_reviewed_json_artifacts() -> None:
    progression = load_progression_engine_config()
    recommendation = load_recommendation_engine_config()
    marking = load_marking_runtime_config()
    generation = load_catalog_generation_runtime_config()

    assert progression.config_version == "progress-config-2026-03"
    assert recommendation.config_version == "rec-config-2026-03"
    assert marking.config_version == "quick-practice-marking-config.v1"
    assert generation.config_version == "creator-generation-config.v2"
    assert generation.structured_prompt_version == "creator.collection.structured-blueprint.v2"
    assert generation.prompt_item_worker_prompt_version == "creator.prompt-item.worker.v1"
    assert generation.max_parallel_prompt_item_children == 4


def test_progression_engine_computes_dimension_and_aggregate_state() -> None:
    now = datetime(2026, 3, 25, 12, 0, tzinfo=UTC)
    config = ProgressionEngineConfig(
        engine_version="progression-engine.vtest",
        schema_version="progression-snapshot.vtest",
        evidence_ledger_schema_version="progression-ledger.vtest",
        config_version="progress-config-test",
        decay_profile=DecayProfileConfig(retention_window_days=180, minimum_weight=0.35),
        confidence_profile=ConfidenceProfileConfig(
            min_recent_evidence=2,
            min_total_evidence=3,
            recent_window_days=30,
        ),
        aggregate_gate_rules=[
            AggregateGateRule(
                aggregate_ref="aggregate-1",
                dimension_ref="dimension-weak",
                floor=0.40,
                ceiling=0.60,
            )
        ],
    )
    snapshot = compute_progression_snapshot(
        assessments=[
            AssessmentEvent(
                assessment_id="a1",
                attempt_ref="t1",
                entity_ref="learner-1",
                created_at=now - timedelta(days=7),
                prompt_version="prompt.v1",
                rubric_version="rubric.v1",
                trace_id="trace-a1",
                dimension_scores=[
                    AssessmentDimensionScore(
                        dimension_ref="dimension-weak",
                        normalized_score=0.25,
                    ),
                    AssessmentDimensionScore(
                        dimension_ref="dimension-strong",
                        normalized_score=1.0,
                    ),
                ],
                evidence=[
                    AssessmentEvidenceReference(
                        dimension_ref="dimension-weak",
                        quote="quoted response weak",
                        explanation="weak evidence",
                    ),
                    AssessmentEvidenceReference(
                        dimension_ref="dimension-strong",
                        quote="quoted response strong",
                        explanation="strong evidence",
                    ),
                ],
            ),
            AssessmentEvent(
                assessment_id="a2",
                attempt_ref="t2",
                entity_ref="learner-1",
                created_at=now - timedelta(days=1),
                prompt_version="prompt.v1",
                rubric_version="rubric.v1",
                trace_id="trace-a2",
                dimension_scores=[
                    AssessmentDimensionScore(
                        dimension_ref="dimension-weak",
                        normalized_score=0.30,
                    ),
                    AssessmentDimensionScore(
                        dimension_ref="dimension-strong",
                        normalized_score=1.0,
                    ),
                ],
                evidence=[
                    AssessmentEvidenceReference(
                        dimension_ref="dimension-weak",
                        quote="quoted response weak",
                        explanation="weak evidence",
                    ),
                    AssessmentEvidenceReference(
                        dimension_ref="dimension-strong",
                        quote="quoted response strong",
                        explanation="strong evidence",
                    ),
                ],
            ),
        ],
        dimension_refs=["dimension-strong", "dimension-weak"],
        aggregate_definitions=[
            AggregateDefinition(
                aggregate_ref="aggregate-1",
                dimension_weights={
                    "dimension-weak": 0.5,
                    "dimension-strong": 0.5,
                },
            )
        ],
        previous_state=None,
        config=config,
        now=now,
    )

    weak_dimension = next(
        state for state in snapshot.dimension_states if state.dimension_ref == "dimension-weak"
    )
    aggregate = next(
        state for state in snapshot.aggregate_states if state.aggregate_ref == "aggregate-1"
    )

    assert weak_dimension.score < 0.35
    assert weak_dimension.confidence_band == "high"
    assert "dimension-weak" in snapshot.weak_dimension_refs
    assert aggregate.gating_applied is True
    assert aggregate.score == 0.6


def test_recommendation_engine_ranks_deficit_aligned_candidate() -> None:
    now = datetime(2026, 3, 25, 12, 0, tzinfo=UTC)
    progression_config = ProgressionEngineConfig(
        engine_version="progression-engine.vtest",
        schema_version="progression-snapshot.vtest",
        evidence_ledger_schema_version="progression-ledger.vtest",
        config_version="progress-config-test",
    )
    snapshot = compute_progression_snapshot(
        assessments=[
            AssessmentEvent(
                assessment_id="a1",
                attempt_ref="t1",
                entity_ref="learner-1",
                created_at=now - timedelta(days=1),
                prompt_version="prompt.v1",
                rubric_version="rubric.v1",
                trace_id="trace-a1",
                dimension_scores=[
                    AssessmentDimensionScore(
                        dimension_ref="expectation-setting",
                        normalized_score=0.25,
                    ),
                    AssessmentDimensionScore(
                        dimension_ref="executive-summary",
                        normalized_score=0.75,
                    ),
                ],
                evidence=[
                    AssessmentEvidenceReference(
                        dimension_ref="expectation-setting",
                        quote="reset expectations directly",
                        explanation="evidence",
                    ),
                    AssessmentEvidenceReference(
                        dimension_ref="executive-summary",
                        quote="summarised concisely",
                        explanation="evidence",
                    ),
                ],
            )
        ],
        dimension_refs=["expectation-setting", "executive-summary"],
        aggregate_definitions=[],
        previous_state=None,
        config=progression_config,
        now=now,
    )
    recommendation = compute_recommendation(
        learner=LearnerContext(
            entity_ref="learner-1",
            target_role="Consulting Manager",
            goals=["Improve expectation setting with clients"],
        ),
        snapshot=snapshot,
        candidates=[
            CandidateItem(
                content_ref="content-1",
                content_type="prompt",
                collection_ref="collection-1",
                title="Reset client expectations",
                summary="Expectation setting practice for consultants.",
                difficulty="intermediate",
                verification_state="verified",
                target_dimension_refs=["expectation-setting"],
                target_aggregate_refs=["stakeholder-management"],
                lifecycle_state="published_public",
            ),
            CandidateItem(
                content_ref="content-2",
                content_type="prompt",
                collection_ref="collection-2",
                title="Write an executive briefing",
                summary="Board-ready concise summaries.",
                difficulty="intermediate",
                verification_state="verified",
                target_dimension_refs=["executive-summary"],
                target_aggregate_refs=["communication"],
                lifecycle_state="published_public",
            ),
        ],
        config=RecommendationEngineConfig(
            engine_version="recommendation-engine.vtest",
            schema_version="recommendation-output.vtest",
            config_version="recommendation-config-test",
            weights=RecommendationWeights(
                dimension_deficit_alignment=0.40,
                stagnation_relief=0.20,
                coverage_gap_fit=0.15,
                goal_alignment=0.15,
                verification_boost=0.10,
            ),
            allowed_lifecycle_states=["published_public"],
            verified_states=["verified"],
            advanced_difficulty_labels=["advanced"],
        ),
        now=now,
    )

    assert recommendation.items[0].content_ref == "content-1"
    assert "weak_dimension:expectation-setting" in recommendation.items[0].reasons
    assert any(reason.startswith("goal_match:") for reason in recommendation.items[0].reasons)


def test_marking_engine_validation_rejects_non_quoted_evidence() -> None:
    prompt = PromptContract(
        prompt_id="prompt-1",
        prompt_version="prompt.v1",
        prompt_type="free_text",
        prompt_text="Respond to the scenario",
        response_mode="text",
        rubric_id="rubric-1",
    )
    response = CandidateResponse(
        response_id="response-1",
        prompt_id="prompt-1",
        actor_id="learner-1",
        response_mode="text",
        content="I hear your concern and the earliest realistic date is Friday.",
        submitted_at=datetime(2026, 3, 25, 12, 0, tzinfo=UTC),
    )
    rubric = RubricDefinition(
        rubric_id="rubric-1",
        rubric_version="rubric.v1",
        scale=RubricScale(minimum_score=1, maximum_score=5),
        criteria=[
            RubricCriterion(
                criterion_ref="expectation-setting",
                description="Sets realistic expectations.",
            )
        ],
    )
    decision = MarkingDecision(
        marking_id="marking-1",
        response_id="response-1",
        prompt_id="prompt-1",
        prompt_version="prompt.v1",
        rubric_id="rubric-1",
        rubric_version="rubric.v1",
        engine_version="marking-engine.v1",
        provider="openai",
        model_slug="gpt-test",
        overall_score=4,
        criterion_judgments=[
            CriterionJudgment(
                criterion_ref="expectation-setting",
                score=4,
                rationale="The response sets a boundary.",
                evidence=[
                    EvidenceReference(
                        criterion_ref="expectation-setting",
                        quote="this quote does not exist",
                        explanation="unsupported evidence",
                    )
                ],
            )
        ],
        rationale="Overall this was solid.",
        strengths=["Set a clear boundary."],
        weaknesses=["Could be firmer."],
        next_actions=["Practice setting tighter checkpoints."],
        trace_id="trace-1",
        created_at=datetime(2026, 3, 25, 12, 1, tzinfo=UTC),
    )

    with pytest.raises(AppError) as excinfo:
        validate_marking_decision(
            prompt=prompt,
            response=response,
            rubric=rubric,
            decision=decision,
        )

    assert excinfo.value.code == "SS-SCORING-014"


def test_build_marking_decision_groups_evidence_by_criterion() -> None:
    prompt = PromptContract(
        prompt_id="prompt-1",
        prompt_version="prompt.v1",
        prompt_type="free_text",
        prompt_text="Respond",
        response_mode="text",
        rubric_id="rubric-1",
    )
    rubric = RubricDefinition(
        rubric_id="rubric-1",
        rubric_version="rubric.v1",
        scale=RubricScale(minimum_score=1, maximum_score=5),
        criteria=[
            RubricCriterion(
                criterion_ref="criterion-1",
                description="Criterion 1",
            )
        ],
    )

    decision = build_marking_decision(
        marking_id="marking-1",
        prompt=prompt,
        response_id="response-1",
        rubric=rubric,
        engine_version="marking-engine.v1",
        provider="openai",
        model_slug="gpt-test",
        overall_score=4,
        criterion_results=[
            CriterionResultInput(
                criterion_ref="criterion-1",
                score=4,
                rationale="Good result",
            )
        ],
        evidence=[
            EvidenceReference(
                criterion_ref="criterion-1",
                quote="quoted evidence",
                explanation="supports criterion",
            )
        ],
        rationale="Overall rationale",
        strengths=["One strength"],
        weaknesses=["One weakness"],
        next_actions=["One next action"],
        trace_id="trace-1",
        created_at=datetime(2026, 3, 25, 12, 0, tzinfo=UTC),
    )

    assert decision.criterion_judgments[0].evidence[0].quote == "quoted evidence"
