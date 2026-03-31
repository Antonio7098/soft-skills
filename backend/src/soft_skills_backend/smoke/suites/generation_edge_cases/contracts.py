"""Generation edge case smoke result contracts."""

from __future__ import annotations

from pydantic import BaseModel


class GenerationEdgeCaseSmokeResult(BaseModel):
    """Result of generation edge case smoke suite."""

    status: str
    test_name: str
    generation_mode: str | None = None
    collection_id: str | None = None
    prompt_items_count: int | None = None
    error_code: str | None = None
    error_details: dict | None = None


class GenerationLongPromptSmokeResult(GenerationEdgeCaseSmokeResult):
    """Result for long prompt edge case test."""


class GenerationSpecialCharsPromptSmokeResult(GenerationEdgeCaseSmokeResult):
    """Result for special characters in prompt edge case test."""


class GenerationInvalidSkillSlugSmokeResult(GenerationEdgeCaseSmokeResult):
    """Result for invalid skill slug edge case test."""


class GenerationEmptyCountsSmokeResult(GenerationEdgeCaseSmokeResult):
    """Result for empty counts edge case test."""


class GenerationMultipleCollectionsSmokeResult(GenerationEdgeCaseSmokeResult):
    """Result for multiple rapid collections generation test."""
