"""Assistant request contracts."""

from __future__ import annotations

from pydantic import BaseModel, Field


class AssistantCorrelation(BaseModel):
    request_id: str
    trace_id: str
    workflow_id: str | None = None


class CreateAssistantSessionCommand(BaseModel):
    title: str | None = Field(default=None, max_length=255)


class CreateAssistantTurnCommand(BaseModel):
    message: str = Field(min_length=1, max_length=12000)


class CancelAssistantTurnCommand(BaseModel):
    reason: str = Field(default="user_requested", min_length=1, max_length=255)


class DecideAssistantApprovalCommand(BaseModel):
    decision: str = Field(pattern="^(approved|denied)$")
    reason: str | None = Field(default=None, max_length=255)
