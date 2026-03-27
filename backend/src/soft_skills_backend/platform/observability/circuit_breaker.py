"""Database-backed circuit breaker for multi-worker deployments."""

from __future__ import annotations

import time
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum

from sqlalchemy.orm import Session

from soft_skills_backend.platform.db.models import CircuitBreakerRecord


class CircuitBreakerStatus(StrEnum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


CIRCUIT_BREAKER_THRESHOLD = 5
CIRCUIT_BREAKER_RESET_TIMEOUT_SECONDS = 30


@dataclass
class CircuitBreakerState:
    status: CircuitBreakerStatus
    failure_count: int
    last_failure_at: datetime | None
    last_failure_reason: str | None
    opened_at: datetime | None
    closed_at: datetime | None


class DatabaseCircuitBreaker:
    """Circuit breaker backed by database for multi-worker deployments.

    This allows circuit breaker state to be shared across workers,
    ensuring consistent failure handling in horizontally scaled deployments.
    """

    def __init__(
        self,
        session: Session,
        *,
        threshold: int = CIRCUIT_BREAKER_THRESHOLD,
        reset_timeout_seconds: int = CIRCUIT_BREAKER_RESET_TIMEOUT_SECONDS,
    ) -> None:
        self._session = session
        self._threshold = threshold
        self._reset_timeout = reset_timeout_seconds

    def get_state(self, stage_name: str) -> CircuitBreakerState:
        record = self._session.get(CircuitBreakerRecord, stage_name)
        if record is None:
            return CircuitBreakerState(
                status=CircuitBreakerStatus.CLOSED,
                failure_count=0,
                last_failure_at=None,
                last_failure_reason=None,
                opened_at=None,
                closed_at=None,
            )
        return CircuitBreakerState(
            status=CircuitBreakerStatus(record.status),
            failure_count=record.failure_count,
            last_failure_at=record.last_failure_at,
            last_failure_reason=record.last_failure_reason,
            opened_at=record.opened_at,
            closed_at=record.closed_at,
        )

    def is_callable(self, stage_name: str) -> bool:
        state = self.get_state(stage_name)
        if state.status == CircuitBreakerStatus.CLOSED:
            return True
        if state.status == CircuitBreakerStatus.OPEN:
            if state.last_failure_at is None:
                return True
            elapsed = time.time() - state.last_failure_at.timestamp()
            return elapsed > self._reset_timeout
        return True

    def record_success(self, stage_name: str) -> None:
        record = self._session.get(CircuitBreakerRecord, stage_name)
        if record is None:
            return
        record.status = CircuitBreakerStatus.CLOSED.value
        record.failure_count = 0
        record.closed_at = datetime.now(UTC)
        record.updated_at = datetime.now(UTC)

    def record_failure(self, stage_name: str, reason: str | None = None) -> None:
        now = datetime.now(UTC)
        record = self._session.get(CircuitBreakerRecord, stage_name)
        if record is None:
            record = CircuitBreakerRecord(
                name=stage_name,
                status=CircuitBreakerStatus.CLOSED.value,
                failure_count=0,
            )
            self._session.add(record)
        record.failure_count = record.failure_count + 1
        record.last_failure_at = now
        record.last_failure_reason = reason
        record.updated_at = now
        if record.failure_count >= self._threshold:
            record.status = CircuitBreakerStatus.OPEN.value
            record.opened_at = now
        else:
            record.status = CircuitBreakerStatus.HALF_OPEN.value
