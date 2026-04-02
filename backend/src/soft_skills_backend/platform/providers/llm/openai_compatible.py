"""OpenAI-compatible provider adapters for various LLM backends."""

from __future__ import annotations

import asyncio
import json
import logging
from abc import abstractmethod
from collections.abc import AsyncIterator
from dataclasses import dataclass
from time import perf_counter
from typing import Any, ClassVar, cast

import httpx

from soft_skills_backend.config import LLMTaskKind, Settings
from soft_skills_backend.shared.errors import AppError, provider_error, validation_error
from soft_skills_backend.shared.ports.llm import (
    LLMProvider,
    ProviderCallContext,
    ProviderCompletion,
    ProviderToolCompletion,
    ProviderToolDefinition,
    ProviderTextChunk,
)
from soft_skills_backend.shared.ports.models import (
    JsonSchemaResponseFormat,
    ProviderToolCall,
)

TRANSIENT_PROVIDER_STATUS_CODES = {408, 429, 500, 502, 503, 504}
RETRYABLE_PROVIDER_PAYLOAD_CODES = {
    "SS-PROVIDER-007",
    "SS-PROVIDER-008",
    "SS-PROVIDER-009",
}
RETRYABLE_STRUCTURED_OUTPUT_FAILURE_MARKERS = (
    "failed to validate json",
    "failed to generate json",
)

logger = logging.getLogger(__name__)


def _add_llm_span_attributes(
    operation: str,
    provider: str,
    model_slug: str | None = None,
    usage: dict[str, int] | None = None,
) -> None:
    """Add LLM-specific attributes to the current OpenTelemetry span if available."""
    try:
        from opentelemetry import trace

        span = trace.get_current_span()
        if span is None:
            return
        span.set_attribute("llm.operation", operation)
        span.set_attribute("llm.provider", provider)
        if model_slug:
            span.set_attribute("llm.model", model_slug)
        if usage:
            if usage.get("prompt_tokens"):
                span.set_attribute("llm.tokens.prompt", usage["prompt_tokens"])
            if usage.get("completion_tokens"):
                span.set_attribute("llm.tokens.completion", usage["completion_tokens"])
            if usage.get("total_tokens"):
                span.set_attribute("llm.tokens.total", usage["total_tokens"])
    except ImportError:
        pass


def _is_retryable_structured_output_failure(
    *,
    status_code: int,
    error_message: str,
) -> bool:
    if status_code != 400:
        return False
    lowered = error_message.lower()
    return any(marker in lowered for marker in RETRYABLE_STRUCTURED_OUTPUT_FAILURE_MARKERS)


@dataclass(frozen=True, slots=True)
class ResolvedLLMProviderConfig:
    """Resolved provider config after applying environment fallbacks."""

    provider_name: str
    base_url: str
    api_key: str | None
    model_slug: str
    backup_model_slug: str | None = None


class OpenAICompatibleLLMProvider(LLMProvider):
    """OpenAI-compatible JSON completion adapter with retry/backoff.

    This is an abstract base class. Use build_llm_provider() factory to get
    the appropriate concrete implementation for your provider.
    """

    provider_name: ClassVar[str] = "openai-compatible"
    base_url: ClassVar[str] = "https://api.openai.com/v1"
    default_model_slug: ClassVar[str] = "gpt-4o"
    backup_model_slug: ClassVar[str | None] = None
    supports_structured_outputs: ClassVar[bool] = True

    def __init__(
        self,
        *,
        settings: Settings,
        provider_call_logger: Any,
        task: LLMTaskKind | None = None,
    ) -> None:
        self._settings = settings
        self._provider_call_logger = provider_call_logger
        self._task = task
        self._resolved = self._resolve_config(settings, task)
        self._complete_json_attempt_counts: dict[tuple[str, ...], int] = {}

    def _resolve_config(
        self,
        settings: Settings,
        task: LLMTaskKind | None,
    ) -> ResolvedLLMProviderConfig:
        api_key = self._get_api_key(settings)
        base_url = self._get_base_url(settings)
        model_slug = self._get_model_slug(settings, task)
        backup = self._get_backup_model_slug(settings)
        provider_name = self._resolve_provider_name(settings)
        return ResolvedLLMProviderConfig(
            provider_name=provider_name,
            base_url=base_url,
            api_key=api_key,
            model_slug=model_slug,
            backup_model_slug=backup,
        )

    def _resolve_provider_name(self, settings: Settings) -> str:
        if self.provider_name == "openai-compatible":
            return settings.provider_name
        return self.provider_name

    def _get_api_key(self, settings: Settings) -> str | None:
        return settings.provider_api_key

    def _get_base_url(self, settings: Settings) -> str:
        return settings.provider_base_url

    def _get_model_slug(self, settings: Settings, task: LLMTaskKind | None) -> str:
        if task is not None:
            model = self._get_task_model(settings, task)
            if model:
                return model
        elif settings.llm_marking_per_skill_model:
            return settings.llm_marking_per_skill_model
        return settings.llm_default_model or self.default_model_slug

    def _get_task_model(self, settings: Settings, task: LLMTaskKind) -> str | None:
        return None

    def _get_backup_model_slug(self, settings: Settings) -> str | None:
        return settings.llm_default_backup_model or self.backup_model_slug

    @property
    def provider_name_prop(self) -> str:
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
        messages: list[dict[str, object]],
        call_context: ProviderCallContext,
        response_schema: JsonSchemaResponseFormat | None = None,
        timeout_seconds: float | None = None,
    ) -> ProviderCompletion:
        self.assert_configured()

        url = f"{self._resolved.base_url.rstrip('/')}/chat/completions"
        resolved_timeout_seconds = timeout_seconds or self._settings.smoke_timeout_seconds

        headers = {
            "Authorization": f"Bearer {self._resolved.api_key}",
            "Content-Type": "application/json",
        }
        max_retries = self._max_retries()
        attempt_key = self._complete_json_attempt_key(call_context)
        starting_attempt = (
            self._complete_json_attempt_counts.get(attempt_key, 0) if attempt_key is not None else 0
        )
        attempts_used = 0

        try:
            for attempt in range(max_retries + 1):
                attempts_used = attempt + 1
                active_model_slug = self._model_slug_for_attempt(starting_attempt + attempt)
                payload = {
                    "model": active_model_slug,
                    "messages": messages,
                    "temperature": 0,
                    "response_format": _build_json_response_format(
                        response_schema,
                        provider_name=self._resolved.provider_name,
                    ),
                }
                provider_preferences = _build_provider_preferences(
                    provider_name=self._resolved.provider_name,
                    response_schema=response_schema,
                )
                if provider_preferences is not None:
                    payload["provider"] = provider_preferences
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
                response_payload: dict[str, Any] | None = None
                try:
                    from httpx import Timeout

                    timeout_config = Timeout(
                        resolved_timeout_seconds,
                        connect=min(5.0, resolved_timeout_seconds),
                        read=resolved_timeout_seconds,
                        write=min(5.0, resolved_timeout_seconds),
                    )
                    async with asyncio.timeout(resolved_timeout_seconds):
                        async with httpx.AsyncClient(timeout=timeout_config) as client:
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
                            timeout_seconds=resolved_timeout_seconds,
                            response_format_type=str(
                                cast(dict[str, object], payload["response_format"])["type"]
                            ),
                        )
                        if (
                            _is_retryable_structured_output_failure(
                                status_code=response.status_code,
                                error_message=error_message,
                            )
                            and attempt < max_retries
                        ):
                            await asyncio.sleep(
                                self._settings.provider_retry_backoff_seconds * (attempt + 1)
                            )
                            continue
                        if (
                            response.status_code in TRANSIENT_PROVIDER_STATUS_CODES
                            and attempt < max_retries
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
                    finish_reason = _extract_finish_reason(response_payload)
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
                        finish_reason=finish_reason,
                        timeout_seconds=resolved_timeout_seconds,
                        response_format_type=str(
                            cast(dict[str, object], payload["response_format"])["type"]
                        ),
                    )
                    _add_llm_span_attributes(
                        operation=call_context.operation,
                        provider=self._resolved.provider_name,
                        model_slug=active_model_slug,
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
                    persisted_error = (
                        str(exc.details.get("reason"))
                        if exc.details and isinstance(exc.details.get("reason"), str)
                        else str(exc)
                    )
                    await self._provider_call_logger.log_call_end(
                        call_id,
                        success=False,
                        latency_ms=latency_ms,
                        error=persisted_error,
                        operation=call_context.operation,
                        provider=self._resolved.provider_name,
                        model_id=active_model_slug,
                        pipeline_run_id=call_context.pipeline_run_id,
                        request_id=call_context.request_id,
                        trace_id=call_context.trace_id,
                        workflow_id=call_context.workflow_id,
                        user_id=call_context.user_id,
                        timeout_seconds=resolved_timeout_seconds,
                        response_format_type=str(
                            cast(dict[str, object], payload["response_format"])["type"]
                        ),
                        error_code=exc.code,
                        response_diagnostics=_build_response_diagnostics(response_payload),
                    )
                    if exc.code in RETRYABLE_PROVIDER_PAYLOAD_CODES and attempt < max_retries:
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
                    if attempt < max_retries:
                        await asyncio.sleep(
                            self._settings.provider_retry_backoff_seconds * (attempt + 1)
                        )
                        continue
                    raise provider_error(
                        "Provider completion request failed",
                        code="SS-PROVIDER-005",
                        details={
                            "reason": timeout_error,
                            "timeout_seconds": resolved_timeout_seconds,
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
                        timeout_seconds=resolved_timeout_seconds,
                        response_format_type=str(
                            cast(dict[str, object], payload["response_format"])["type"]
                        ),
                    )
                    if attempt < max_retries:
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
        finally:
            self._record_complete_json_attempts(
                attempt_key=attempt_key,
                starting_attempt=starting_attempt,
                attempts_used=attempts_used,
            )

    async def complete_with_tools(
        self,
        *,
        messages: list[dict[str, object]],
        tools: list[ProviderToolDefinition],
        call_context: ProviderCallContext,
        timeout_seconds: float | None = None,
        tool_choice: str | None = None,
    ) -> ProviderToolCompletion:
        self.assert_configured()

        url = f"{self._resolved.base_url.rstrip('/')}/chat/completions"
        resolved_timeout_seconds = timeout_seconds or self._settings.smoke_timeout_seconds
        headers = {
            "Authorization": f"Bearer {self._resolved.api_key}",
            "Content-Type": "application/json",
        }
        max_retries = self._max_retries()

        for attempt in range(max_retries + 1):
            active_model_slug = self._model_slug_for_attempt(attempt)
            provider_tools = [_build_provider_tool_definition(tool) for tool in tools]
            payload: dict[str, Any] = {
                "model": active_model_slug,
                "messages": messages,
                "temperature": 0,
                "tools": provider_tools,
                "parallel_tool_calls": True,
            }
            if tool_choice is not None:
                payload["tool_choice"] = {
                    "type": "function",
                    "function": {"name": tool_choice},
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
            response_payload: dict[str, Any] | None = None
            tool_payload_diagnostics = _build_tool_payload_diagnostics(
                tools=tools,
                provider_tools=provider_tools,
                messages=messages,
                tool_choice=tool_choice,
            )
            try:
                # Use explicit httpx timeout configuration to ensure proper timeout handling
                from httpx import Timeout
                timeout_config = Timeout(
                    resolved_timeout_seconds,
                    connect=min(5.0, resolved_timeout_seconds),
                    read=resolved_timeout_seconds,
                    write=min(5.0, resolved_timeout_seconds),
                )
                async with asyncio.timeout(resolved_timeout_seconds):
                    async with httpx.AsyncClient(timeout=timeout_config) as client:
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
                        timeout_seconds=resolved_timeout_seconds,
                        tool_payload_diagnostics=tool_payload_diagnostics,
                        provider_response_diagnostics=_build_response_diagnostics(response_payload),
                    )
                    logger.warning(
                        "Provider tool request failed",
                        extra={
                            "provider": self._resolved.provider_name,
                            "model": active_model_slug,
                            "status_code": response.status_code,
                            "operation": call_context.operation,
                            "tool_payload_diagnostics": tool_payload_diagnostics,
                            "provider_response_diagnostics": _build_response_diagnostics(
                                response_payload
                            ),
                            "error_message": error_message,
                        },
                    )
                    if (
                        response.status_code in TRANSIENT_PROVIDER_STATUS_CODES
                        and attempt < max_retries
                    ):
                        await asyncio.sleep(
                            self._settings.provider_retry_backoff_seconds * (attempt + 1)
                        )
                        continue
                    raise provider_error(
                        "Provider tool request failed",
                        code="SS-PROVIDER-004",
                        details={
                            "status_code": response.status_code,
                            "reason": error_message,
                            "tool_payload_diagnostics": tool_payload_diagnostics,
                            "provider_response_diagnostics": _build_response_diagnostics(
                                response_payload
                            ),
                        },
                    )
                message = _extract_provider_message(response_payload)
                content = _extract_provider_message_text(message)
                provider_tool_calls = _extract_provider_tool_calls(message)
                usage = _extract_usage(response_payload)
                finish_reason = _extract_finish_reason(response_payload)
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
                    finish_reason=finish_reason,
                    timeout_seconds=resolved_timeout_seconds,
                    tool_payload_diagnostics=tool_payload_diagnostics,
                )
                _add_llm_span_attributes(
                    operation=call_context.operation,
                    provider=self._resolved.provider_name,
                    model_slug=active_model_slug,
                    usage=usage,
                )
                return ProviderToolCompletion(
                    content=content,
                    tool_calls=provider_tool_calls,
                    model_slug=str(response_payload.get("model", active_model_slug)),
                    usage=usage,
                    raw_response=response_payload,
                )
            except AppError as exc:
                latency_ms = int((perf_counter() - start) * 1000)
                persisted_error = (
                    str(exc.details.get("reason"))
                    if exc.details and isinstance(exc.details.get("reason"), str)
                    else str(exc)
                )
                await self._provider_call_logger.log_call_end(
                    call_id,
                    success=False,
                    latency_ms=latency_ms,
                    error=persisted_error,
                    operation=call_context.operation,
                    provider=self._resolved.provider_name,
                    model_id=active_model_slug,
                    pipeline_run_id=call_context.pipeline_run_id,
                    request_id=call_context.request_id,
                    trace_id=call_context.trace_id,
                    workflow_id=call_context.workflow_id,
                    user_id=call_context.user_id,
                    timeout_seconds=resolved_timeout_seconds,
                    error_code=exc.code,
                    response_diagnostics=_build_response_diagnostics(response_payload),
                )
                if exc.code in RETRYABLE_PROVIDER_PAYLOAD_CODES and attempt < max_retries:
                    await asyncio.sleep(
                        self._settings.provider_retry_backoff_seconds * (attempt + 1)
                    )
                    continue
                raise
            except TimeoutError as exc:
                latency_ms = int((perf_counter() - start) * 1000)
                timeout_error = "Provider tool request exceeded the configured timeout budget"
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
                if attempt < max_retries:
                    await asyncio.sleep(
                        self._settings.provider_retry_backoff_seconds * (attempt + 1)
                    )
                    continue
                raise provider_error(
                    "Provider tool request failed",
                    code="SS-PROVIDER-005",
                    details={
                        "reason": timeout_error,
                        "timeout_seconds": resolved_timeout_seconds,
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
                    timeout_seconds=resolved_timeout_seconds,
                )
                if attempt < max_retries:
                    await asyncio.sleep(
                        self._settings.provider_retry_backoff_seconds * (attempt + 1)
                    )
                    continue
                raise provider_error(
                    "Provider tool request failed",
                    code="SS-PROVIDER-005",
                    details={"reason": str(exc), "url": url},
                ) from exc

        raise provider_error(
            "Provider tool request exhausted retries",
            code="SS-PROVIDER-006",
        )

    async def stream_text(
        self,
        *,
        messages: list[dict[str, object]],
        call_context: ProviderCallContext,
    ) -> AsyncIterator[ProviderTextChunk]:
        self.assert_configured()

        url = f"{self._resolved.base_url.rstrip('/')}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self._resolved.api_key}",
            "Content-Type": "application/json",
        }

        max_retries = self._max_retries()
        for attempt in range(max_retries + 1):
            active_model_slug = self._model_slug_for_attempt(attempt)
            payload = {
                "model": active_model_slug,
                "messages": messages,
                "temperature": 0.2,
                "stream": True,
                "stream_options": {"include_usage": True},
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
                        async with client.stream(
                            "POST",
                            url,
                            headers=headers,
                            json=payload,
                        ) as response:
                            if response.status_code >= 400:
                                response_payload = json.loads(await response.aread())
                                error_message = _provider_error_message(response_payload)
                                latency_ms = int((perf_counter() - start) * 1000)
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
                                    and attempt < max_retries
                                ):
                                    await asyncio.sleep(
                                        self._settings.provider_retry_backoff_seconds
                                        * (attempt + 1)
                                    )
                                    continue
                                raise provider_error(
                                    "Provider stream request failed",
                                    code="SS-PROVIDER-004",
                                    details={
                                        "status_code": response.status_code,
                                        "reason": error_message,
                                    },
                                )

                            usage: dict[str, int] = {}
                            finish_reason: str | None = None
                            streamed_any = False
                            async for line in response.aiter_lines():
                                if not line.startswith("data:"):
                                    continue
                                event_text = line.removeprefix("data:").strip()
                                if not event_text:
                                    continue
                                if event_text == "[DONE]":
                                    break
                                event_payload = json.loads(event_text)
                                usage = _extract_usage(event_payload) or usage
                                delta = _extract_stream_delta(event_payload)
                                if not delta:
                                    continue
                                streamed_any = True
                                finish_reason = _extract_finish_reason(event_payload)
                                yield ProviderTextChunk(
                                    delta=delta,
                                    model_slug=str(event_payload.get("model", active_model_slug)),
                                    usage=usage,
                                    raw_event=event_payload,
                                    done=False,
                                )
                            latency_ms = int((perf_counter() - start) * 1000)
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
                                finish_reason=finish_reason,
                            )
                            _add_llm_span_attributes(
                                operation=call_context.operation,
                                provider=self._resolved.provider_name,
                                model_slug=active_model_slug,
                                usage=usage,
                            )
                            yield ProviderTextChunk(
                                delta="",
                                model_slug=active_model_slug,
                                usage=usage,
                                raw_event={},
                                done=True,
                            )
                            if streamed_any:
                                return
                            raise provider_error(
                                "Provider stream response did not include text deltas",
                                code="SS-PROVIDER-009",
                            )
            except AppError as exc:
                if exc.code in RETRYABLE_PROVIDER_PAYLOAD_CODES and attempt < max_retries:
                    await asyncio.sleep(
                        self._settings.provider_retry_backoff_seconds * (attempt + 1)
                    )
                    continue
                raise
            except TimeoutError as exc:
                latency_ms = int((perf_counter() - start) * 1000)
                timeout_error = "Provider stream request exceeded the configured timeout budget"
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
                if attempt < max_retries:
                    await asyncio.sleep(
                        self._settings.provider_retry_backoff_seconds * (attempt + 1)
                    )
                    continue
                raise provider_error(
                    "Provider stream request failed",
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
                if attempt < max_retries:
                    await asyncio.sleep(
                        self._settings.provider_retry_backoff_seconds * (attempt + 1)
                    )
                    continue
                raise provider_error(
                    "Provider stream request failed",
                    code="SS-PROVIDER-005",
                    details={"reason": str(exc), "url": url},
                ) from exc

        raise provider_error(
            "Provider stream request exhausted retries",
            code="SS-PROVIDER-006",
        )

    def _model_slug_for_attempt(self, attempt: int) -> str:
        if self._resolved.backup_model_slug and attempt >= self._backup_model_attempt_threshold():
            return self._resolved.backup_model_slug
        return self._resolved.model_slug

    def _max_retries(self) -> int:
        if self._task is LLMTaskKind.ASSISTANT:
            return self._settings.llm_assistant_max_retries
        return self._settings.provider_max_retries

    def _backup_model_attempt_threshold(self) -> int:
        if self._task is LLMTaskKind.ASSISTANT:
            return 1
        return 2

    def _complete_json_attempt_key(
        self, call_context: ProviderCallContext
    ) -> tuple[str, ...] | None:
        parts = (
            call_context.pipeline_run_id,
            call_context.operation,
            call_context.request_id,
            call_context.workflow_id,
        )
        if not any(parts):
            return None
        return tuple(part or "" for part in parts)

    def _record_complete_json_attempts(
        self,
        *,
        attempt_key: tuple[str, ...] | None,
        starting_attempt: int,
        attempts_used: int,
    ) -> None:
        if attempt_key is None or attempts_used <= 0:
            return
        self._complete_json_attempt_counts[attempt_key] = starting_attempt + attempts_used
        while len(self._complete_json_attempt_counts) > 2048:
            self._complete_json_attempt_counts.pop(next(iter(self._complete_json_attempt_counts)))


def resolve_llm_provider_config(
    settings: Settings,
    task: LLMTaskKind | None = None,
) -> ResolvedLLMProviderConfig:
    """Resolve provider details, including OpenRouter environment aliases."""

    provider_name = settings.provider_name
    base_url = settings.provider_base_url
    api_key = settings.provider_api_key
    model_slug = settings.llm_default_model
    backup_model_slug = settings.llm_default_backup_model

    if task is not None:
        model_slug = settings.get_llm_model_for_task(task)
    elif settings.llm_marking_per_skill_model:
        model_slug = settings.llm_marking_per_skill_model

    if (
        api_key is None
        and settings.openrouter_api_key
        and (provider_name != "groq" or settings.groq_api_key is None)
    ):
        api_key = settings.openrouter_api_key
        provider_name = "openrouter"
        base_url = settings.openrouter_base_url

    return ResolvedLLMProviderConfig(
        provider_name=provider_name,
        base_url=base_url,
        api_key=api_key,
        model_slug=model_slug,
        backup_model_slug=backup_model_slug,
    )


def build_llm_provider(
    *,
    settings: Settings,
    provider_call_logger: Any,
    task: LLMTaskKind | None = None,
) -> OpenAICompatibleLLMProvider:
    """Create a task-scoped OpenAI-compatible provider instance."""

    provider_name = settings.provider_name

    if provider_name == "groq":
        from soft_skills_backend.platform.providers.llm.groq import GroqLLMProvider

        return GroqLLMProvider(
            settings=settings,
            provider_call_logger=provider_call_logger,
            task=task,
        )
    elif provider_name == "openrouter":
        from soft_skills_backend.platform.providers.llm.openrouter import OpenRouterLLMProvider

        return OpenRouterLLMProvider(
            settings=settings,
            provider_call_logger=provider_call_logger,
            task=task,
        )

    return OpenAICompatibleLLMProvider(
        settings=settings,
        provider_call_logger=provider_call_logger,
        task=task,
    )


def _build_json_response_format(
    response_schema: JsonSchemaResponseFormat | None,
    *,
    provider_name: str | None = None,
) -> dict[str, Any]:
    if response_schema is None:
        return {"type": "json_object"}
    if provider_name == "openrouter":
        return {"type": "json_object"}
    if provider_name == "groq":
        # Groq rejects strict JSON schemas that contain optional properties.
        # Keep provider-side schema guidance, but disable strict mode and rely
        # on app-side typed validation/repair for the final contract.
        return {
            "type": "json_schema",
            "json_schema": {
                "name": response_schema.name,
                "strict": False,
                "schema": response_schema.normalized_schema(),
            },
        }
    strict = response_schema.strict
    return {
        "type": "json_schema",
        "json_schema": {
            "name": response_schema.name,
            "strict": strict,
            "schema": response_schema.normalized_schema(),
        },
    }


def _build_provider_preferences(
    *,
    provider_name: str,
    response_schema: JsonSchemaResponseFormat | None,
) -> dict[str, Any] | None:
    if response_schema is None:
        return None
    if provider_name != "openrouter":
        return None
    return None


def _build_provider_tool_definition(tool: ProviderToolDefinition) -> dict[str, Any]:
    return {
        "type": "function",
        "function": {
            "name": tool.name,
            "description": tool.description,
            "parameters": tool.parameters,
        },
    }


def _build_tool_payload_diagnostics(
    *,
    tools: list[ProviderToolDefinition],
    provider_tools: list[dict[str, Any]],
    messages: list[dict[str, object]],
    tool_choice: str | None,
) -> dict[str, Any]:
    payload = {
        "messages": messages,
        "tools": provider_tools,
        "parallel_tool_calls": True,
    }
    if tool_choice is not None:
        payload["tool_choice"] = {"type": "function", "function": {"name": tool_choice}}
    try:
        payload_size_bytes = len(json.dumps(payload, separators=(",", ":"), sort_keys=True))
    except TypeError:
        payload_size_bytes = None
    return {
        "tool_count": len(tools),
        "tool_choice": tool_choice,
        "message_count": len(messages),
        "payload_size_bytes": payload_size_bytes,
        "tool_names": [tool.name for tool in tools],
        "tools": [_build_single_tool_diagnostics(tool) for tool in tools],
    }


def _build_single_tool_diagnostics(tool: ProviderToolDefinition) -> dict[str, Any]:
    schema = tool.parameters
    properties = schema.get("properties")
    required = schema.get("required")
    return {
        "name": tool.name,
        "description_length": len(tool.description),
        "schema_size_bytes": len(json.dumps(schema, separators=(",", ":"), sort_keys=True)),
        "top_level_property_count": len(properties) if isinstance(properties, dict) else 0,
        "required_count": len(required) if isinstance(required, list) else 0,
        "max_schema_depth": _schema_max_depth(schema),
        "schema_keys": sorted(str(key) for key in schema.keys()),
    }


def _schema_max_depth(node: Any, *, _depth: int = 1) -> int:
    if isinstance(node, dict):
        child_depth = _depth
        for value in node.values():
            child_depth = max(child_depth, _schema_max_depth(value, _depth=_depth + 1))
        return child_depth
    if isinstance(node, list):
        child_depth = _depth
        for value in node:
            child_depth = max(child_depth, _schema_max_depth(value, _depth=_depth + 1))
        return child_depth
    return _depth


def _build_response_diagnostics(response_payload: dict[str, Any] | None) -> dict[str, Any] | None:
    if not isinstance(response_payload, dict):
        return None
    choices = response_payload.get("choices")
    diagnostics: dict[str, Any] = {
        "top_level_keys": sorted(str(key) for key in response_payload.keys()),
        "choice_count": len(choices) if isinstance(choices, list) else None,
        "model": response_payload.get("model"),
    }
    if isinstance(choices, list) and choices:
        first_choice = choices[0]
        if isinstance(first_choice, dict):
            message = first_choice.get("message")
            diagnostics["choice_keys"] = sorted(str(key) for key in first_choice.keys())
            if isinstance(message, dict):
                diagnostics["message_keys"] = sorted(str(key) for key in message.keys())
                diagnostics["content_type"] = type(message.get("content")).__name__
    return {key: value for key, value in diagnostics.items() if value is not None}


def _extract_provider_message(payload: dict[str, Any]) -> dict[str, Any]:
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
    return cast(dict[str, Any], message)


def _extract_message_content(payload: dict[str, Any]) -> str | dict[str, Any]:
    message = _extract_provider_message(payload)
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
            "message_keys": sorted(str(key) for key in message),
        },
    )


def _extract_provider_message_text(message: dict[str, Any]) -> str | None:
    content = message.get("content")
    if isinstance(content, str):
        stripped = content.strip()
        return stripped or None
    if isinstance(content, list):
        text_parts = [
            str(item.get("text"))
            for item in content
            if isinstance(item, dict)
            and item.get("type") == "text"
            and item.get("text") is not None
        ]
        joined = "".join(text_parts).strip()
        return joined or None
    if content is None:
        return None
    raise provider_error(
        "Provider completion response content was not understood",
        code="SS-PROVIDER-009",
        details={
            "content_type": type(content).__name__,
            "message_keys": sorted(str(key) for key in message),
        },
    )


def _extract_provider_tool_calls(message: dict[str, Any]) -> list[ProviderToolCall]:
    raw_tool_calls = message.get("tool_calls")
    if raw_tool_calls is None:
        return []
    if not isinstance(raw_tool_calls, list):
        raise provider_error(
            "Provider tool completion response did not include tool calls in the expected shape",
            code="SS-PROVIDER-010",
        )
    tool_calls: list[ProviderToolCall] = []
    for raw_tool_call in raw_tool_calls:
        if not isinstance(raw_tool_call, dict):
            raise provider_error(
                "Provider tool completion response included an invalid tool call",
                code="SS-PROVIDER-010",
            )
        function = raw_tool_call.get("function")
        if not isinstance(function, dict):
            raise provider_error(
                "Provider tool completion response did not include a function payload",
                code="SS-PROVIDER-010",
            )
        tool_name = function.get("name")
        arguments = function.get("arguments", "{}")
        if not isinstance(tool_name, str) or not tool_name.strip():
            raise provider_error(
                "Provider tool completion response did not include a function name",
                code="SS-PROVIDER-010",
            )
        parsed_arguments = _parse_tool_arguments(arguments)
        tool_calls.append(
            ProviderToolCall(
                call_id=str(raw_tool_call.get("id") or tool_name),
                tool_name=tool_name,
                arguments=parsed_arguments,
                raw_tool_call=raw_tool_call,
            )
        )
    return tool_calls


def _parse_tool_arguments(arguments: Any) -> dict[str, Any]:
    if isinstance(arguments, dict):
        return cast(dict[str, Any], arguments)
    if isinstance(arguments, str):
        try:
            parsed = json.loads(arguments)
        except json.JSONDecodeError as exc:
            raise provider_error(
                "Provider tool completion arguments were not valid JSON",
                code="SS-PROVIDER-011",
                details={"reason": str(exc)},
            ) from exc
        if isinstance(parsed, dict):
            return cast(dict[str, Any], parsed)
    raise provider_error(
        "Provider tool completion arguments were not understood",
        code="SS-PROVIDER-011",
        details={"arguments_type": type(arguments).__name__},
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


def _extract_finish_reason(payload: dict[str, Any]) -> str | None:
    choices = payload.get("choices")
    if not isinstance(choices, list) or not choices:
        return None
    finish_reason = choices[0].get("finish_reason")
    if isinstance(finish_reason, str):
        return finish_reason
    return None


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


def _extract_stream_delta(payload: dict[str, Any]) -> str:
    choices = payload.get("choices")
    if not isinstance(choices, list) or not choices:
        return ""
    delta = choices[0].get("delta")
    if not isinstance(delta, dict):
        return ""
    content = delta.get("content")
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
    return ""
