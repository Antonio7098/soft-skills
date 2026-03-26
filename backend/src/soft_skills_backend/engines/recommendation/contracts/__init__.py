"""Contracts for the recommendation engine."""

from soft_skills_backend.engines.recommendation.contracts.models import (
    CandidateItem,
    ComputedRecommendation,
    LearnerContext,
    RecommendationEngineConfig,
    RecommendationWeights,
    RecommendedCandidate,
)

__all__ = [
    "CandidateItem",
    "ComputedRecommendation",
    "LearnerContext",
    "RecommendationEngineConfig",
    "RecommendationWeights",
    "RecommendedCandidate",
]
