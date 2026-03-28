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


class AssistantPracticeRuntimeSmokeResult(BaseModel):
    """Result of a multi-turn assistant-facilitated practice smoke flow."""

    status: str
    session_id: str
    practice_run_id: str
    turn_ids: list[str] = Field(default_factory=list)
    tool_names: list[str] = Field(default_factory=list)
    message_count: int = 0
    assistant_message_preview: str | None = None


class AssistantStreamSmokeResult(BaseModel):
    """Result of an assistant websocket streaming smoke flow."""

    status: str
    session_id: str
    turn_id: str
    stream_token: str
    event_types: list[str]
    delta_count: int
    final_content: str | None = None
