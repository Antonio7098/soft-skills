"""Admin-agent request contracts."""

from __future__ import annotations

from typing import TypeAlias

from pydantic import BaseModel, Field, field_validator

AdminAgentScalar: TypeAlias = str | int | float | bool | None


class AdminAgentCorrelation(BaseModel):
    request_id: str
    trace_id: str
    workflow_id: str | None = None


class QueryAdminDataCommand(BaseModel):
    sql: str = Field(min_length=1, max_length=4000)
    params: dict[str, AdminAgentScalar] = Field(default_factory=dict)

    @field_validator("sql")
    @classmethod
    def _strip_sql(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("SQL must not be blank")
        return normalized


class AdminAgentChatCommand(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    conversation_id: str | None = Field(default=None, min_length=8, max_length=64)

    @field_validator("message")
    @classmethod
    def _strip_message(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Message must not be blank")
        return normalized

    @field_validator("conversation_id")
    @classmethod
    def _normalize_conversation_id(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None
