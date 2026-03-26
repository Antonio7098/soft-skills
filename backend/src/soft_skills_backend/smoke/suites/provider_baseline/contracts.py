"""Provider baseline smoke result contracts."""

from __future__ import annotations

from pydantic import BaseModel


class ProviderBaselineSmokeResult(BaseModel):
    """Result of a direct low-level provider smoke call."""

    status: str
    provider: str
    model_slug: str
    response_preview: str
