"""HTTP middleware for correlation and structured request logging."""

from __future__ import annotations

from time import perf_counter
from typing import Any, cast

from starlette.types import ASGIApp, Message, Receive, Scope, Send

from soft_skills_backend.platform.observability.context import (
    clear_request_context,
    initialize_request_context,
)
from soft_skills_backend.platform.observability.events import WorkflowEvent
from soft_skills_backend.platform.observability.logging import get_logger
from soft_skills_backend.platform.observability.telemetry import (
    W3C_TRACE_VERSION,
    extract_trace_context,
)


class RequestContextMiddleware:
    """Attach correlation identifiers to requests and responses and emit HTTP audit events."""

    def __init__(self, app: ASGIApp, workflow_events: Any = None) -> None:
        self.app = app
        self._workflow_events = workflow_events

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        logger = get_logger("soft_skills_backend.http")
        start_time = perf_counter()
        headers = {
            key.decode("latin1").lower(): value.decode("latin1")
            for key, value in scope.get("headers", [])
        }

        otel_context = extract_trace_context(headers)
        trace_id_from_otel = None
        if otel_context:
            traceparent = otel_context.get("traceparent", "")
            if traceparent:
                parts = traceparent.split("-")
                if len(parts) >= 3:
                    trace_id_from_otel = parts[1]

        correlation = initialize_request_context(
            request_id=headers.get("x-request-id"),
            trace_id=headers.get("x-trace-id") or trace_id_from_otel,
            workflow_id=headers.get("x-workflow-id"),
        )
        scope.setdefault("state", {})
        scope["state"]["request_id"] = correlation["request_id"]
        scope["state"]["trace_id"] = correlation["trace_id"]
        scope["state"]["workflow_id"] = correlation["workflow_id"] or None

        client_ip = self._extract_client_ip(scope)
        query_params = dict(self._parse_query_params(scope.get("query_string", b"")))
        user_agent = headers.get("user-agent", "")[:256] if headers.get("user-agent") else None

        if self._workflow_events is not None:
            received_event = WorkflowEvent(
                event_type="http.request.received.v1",
                request_id=correlation["request_id"],
                trace_id=correlation["trace_id"],
                workflow_id=correlation["workflow_id"],
                payload={
                    "method": scope["method"],
                    "path": scope["path"],
                    "query_params": query_params,
                    "user_agent": user_agent,
                    "client_ip": client_ip,
                },
            )
            self._workflow_events.record(received_event)

        status_code = 0
        error_code: str | None = None

        async def send_with_correlation(message: Message) -> None:
            nonlocal status_code, error_code
            if message["type"] == "http.response.start":
                status_code = message.get("status", 0)
                message.setdefault("headers", [])
                headers_list = list(message["headers"])
                headers_list.append((b"x-request-id", correlation["request_id"].encode("latin1")))
                headers_list.append((b"x-trace-id", correlation["trace_id"].encode("latin1")))
                headers_list.append(
                    (
                        b"traceparent",
                        f"{W3C_TRACE_VERSION}-{correlation['trace_id']}-0-01".encode("latin1"),
                    )
                )
                message["headers"] = headers_list
            await send(message)

        try:
            await self.app(scope, receive, send_with_correlation)
        except Exception as exc:
            error_code = getattr(exc, "code", None)
            raise
        finally:
            duration_ms = int((perf_counter() - start_time) * 1000)
            logger.info(
                "http.request.completed",
                method=scope["method"],
                path=scope["path"],
                status_code=status_code,
                duration_ms=duration_ms,
            )
            if self._workflow_events is not None:
                completed_event = WorkflowEvent(
                    event_type="http.request.completed.v1",
                    request_id=correlation["request_id"],
                    trace_id=correlation["trace_id"],
                    workflow_id=correlation["workflow_id"],
                    error_code=error_code,
                    payload={
                        "method": scope["method"],
                        "path": scope["path"],
                        "status_code": status_code,
                        "latency_ms": duration_ms,
                        "error_code": error_code,
                    },
                )
                self._workflow_events.record(completed_event)
            clear_request_context()

    def _extract_client_ip(self, scope: Scope) -> str | None:
        client_tuple = cast(tuple[str, int] | None, scope.get("client"))
        if client_tuple is None:
            return None
        return client_tuple[0]

    def _parse_query_params(self, query_string: bytes) -> dict[str, str]:
        if not query_string:
            return {}
        params: dict[str, str] = {}
        for part in query_string.decode("latin1").split("&"):
            if "=" in part:
                key, value = part.split("=", 1)
                params[key] = value
            elif part:
                params[part] = ""
        return params
