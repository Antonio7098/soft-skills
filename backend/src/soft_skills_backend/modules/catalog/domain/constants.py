"""Catalog application constants."""

from __future__ import annotations

ALLOWED_COLLECTION_STATES: set[str] = {
    "draft",
    "review",
    "published_private",
    "published_public",
    "archived",
}
ALLOWED_VERIFICATION_STATES: set[str] = {"unverified", "verified", "rejected"}
ALLOWED_PROMPT_TYPES: dict[str, str] = {
    "quick_practice_prompt": "quick_practice_prompt",
    "interview_prompt": "interview_prompt",
}
ALLOWED_SCENARIO_CONTENT_TYPE = "scenario_step"
ALLOWED_SCENARIO_ARTIFACT_TYPES: set[str] = {"email", "note", "report", "brief"}
ALLOWED_DIFFICULTIES: set[str] = {"introductory", "intermediate", "advanced"}
ALLOWED_COLLECTION_SOURCE_TYPES: set[str] = {
    "manual",
    "generated_structured",
    "generated_chat",
}
ALLOWED_DISCOVERY_TIERS: set[str] = {"private", "global_public", "org_public", "standard_public"}
ALLOWED_COLLECTION_TRANSITIONS: dict[str, set[str]] = {
    "draft": {"review", "published_private", "published_public", "archived"},
    "review": {"draft", "published_private", "published_public", "archived"},
    "published_private": {"review", "published_public", "archived"},
    "published_public": {"review", "archived"},
    "archived": set(),
}
