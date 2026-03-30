"""Admin-agent smoke contracts."""

from __future__ import annotations

from pydantic import BaseModel


class AdminAgentSmokeResult(BaseModel):
    conversation_id: str
    organisation_id: str
    session_row_count: int
    source_view_count: int
    message_preview: str
