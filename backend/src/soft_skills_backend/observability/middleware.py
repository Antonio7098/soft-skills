"""HTTP middleware for correlation and structured request logging."""

from __future__ import annotations

from time import perf_counter

from starlette.types import ASGIApp, Message, Receive, Scope, Send

from soft_skills_backend.observability.context import (
    clear_request_context,
    initialize_request_context,
)
from soft_skills_backend.observability.logging import get_logger


class RequestContextMiddleware:
    """Attach correlation identifiers to requests and responses."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

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
        correlation = initialize_request_context(
            request_id=headers.get("x-request-id"),
            trace_id=headers.get("x-trace-id"),
            workflow_id=headers.get("x-workflow-id"),
        )
        scope.setdefault("state", {})
        scope["state"]["request_id"] = correlation["request_id"]
        scope["state"]["trace_id"] = correlation["trace_id"]
        scope["state"]["workflow_id"] = correlation["workflow_id"] or None

        async def send_with_correlation(message: Message) -> None:
            if message["type"] == "http.response.start":
                message.setdefault("headers", [])
                headers_list = list(message["headers"])
                headers_list.append((b"x-request-id", correlation["request_id"].encode("latin1")))
                headers_list.append((b"x-trace-id", correlation["trace_id"].encode("latin1")))
                message["headers"] = headers_list
            await send(message)

        try:
            await self.app(scope, receive, send_with_correlation)
        finally:
            duration_ms = int((perf_counter() - start_time) * 1000)
            logger.info(
                "http.request.completed",
                method=scope["method"],
                path=scope["path"],
                duration_ms=duration_ms,
            )
            clear_request_context()
