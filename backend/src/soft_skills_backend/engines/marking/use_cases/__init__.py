"""Use cases for the marking engine."""

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
    "CriterionResultInput",
    "PromptLibrary",
    "StructuredOutputRejectionError",
    "TypedLLMOutput",
    "TypedLLMResult",
    "build_marking_decision",
]
