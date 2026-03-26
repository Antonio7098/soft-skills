"""Reusable prompt rendering and typed-output helpers for engine-backed marking."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, TypeVar, cast

from pydantic import BaseModel, ValidationError

from soft_skills_backend.engines.marking.contracts.models import (
    PromptTemplate,
    RenderedPrompt,
)
from soft_skills_backend.shared.errors import AppError, validation_error
from soft_skills_backend.shared.ports.llm import LLMProvider
from soft_skills_backend.shared.ports.telemetry import ProviderCallContext

ModelT = TypeVar("ModelT", bound=BaseModel)


@dataclass(slots=True)
class TypedLLMResult:
    """Validated typed model output."""

    parsed: BaseModel
    raw_payload: dict[str, Any]
    schema_version: str
    usage: dict[str, int]
    model_slug: str


@dataclass(slots=True)
class StructuredOutputRejectionError(Exception):
    """Raised when a provider returned data that must be rejected."""

    app_error: AppError
    raw_payload: dict[str, Any]


class PromptLibrary:
    """Small versioned prompt registry."""

    def __init__(self) -> None:
        self._templates: dict[tuple[str, str], PromptTemplate] = {}
        self._defaults: dict[str, str] = {}

    def register(self, template: PromptTemplate, *, make_default: bool = False) -> None:
        self._templates[(template.name, template.version)] = template
        if make_default or template.name not in self._defaults:
            self._defaults[template.name] = template.version

    def render(
        self,
        name: str,
        *,
        variables: dict[str, object],
        version: str | None = None,
    ) -> RenderedPrompt:
        resolved_version = version or self._defaults.get(name)
        if resolved_version is None:
            raise validation_error(
                "Prompt library default version was not found",
                code="SS-VALIDATION-017",
                details={"prompt_name": name},
            )
        template = self._templates.get((name, resolved_version))
        if template is None:
            raise validation_error(
                "Prompt library template was not found",
                code="SS-VALIDATION-018",
                details={"prompt_name": name, "prompt_version": resolved_version},
            )
        return RenderedPrompt(
            name=template.name,
            version=template.version,
            content=template.template.format(**variables),
        )


class TypedLLMOutput:
    """Pydantic-backed typed output parser with bounded corrective retries."""

    def __init__(
        self,
        model_type: type[ModelT],
        *,
        schema_version: str,
        max_validation_retries: int,
    ) -> None:
        self._model_type = model_type
        self._schema_version = schema_version
        self._max_validation_retries = max_validation_retries

    async def generate(
        self,
        provider: LLMProvider,
        *,
        messages: list[dict[str, str]],
        call_context: ProviderCallContext,
    ) -> TypedLLMResult:
        retry_messages = list(messages)
        last_payload: dict[str, Any] = {}
        for attempt in range(self._max_validation_retries + 1):
            completion = await provider.complete_json(
                messages=retry_messages,
                call_context=call_context,
            )
            try:
                payload = _coerce_json_payload(completion.content)
                last_payload = payload
                parsed = self._model_type.model_validate(payload)
                return TypedLLMResult(
                    parsed=parsed,
                    raw_payload=payload,
                    schema_version=self._schema_version,
                    usage=completion.usage,
                    model_slug=completion.model_slug,
                )
            except (json.JSONDecodeError, ValidationError) as exc:
                if attempt >= self._max_validation_retries:
                    raise StructuredOutputRejectionError(
                        app_error=validation_error(
                            "Provider returned malformed structured output",
                            code="SS-VALIDATION-019",
                            details={"reason": str(exc)},
                        ),
                        raw_payload=last_payload,
                    ) from exc
                retry_messages = [
                    *messages,
                    {
                        "role": "assistant",
                        "content": _stringify_provider_content(completion.content),
                    },
                    {
                        "role": "user",
                        "content": (
                            "Return JSON only. The previous output was invalid. "
                            f"Fix the schema issues: {exc}"
                        ),
                    },
                ]
        raise StructuredOutputRejectionError(
            app_error=validation_error(
                "Provider returned malformed structured output",
                code="SS-VALIDATION-019",
            ),
            raw_payload=last_payload,
        )


def _coerce_json_payload(content: str | dict[str, Any]) -> dict[str, Any]:
    if isinstance(content, dict):
        return content
    parsed = json.loads(content)
    if isinstance(parsed, dict):
        return cast(dict[str, Any], parsed)
    raise json.JSONDecodeError("Expected a JSON object", content, 0)


def _stringify_provider_content(content: str | dict[str, Any]) -> str:
    if isinstance(content, str):
        return content
    return json.dumps(content)
