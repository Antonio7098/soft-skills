"""Shared API schemas and response helpers."""

from __future__ import annotations

from typing import Generic, TypeVar

from fastapi import Request
from pydantic import BaseModel, Field

from soft_skills_backend.shared.errors import ErrorCategory

T = TypeVar("T")


class ResponseMeta(BaseModel):
    """Correlation metadata returned with all responses."""

    request_id: str = ""
    trace_id: str = ""
    version: str = Field(default="v1")


class ApiEnvelope(BaseModel, Generic[T]):
    """Standard API success envelope."""

    data: T
    meta: ResponseMeta


class ErrorBody(BaseModel):
    """Standard API error body."""

    code: str
    category: ErrorCategory
    message: str
    details: dict[str, object] | None = None


class ErrorEnvelope(BaseModel):
    """Standard API error envelope."""

    error: ErrorBody
    meta: ResponseMeta


def response_meta(request: Request) -> ResponseMeta:
    """Build response metadata from request state."""

    return ResponseMeta(
        request_id=getattr(request.state, "request_id", ""),
        trace_id=getattr(request.state, "trace_id", ""),
    )


def ok_response(request: Request, data: T) -> ApiEnvelope[T]:
    """Wrap successful responses."""

    return ApiEnvelope[T](data=data, meta=response_meta(request))
