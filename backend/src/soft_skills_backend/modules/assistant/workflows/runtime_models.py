"""Assistant runtime typed-output contracts."""

from __future__ import annotations

from typing import Annotated, Any, Literal, TypeAlias

from pydantic import BaseModel, ConfigDict, Field, TypeAdapter, model_validator

from soft_skills_backend.modules.assistant.workflows.practice_facilitation import (
    StartCollectionPracticeToolArgs,
)
from soft_skills_backend.modules.catalog.contracts.collection_commands import (
    ChatCollectionGenerationCommand,
)
from soft_skills_backend.modules.catalog.contracts.prompt_item_commands import (
    ChatPromptItemGenerationCommand,
)
from soft_skills_backend.shared.ports.models import ProviderToolCall

AssistantToolName = Literal[
    "query_user_context",
    "start_collection_practice",
    "get_active_practice",
    "submit_active_practice_response",
    "end_active_practice",
    "generate_collection",
    "generate_prompt_items",
]


class _StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class AssistantSqlParamEntry(_StrictModel):
    key: str = Field(min_length=1, max_length=128)
    value: str | float | bool | None = None


class QueryUserContextToolArgs(_StrictModel):
    sql: str = Field(min_length=1, max_length=4000)
    params: list[AssistantSqlParamEntry] = Field(default_factory=list, max_length=16)


class GetActivePracticeToolArgs(_StrictModel):
    pass


class SubmitActivePracticeResponseToolArgs(_StrictModel):
    response_text: str | None = Field(default=None, max_length=12000)


class EndActivePracticeToolArgs(_StrictModel):
    pass


class GeneratePromptItemsToolArgs(ChatPromptItemGenerationCommand):
    model_config = ConfigDict(extra="forbid")

    collection_id: str = Field(min_length=1)


class _AssistantToolRequestBase(_StrictModel):
    call_id: str = Field(min_length=1, max_length=64)
    tool_name: AssistantToolName

    def arguments_payload(self) -> dict[str, Any]:
        payload = self.arguments.model_dump(mode="json", exclude_none=True)
        params = payload.get("params")
        if isinstance(params, list):
            payload["params"] = {
                str(item["key"]): item.get("value")
                for item in params
                if isinstance(item, dict) and isinstance(item.get("key"), str)
            }
        return payload


class QueryUserContextToolRequest(_AssistantToolRequestBase):
    tool_name: Literal["query_user_context"]
    arguments: QueryUserContextToolArgs


class StartCollectionPracticeToolRequest(_AssistantToolRequestBase):
    tool_name: Literal["start_collection_practice"]
    arguments: StartCollectionPracticeToolArgs


class GetActivePracticeToolRequest(_AssistantToolRequestBase):
    tool_name: Literal["get_active_practice"]
    arguments: GetActivePracticeToolArgs = Field(default_factory=GetActivePracticeToolArgs)


class SubmitActivePracticeResponseToolRequest(_AssistantToolRequestBase):
    tool_name: Literal["submit_active_practice_response"]
    arguments: SubmitActivePracticeResponseToolArgs = Field(
        default_factory=SubmitActivePracticeResponseToolArgs
    )


class EndActivePracticeToolRequest(_AssistantToolRequestBase):
    tool_name: Literal["end_active_practice"]
    arguments: EndActivePracticeToolArgs = Field(default_factory=EndActivePracticeToolArgs)


class GenerateCollectionToolRequest(_AssistantToolRequestBase):
    tool_name: Literal["generate_collection"]
    arguments: ChatCollectionGenerationCommand


class GeneratePromptItemsToolRequest(_AssistantToolRequestBase):
    tool_name: Literal["generate_prompt_items"]
    arguments: GeneratePromptItemsToolArgs


AssistantToolRequest: TypeAlias = Annotated[
    QueryUserContextToolRequest
    | StartCollectionPracticeToolRequest
    | GetActivePracticeToolRequest
    | SubmitActivePracticeResponseToolRequest
    | EndActivePracticeToolRequest
    | GenerateCollectionToolRequest
    | GeneratePromptItemsToolRequest,
    Field(discriminator="tool_name"),
]

_ASSISTANT_TOOL_REQUEST_ADAPTER = TypeAdapter(AssistantToolRequest)


class AssistantDecision(_StrictModel):
    action: Literal["tool_calls", "final_response"]
    tool_calls: list[AssistantToolRequest] = Field(default_factory=list, max_length=4)
    final_response: str | None = Field(default=None, max_length=12000)

    @model_validator(mode="after")
    def validate_action(self) -> AssistantDecision:
        if self.action == "tool_calls":
            if not self.tool_calls:
                raise ValueError("tool_calls action requires at least one tool call")
            if self.final_response and self.final_response.strip():
                raise ValueError("tool_calls action cannot include final_response")
            return self
        if not self.final_response or not self.final_response.strip():
            raise ValueError("final_response action requires final_response text")
        if self.tool_calls:
            raise ValueError("final_response action cannot include tool_calls")
        return self


def parse_assistant_tool_requests(
    tool_calls: list[ProviderToolCall],
) -> list[AssistantToolRequest]:
    """Validate provider-native tool calls against assistant tool contracts."""

    return [
        _ASSISTANT_TOOL_REQUEST_ADAPTER.validate_python(
            {
                "call_id": tool_call.call_id,
                "tool_name": tool_call.tool_name,
                "arguments": tool_call.arguments,
            }
        )
        for tool_call in tool_calls
    ]
