"""Assistant domain enums and invariants."""

from __future__ import annotations

from enum import StrEnum


class AssistantSessionStatus(StrEnum):
    ACTIVE = "active"
    ARCHIVED = "archived"


class AssistantTurnStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    CANCELLING = "cancelling"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    FAILED = "failed"


class AssistantMessageRole(StrEnum):
    USER = "user"
    ASSISTANT = "assistant"


class AssistantToolCallStatus(StrEnum):
    PENDING_APPROVAL = "pending_approval"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AssistantApprovalStatus(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    DENIED = "denied"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


TERMINAL_TURN_STATUSES = {
    AssistantTurnStatus.COMPLETED,
    AssistantTurnStatus.CANCELLED,
    AssistantTurnStatus.FAILED,
}


def is_turn_terminal(status: AssistantTurnStatus | str) -> bool:
    return AssistantTurnStatus(status) in TERMINAL_TURN_STATUSES
