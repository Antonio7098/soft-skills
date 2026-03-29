"""Admin telemetry smoke suite."""

from __future__ import annotations

from .contracts import AdminTelemetrySmokeResult
from .smoke import AdminTelemetrySmoke

__all__ = ["AdminTelemetrySmoke", "AdminTelemetrySmokeResult"]
