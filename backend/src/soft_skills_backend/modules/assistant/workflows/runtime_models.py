"""Assistant runtime typed-output contracts."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator

AssistantToolName = Literal[
    "list_collections",
    "get_collection",
    "list_recent_attempts",
    "get_attempt",
    "generate_collection",
    "generate_prompt_items",
]


class AssistantToolRequest(BaseModel):
    call_id: str = Field(min_length=1, max_length=64)
    tool_name: AssistantToolName
    arguments: dict[str, Any] = Field(default_factory=dict)


class AssistantDecision(BaseModel):
    tool_calls: list[AssistantToolRequest] = Field(default_factory=list, max_length=4)
    final_response: str | None = Field(default=None, max_length=12000)

    @model_validator(mode="after")
    def validate_action(self) -> AssistantDecision:
        has_tools = bool(self.tool_calls)
        has_response = bool(self.final_response and self.final_response.strip())
        if has_tools == has_response:
            raise ValueError("Return either tool_calls or final_response")
        return self
