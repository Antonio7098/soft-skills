"""Shared application errors."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from typing import Any


class ErrorCategory(StrEnum):
    """Stable error categories from the canon."""

    VALIDATION = "validation"
    DOMAIN = "domain"
    SCORING = "scoring"
    ORCHESTRATION = "orchestration"
    PROVIDER = "provider"
    PERSISTENCE = "persistence"
    AUTH = "auth"
    UI = "ui"


@dataclass(slots=True)
class AppError(Exception):
    """Structured application error with stable code."""

    code: str
    category: ErrorCategory
    message: str
    status_code: int
    details: Mapping[str, Any] | None = None

    def __str__(self) -> str:
        return f"{self.code}: {self.message}"


def validation_error(
    message: str,
    *,
    code: str = "SS-VALIDATION-001",
    status_code: int = 422,
    details: Mapping[str, Any] | None = None,
) -> AppError:
    return AppError(
        code=code,
        category=ErrorCategory.VALIDATION,
        message=message,
        status_code=status_code,
        details=details,
    )


def persistence_error(
    message: str,
    *,
    code: str = "SS-PERSISTENCE-001",
    status_code: int = 503,
    details: Mapping[str, Any] | None = None,
) -> AppError:
    return AppError(
        code=code,
        category=ErrorCategory.PERSISTENCE,
        message=message,
        status_code=status_code,
        details=details,
    )


def auth_error(
    message: str,
    *,
    code: str = "SS-AUTH-001",
    status_code: int = 401,
    details: Mapping[str, Any] | None = None,
) -> AppError:
    return AppError(
        code=code,
        category=ErrorCategory.AUTH,
        message=message,
        status_code=status_code,
        details=details,
    )


def domain_error(
    message: str,
    *,
    code: str = "SS-DOMAIN-001",
    status_code: int = 400,
    details: Mapping[str, Any] | None = None,
) -> AppError:
    return AppError(
        code=code,
        category=ErrorCategory.DOMAIN,
        message=message,
        status_code=status_code,
        details=details,
    )


def provider_error(
    message: str,
    *,
    code: str = "SS-PROVIDER-001",
    status_code: int = 503,
    details: Mapping[str, Any] | None = None,
) -> AppError:
    return AppError(
        code=code,
        category=ErrorCategory.PROVIDER,
        message=message,
        status_code=status_code,
        details=details,
    )


def scoring_error(
    message: str,
    *,
    code: str = "SS-SCORING-001",
    status_code: int = 422,
    details: Mapping[str, Any] | None = None,
) -> AppError:
    return AppError(
        code=code,
        category=ErrorCategory.SCORING,
        message=message,
        status_code=status_code,
        details=details,
    )


def orchestration_error(
    message: str,
    *,
    code: str = "SS-ORCHESTRATION-001",
    status_code: int = 500,
    details: Mapping[str, Any] | None = None,
) -> AppError:
    return AppError(
        code=code,
        category=ErrorCategory.ORCHESTRATION,
        message=message,
        status_code=status_code,
        details=details,
    )


def get_typed_error_event_type(error: AppError) -> str:
    """Map an AppError to its corresponding typed error event type."""
    code = error.code
    if code.startswith("SS-VALIDATION-"):
        return "error.validation.v1"
    if code.startswith("SS-AUTH-"):
        auth_num = int(code.split("-")[-1])
        if auth_num <= 3:
            return "error.authentication.v1"
        return "error.authorization.v1"
    if code.startswith("SS-DOMAIN-"):
        return "error.not_found.v1"
    if code.startswith("SS-SCORING-"):
        return "error.scoring.v1"
    if code.startswith("SS-PROVIDER-"):
        return "error.provider.v1"
    if code.startswith("SS-ORCHESTRATION-"):
        return "error.rate_limited.v1"
    if code.startswith("SS-PERSISTENCE-"):
        return "error.persistence.v1"
    return "error.unknown.v1"
