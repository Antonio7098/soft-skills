"""App-agnostic marking engine."""

from soft_skills_backend.engines.marking.contracts.models import (
    CandidateResponse,
    CriterionJudgment,
    EvidenceReference,
    MarkingDecision,
    PromptArtifact,
    PromptContract,
    PromptTemplate,
    RenderedPrompt,
    RubricCriterion,
    RubricDefinition,
    RubricScale,
)
from soft_skills_backend.engines.marking.domain.validation import (
    validate_marking_decision,
)
from soft_skills_backend.engines.marking.use_cases.decision_builder import (
    CriterionResultInput,
    build_marking_decision,
)
from soft_skills_backend.engines.marking.use_cases.structured_output import (
    PromptLibrary,
    StructuredOutputRejectionError,
    TypedLLMOutput,
    TypedLLMResult,
)

__all__ = [
    "CandidateResponse",
    "CriterionResultInput",
    "CriterionJudgment",
    "EvidenceReference",
    "MarkingDecision",
    "PromptArtifact",
    "PromptContract",
    "PromptLibrary",
    "PromptTemplate",
    "RenderedPrompt",
    "RubricCriterion",
    "RubricDefinition",
    "RubricScale",
    "StructuredOutputRejectionError",
    "TypedLLMOutput",
    "TypedLLMResult",
    "build_marking_decision",
    "validate_marking_decision",
]
