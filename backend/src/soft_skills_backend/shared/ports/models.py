"""Ports domain models."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel, Field


@dataclass(frozen=True, slots=True)
class JsonSchemaResponseFormat:
    """Strict JSON-schema response contract for provider-backed completions."""

    name: str
    schema: dict[str, Any]
    strict: bool = True

    def normalized_schema(self) -> dict[str, Any]:
        """Return a provider-safe strict schema."""

        return normalize_strict_json_schema(self.schema)


class ProviderCompletion(BaseModel):
    """Provider response normalized for structured validation."""

    content: str | dict[str, Any]
    model_slug: str
    usage: dict[str, int] = Field(default_factory=dict)
    raw_response: dict[str, Any] = Field(default_factory=dict)


class ProviderTextChunk(BaseModel):
    """Provider text-stream chunk normalized for live token delivery."""

    delta: str
    model_slug: str | None = None
    usage: dict[str, int] = Field(default_factory=dict)
    raw_event: dict[str, Any] = Field(default_factory=dict)
    done: bool = False


@dataclass(frozen=True, slots=True)
class ProviderToolDefinition:
    """Provider-native function tool definition."""

    name: str
    description: str
    parameters: dict[str, Any]


class ProviderToolCall(BaseModel):
    """Normalized provider-native tool call."""

    call_id: str
    tool_name: str
    arguments: dict[str, Any] = Field(default_factory=dict)
    raw_tool_call: dict[str, Any] = Field(default_factory=dict)


class ProviderToolCompletion(BaseModel):
    """Provider response normalized for native tool calling."""

    content: str | None = None
    tool_calls: list[ProviderToolCall] = Field(default_factory=list)
    model_slug: str
    usage: dict[str, int] = Field(default_factory=dict)
    raw_response: dict[str, Any] = Field(default_factory=dict)


def normalize_strict_json_schema(schema: dict[str, Any]) -> dict[str, Any]:
    """Normalize a JSON schema for strict provider-side validation.

    OpenAI-compatible structured-output providers commonly require every object
    node to declare `additionalProperties: false` in strict mode.
    """

    normalized = deepcopy(schema)
    _normalize_schema_node(normalized)
    return normalized


def _normalize_schema_node(node: Any) -> None:
    if isinstance(node, dict):
        node_type = node.get("type")
        if node_type == "object":
            node.setdefault("additionalProperties", False)
            properties = node.get("properties")
            if isinstance(properties, dict):
                for value in properties.values():
                    _normalize_schema_node(value)
            additional_properties = node.get("additionalProperties")
            if isinstance(additional_properties, dict):
                _normalize_schema_node(additional_properties)
            pattern_properties = node.get("patternProperties")
            if isinstance(pattern_properties, dict):
                for value in pattern_properties.values():
                    _normalize_schema_node(value)
        elif node_type == "array":
            _normalize_schema_node(node.get("items"))

        for key in ("$defs", "definitions", "dependentSchemas", "properties"):
            child = node.get(key)
            if isinstance(child, dict):
                for value in child.values():
                    _normalize_schema_node(value)
        for key in ("allOf", "anyOf", "oneOf", "prefixItems"):
            child = node.get(key)
            if isinstance(child, list):
                for value in child:
                    _normalize_schema_node(value)
        for key in ("not", "if", "then", "else", "contains", "items"):
            _normalize_schema_node(node.get(key))
    elif isinstance(node, list):
        for value in node:
            _normalize_schema_node(value)


__all__ = [
    "JsonSchemaResponseFormat",
    "ProviderCompletion",
    "ProviderToolCall",
    "ProviderToolCompletion",
    "ProviderToolDefinition",
    "ProviderTextChunk",
    "normalize_strict_json_schema",
]
