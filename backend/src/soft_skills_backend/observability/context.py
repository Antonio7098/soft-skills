"""Request-scoped correlation context helpers."""

from __future__ import annotations

from typing import Any
from uuid import uuid4

import structlog


def initialize_request_context(
    *,
    request_id: str | None = None,
    trace_id: str | None = None,
    workflow_id: str | None = None,
    user_id: str | None = None,
) -> dict[str, str]:
    """Reset and bind request-scoped identifiers."""

    resolved_request_id = request_id or uuid4().hex
    resolved_trace_id = trace_id or uuid4().hex
    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(
        request_id=resolved_request_id,
        trace_id=resolved_trace_id,
        workflow_id=workflow_id,
        user_id=user_id,
    )
    return {
        "request_id": resolved_request_id,
        "trace_id": resolved_trace_id,
        "workflow_id": workflow_id or "",
        "user_id": user_id or "",
    }


def clear_request_context() -> None:
    """Clear all request-scoped identifiers."""

    structlog.contextvars.clear_contextvars()


def get_current_context() -> dict[str, Any]:
    """Return the currently bound context variables."""

    return structlog.contextvars.get_contextvars()
