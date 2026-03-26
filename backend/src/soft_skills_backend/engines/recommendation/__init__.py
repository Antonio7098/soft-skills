"""App-agnostic recommendation engine."""

from soft_skills_backend.engines.recommendation.contracts.models import (
    CandidateItem,
    ComputedRecommendation,
    LearnerContext,
    RecommendationEngineConfig,
    RecommendationWeights,
    RecommendedCandidate,
)
from soft_skills_backend.engines.recommendation.domain.recommendation import (
    compute_recommendation,
)

__all__ = [
    "CandidateItem",
    "ComputedRecommendation",
    "LearnerContext",
    "RecommendationEngineConfig",
    "RecommendationWeights",
    "RecommendedCandidate",
    "compute_recommendation",
]
