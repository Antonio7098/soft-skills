"""Full user journey smoke contracts."""

from __future__ import annotations

from pydantic import BaseModel


class FullUserJourneySmokeResult(BaseModel):
    status: str
    user_id: str
    first_collection_id: str
    first_collection_prompt_items_count: int
    second_collection_id: str
    second_collection_prompt_items_count: int
    assistant_session_id: str
    assistant_turn_ids: list[str]
    assistant_tool_names: list[str]
    practice_run_id: str
    attempt_ids: list[str]
    skill_slugs: list[str]
    progress_snapshot_id: str | None
    organisation_id: str
    saved_collection_ids: list[str]
    global_hub_collection_ids: list[str]
