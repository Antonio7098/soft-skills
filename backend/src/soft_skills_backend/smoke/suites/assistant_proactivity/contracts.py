"""Assistant proactivity smoke contracts."""

from __future__ import annotations

from pydantic import BaseModel, Field


class AssistantProactivitySmokeResult(BaseModel):
    """Result of an assistant proactivity under ambiguity smoke flow."""

    status: str
    session_id: str
    turn_id: str
    turn_status: str
    tool_names: list[str] = Field(default_factory=list)
    message_count: int = 0
    assistant_message_preview: str | None = None
    last_error_code: str | None = None
    ambiguous_message: str
