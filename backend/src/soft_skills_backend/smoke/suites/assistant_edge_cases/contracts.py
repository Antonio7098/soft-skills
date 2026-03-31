"""Assistant edge case smoke result contracts."""

from __future__ import annotations

from pydantic import BaseModel


class AssistantEdgeCaseSmokeResult(BaseModel):
    """Result of assistant edge case smoke suite."""

    status: str
    test_name: str
    session_id: str | None = None
    turn_count: int = 0
    tool_names: list[str] = []
    error_code: str | None = None
    error_details: dict | None = None


class AssistantLongMessageSmokeResult(AssistantEdgeCaseSmokeResult):
    """Result for long message edge case test."""


class AssistantSpecialCharsSmokeResult(AssistantEdgeCaseSmokeResult):
    """Result for special characters edge case test."""


class AssistantRapidTurnsSmokeResult(AssistantEdgeCaseSmokeResult):
    """Result for rapid sequential turns edge case test."""


class AssistantConcurrentSessionsSmokeResult(AssistantEdgeCaseSmokeResult):
    """Result for concurrent sessions edge case test."""


class AssistantEmptyMessageSmokeResult(AssistantEdgeCaseSmokeResult):
    """Result for empty/minimal message edge case test."""


class AssistantToolSequenceSmokeResult(AssistantEdgeCaseSmokeResult):
    """Result for tool sequencing edge case test."""


class AssistantInvalidSessionSmokeResult(AssistantEdgeCaseSmokeResult):
    """Result for invalid session handling edge case test."""
