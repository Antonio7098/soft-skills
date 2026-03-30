"""Global API error handlers."""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from soft_skills_backend.config import Settings
from soft_skills_backend.entrypoints.http.schemas import ErrorBody, ErrorEnvelope, response_meta
from soft_skills_backend.platform.observability.logging import get_logger
from soft_skills_backend.shared.errors import AppError, ErrorCategory


def register_error_handlers(app: FastAPI, settings: Settings) -> None:
    """Attach application error handlers."""

    logger = get_logger("soft_skills_backend.errors")

    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
        logger.info(
            "api.error",
            code=exc.code,
            category=exc.category.value,
            status_code=exc.status_code,
        )
        payload = ErrorEnvelope(
            error=ErrorBody(
                code=exc.code,
                category=exc.category,
                message=exc.message,
                details=None if exc.details is None else dict(exc.details),
            ),
            meta=response_meta(request),
        )
        return JSONResponse(status_code=exc.status_code, content=payload.model_dump(mode="json"))

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        payload = ErrorEnvelope(
            error=ErrorBody(
                code="SS-VALIDATION-001",
                category=ErrorCategory.VALIDATION,
                message="Request validation failed",
                details={"errors": _sanitize_for_json(exc.errors())},
            ),
            meta=response_meta(request),
        )
        return JSONResponse(status_code=422, content=payload.model_dump(mode="json"))

    @app.exception_handler(Exception)
    async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("api.unhandled_error", error_type=exc.__class__.__name__)
        details: dict[str, object] | None = (
            {"error_type": exc.__class__.__name__} if settings.environment != "prod" else None
        )
        payload = ErrorEnvelope(
            error=ErrorBody(
                code="SS-ORCHESTRATION-001",
                category=ErrorCategory.ORCHESTRATION,
                message="Unhandled application error",
                details=details,
            ),
            meta=response_meta(request),
        )
        return JSONResponse(status_code=500, content=payload.model_dump(mode="json"))


def _sanitize_for_json(value: Any) -> Any:
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, dict):
        return {str(key): _sanitize_for_json(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_sanitize_for_json(item) for item in value]
    return str(value)
