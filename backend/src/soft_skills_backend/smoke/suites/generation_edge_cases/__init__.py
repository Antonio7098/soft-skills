"""Generation edge case smoke suites."""

from .contracts import (
    GenerationEdgeCaseSmokeResult,
    GenerationEmptyCountsSmokeResult,
    GenerationInvalidSkillSlugSmokeResult,
    GenerationLongPromptSmokeResult,
    GenerationMultipleCollectionsSmokeResult,
    GenerationSpecialCharsPromptSmokeResult,
)
from .smoke import (
    GenerationEmptyCountsSmoke,
    GenerationInvalidSkillSlugSmoke,
    GenerationLongPromptSmoke,
    GenerationMultipleCollectionsSmoke,
    GenerationSpecialCharsPromptSmoke,
)

__all__ = [
    "GenerationEdgeCaseSmokeResult",
    "GenerationEmptyCountsSmoke",
    "GenerationEmptyCountsSmokeResult",
    "GenerationInvalidSkillSlugSmoke",
    "GenerationInvalidSkillSlugSmokeResult",
    "GenerationLongPromptSmoke",
    "GenerationLongPromptSmokeResult",
    "GenerationMultipleCollectionsSmoke",
    "GenerationMultipleCollectionsSmokeResult",
    "GenerationSpecialCharsPromptSmoke",
    "GenerationSpecialCharsPromptSmokeResult",
]
