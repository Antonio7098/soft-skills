"""App-agnostic progression engine."""

from soft_skills_backend.engines.progression.contracts.models import (
    AggregateDefinition,
    AggregateGateRule,
    AggregateState,
    AssessmentDimensionScore,
    AssessmentEvent,
    AssessmentEvidenceReference,
    ComputedProgressionSnapshot,
    ConfidenceProfileConfig,
    DecayProfileConfig,
    DimensionContribution,
    DimensionState,
    PriorProgressState,
    ProgressionEngineConfig,
)
from soft_skills_backend.engines.progression.domain.progression import (
    compute_progression_snapshot,
    diff_summary,
)

__all__ = [
    "AggregateDefinition",
    "AggregateGateRule",
    "AggregateState",
    "AssessmentDimensionScore",
    "AssessmentEvent",
    "AssessmentEvidenceReference",
    "ComputedProgressionSnapshot",
    "ConfidenceProfileConfig",
    "DecayProfileConfig",
    "DimensionContribution",
    "DimensionState",
    "PriorProgressState",
    "ProgressionEngineConfig",
    "compute_progression_snapshot",
    "diff_summary",
]
