"""Assistant runtime smoke contracts."""

from __future__ import annotations

from pydantic import BaseModel, Field


class AssistantRuntimeSmokeResult(BaseModel):
    """Result of an assistant runtime smoke flow."""

    status: str
    session_id: str
    turn_id: str
    turn_status: str
    tool_names: list[str] = Field(default_factory=list)
    message_count: int = 0
    assistant_message_preview: str | None = None
