"""Defensive assistant SQL result redaction."""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any, Mapping

_EMAIL_PATTERN = re.compile(r"([A-Za-z0-9._%+-]+)@([A-Za-z0-9.-]+\.[A-Za-z]{2,})")
_SENSITIVE_KEYWORDS = ("email", "content", "prompt", "response", "text", "payload")


class AssistantResultRedactor:
    """Backstop redaction for learner-safe SQL results."""

    def redact_rows(self, rows: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
        return [self._redact_row(row) for row in rows]

    def _redact_row(self, row: Mapping[str, Any]) -> dict[str, Any]:
        redacted: dict[str, Any] = {}
        for key, value in row.items():
            lowered = key.lower()
            if any(keyword in lowered for keyword in _SENSITIVE_KEYWORDS):
                redacted[key] = "[redacted]"
                continue
            redacted[key] = self._redact_value(value)
        return redacted

    def _redact_value(self, value: Any) -> Any:
        if value is None or isinstance(value, (bool, int, float)):
            return value
        if isinstance(value, datetime):
            return value.isoformat()
        if isinstance(value, str):
            masked = _EMAIL_PATTERN.sub(r"***@\2", value)
            if len(masked) > 240:
                return f"{masked[:237]}..."
            return masked
        if isinstance(value, (list, dict, tuple, set)):
            return "[redacted]"
        return str(value)
