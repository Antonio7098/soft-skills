"""OpenAI-compatible provider adapter used for quick practice and content generation."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from time import perf_counter
from typing import Any, cast

import httpx

from soft_skills_backend.config import Settings
from soft_skills_backend.shared.errors import AppError, provider_error, validation_error
from soft_skills_backend.shared.ports.llm import (
    LLMProvider,
    ProviderCallContext,
    ProviderCompletion,
)

TRANSIENT_PROVIDER_STATUS_CODES = {408, 429, 500, 502, 503, 504}
RETRYABLE_PROVIDER_PAYLOAD_CODES = {
    "SS-PROVIDER-007",
    "SS-PROVIDER-008",
    "SS-PROVIDER-009",
}


@dataclass(frozen=True, slots=True)
class ResolvedLLMProviderConfig:
    """Resolved provider config after applying environment fallbacks."""

    provider_name: str
    base_url: str
    api_key: str | None
    model_slug: str
    backup_model_slug: str | None = None


class OpenAICompatibleLLMProvider(LLMProvider):
    """OpenAI-compatible JSON completion adapter with retry/backoff."""

    def __init__(
        self,
        *,
        settings: Settings,
        provider_call_logger: Any,
    ) -> None:
        self._settings = settings
        self._provider_call_logger = provider_call_logger
        self._resolved = resolve_llm_provider_config(settings)

    @property
    def provider_name(self) -> str:
        return self._resolved.provider_name

    @property
    def model_slug(self) -> str:
        return self._resolved.model_slug

    def assert_configured(self) -> None:
        if not self._resolved.api_key:
            raise validation_error(
                "Provider API key is required for quick-practice assessment",
                code="SS-VALIDATION-020",
            )

    async def complete_json(
        self,
        *,
        messages: list[dict[str, str]],
        call_context: ProviderCallContext,
    ) -> ProviderCompletion:
        self.assert_configured()

        url = f"{self._resolved.base_url.rstrip('/')}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self._resolved.api_key}",
            "Content-Type": "application/json",
        }

        for attempt in range(self._settings.provider_max_retries + 1):
            active_model_slug = self._model_slug_for_attempt(attempt)
            payload = {
                "model": active_model_slug,
                "messages": messages,
                "temperature": 0,
                "response_format": {"type": "json_object"},
            }
            call_id = await self._provider_call_logger.log_call_start(
                operation=call_context.operation,
                provider=self._resolved.provider_name,
                model_id=active_model_slug,
                pipeline_run_id=call_context.pipeline_run_id,
                request_id=call_context.request_id,
                trace_id=call_context.trace_id,
                workflow_id=call_context.workflow_id,
                user_id=call_context.user_id,
            )
            start = perf_counter()
            try:
                async with asyncio.timeout(self._settings.smoke_timeout_seconds):
                    async with httpx.AsyncClient(
                        timeout=self._settings.smoke_timeout_seconds
                    ) as client:
                        response = await client.post(url, headers=headers, json=payload)
                latency_ms = int((perf_counter() - start) * 1000)
                response_payload = response.json()
                if response.status_code >= 400:
                    error_message = _provider_error_message(response_payload)
                    await self._provider_call_logger.log_call_end(
                        call_id,
                        success=False,
                        latency_ms=latency_ms,
                        error=error_message,
                        operation=call_context.operation,
                        provider=self._resolved.provider_name,
                        model_id=active_model_slug,
                        pipeline_run_id=call_context.pipeline_run_id,
                        request_id=call_context.request_id,
                        trace_id=call_context.trace_id,
                        workflow_id=call_context.workflow_id,
                        user_id=call_context.user_id,
                        http_status=response.status_code,
                    )
                    if (
                        response.status_code in TRANSIENT_PROVIDER_STATUS_CODES
                        and attempt < self._settings.provider_max_retries
                    ):
                        await asyncio.sleep(
                            self._settings.provider_retry_backoff_seconds * (attempt + 1)
                        )
                        continue
                    raise provider_error(
                        "Provider completion request failed",
                        code="SS-PROVIDER-004",
                        details={
                            "status_code": response.status_code,
                            "reason": error_message,
                        },
                    )
                content = _extract_message_content(response_payload)
                usage = _extract_usage(response_payload)
                await self._provider_call_logger.log_call_end(
                    call_id,
                    success=True,
                    latency_ms=latency_ms,
                    operation=call_context.operation,
                    provider=self._resolved.provider_name,
                    model_id=active_model_slug,
                    pipeline_run_id=call_context.pipeline_run_id,
                    request_id=call_context.request_id,
                    trace_id=call_context.trace_id,
                    workflow_id=call_context.workflow_id,
                    user_id=call_context.user_id,
                    usage=usage,
                )
                return ProviderCompletion(
                    content=content,
                    model_slug=str(response_payload.get("model", active_model_slug)),
                    usage=usage,
                    raw_response=response_payload,
                )
            except AppError as exc:
                latency_ms = int((perf_counter() - start) * 1000)
                await self._provider_call_logger.log_call_end(
                    call_id,
                    success=False,
                    latency_ms=latency_ms,
                    error=str(exc),
                    operation=call_context.operation,
                    provider=self._resolved.provider_name,
                    model_id=active_model_slug,
                    pipeline_run_id=call_context.pipeline_run_id,
                    request_id=call_context.request_id,
                    trace_id=call_context.trace_id,
                    workflow_id=call_context.workflow_id,
                    user_id=call_context.user_id,
                )
                if exc.code in RETRYABLE_PROVIDER_PAYLOAD_CODES and attempt < self._settings.provider_max_retries:
                    await asyncio.sleep(
                        self._settings.provider_retry_backoff_seconds * (attempt + 1)
                    )
                    continue
                raise
            except TimeoutError as exc:
                latency_ms = int((perf_counter() - start) * 1000)
                timeout_error = "Provider completion request exceeded the configured timeout budget"
                await self._provider_call_logger.log_call_end(
                    call_id,
                    success=False,
                    latency_ms=latency_ms,
                    error=timeout_error,
                    operation=call_context.operation,
                    provider=self._resolved.provider_name,
                    model_id=active_model_slug,
                    pipeline_run_id=call_context.pipeline_run_id,
                    request_id=call_context.request_id,
                    trace_id=call_context.trace_id,
                    workflow_id=call_context.workflow_id,
                    user_id=call_context.user_id,
                )
                if attempt < self._settings.provider_max_retries:
                    await asyncio.sleep(
                        self._settings.provider_retry_backoff_seconds * (attempt + 1)
                    )
                    continue
                raise provider_error(
                    "Provider completion request failed",
                    code="SS-PROVIDER-005",
                    details={
                        "reason": timeout_error,
                        "timeout_seconds": self._settings.smoke_timeout_seconds,
                        "url": url,
                    },
                ) from exc
            except httpx.HTTPError as exc:
                latency_ms = int((perf_counter() - start) * 1000)
                await self._provider_call_logger.log_call_end(
                    call_id,
                    success=False,
                    latency_ms=latency_ms,
                    error=str(exc),
                    operation=call_context.operation,
                    provider=self._resolved.provider_name,
                    model_id=active_model_slug,
                    pipeline_run_id=call_context.pipeline_run_id,
                    request_id=call_context.request_id,
                    trace_id=call_context.trace_id,
                    workflow_id=call_context.workflow_id,
                    user_id=call_context.user_id,
                )
                if attempt < self._settings.provider_max_retries:
                    await asyncio.sleep(
                        self._settings.provider_retry_backoff_seconds * (attempt + 1)
                    )
                    continue
                raise provider_error(
                    "Provider completion request failed",
                    code="SS-PROVIDER-005",
                    details={"reason": str(exc), "url": url},
                ) from exc

        raise provider_error(
            "Provider completion request exhausted retries",
            code="SS-PROVIDER-006",
        )

    def _model_slug_for_attempt(self, attempt: int) -> str:
        if self._resolved.backup_model_slug and attempt >= 2:
            return self._resolved.backup_model_slug
        return self._resolved.model_slug


def resolve_llm_provider_config(settings: Settings) -> ResolvedLLMProviderConfig:
    """Resolve provider details, including OpenRouter environment aliases."""

    provider_name = settings.provider_name
    base_url = settings.provider_base_url
    api_key = settings.provider_api_key
    model_slug = settings.provider_model_slug

    if settings.llm_marking_model:
        model_slug = settings.llm_marking_model
    backup_model_slug = settings.llm_marking_model_backup

    if api_key is None and settings.openrouter_api_key:
        api_key = settings.openrouter_api_key
        if provider_name == "openai":
            provider_name = "openrouter"
        if base_url == "https://api.openai.com/v1":
            base_url = settings.openrouter_base_url
        if settings.llm_marking_model:
            model_slug = settings.llm_marking_model

    return ResolvedLLMProviderConfig(
        provider_name=provider_name,
        base_url=base_url,
        api_key=api_key,
        model_slug=model_slug,
        backup_model_slug=backup_model_slug,
    )


def _extract_message_content(payload: dict[str, Any]) -> str | dict[str, Any]:
    choices = payload.get("choices")
    if not isinstance(choices, list) or not choices:
        raise provider_error(
            "Provider completion response did not include choices",
            code="SS-PROVIDER-007",
        )
    message = choices[0].get("message")
    if not isinstance(message, dict):
        raise provider_error(
            "Provider completion response did not include a message",
            code="SS-PROVIDER-008",
        )
    content = message.get("content")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        text_parts = [
            str(item.get("text"))
            for item in content
            if isinstance(item, dict)
            and item.get("type") == "text"
            and item.get("text") is not None
        ]
        return "".join(text_parts)
    if isinstance(content, dict):
        return cast(dict[str, Any], content)
    raise provider_error(
        "Provider completion response content was not understood",
        code="SS-PROVIDER-009",
        details={
            "content_type": type(content).__name__,
            "message_keys": sorted(str(key) for key in message.keys()),
        },
    )


def _extract_usage(payload: dict[str, Any]) -> dict[str, int]:
    usage = payload.get("usage")
    if not isinstance(usage, dict):
        return {}
    return {
        key: int(value)
        for key, value in usage.items()
        if key in {"prompt_tokens", "completion_tokens", "total_tokens"} and value is not None
    }


def _provider_error_message(payload: dict[str, Any]) -> str:
    error = payload.get("error")
    if isinstance(error, dict):
        message = error.get("message")
        if isinstance(message, str) and message.strip():
            return message
    message = payload.get("message")
    if isinstance(message, str) and message.strip():
        return message
    return "Provider returned an error response"
