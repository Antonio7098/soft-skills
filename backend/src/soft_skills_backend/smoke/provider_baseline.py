"""Baseline real-provider smoke harness."""

from __future__ import annotations

from collections.abc import Sequence

import httpx
from pydantic import BaseModel

from soft_skills_backend.config import Settings, get_settings
from soft_skills_backend.domain.errors import provider_error, validation_error


class ProviderSmokeResult(BaseModel):
    """Result of the baseline provider smoke flow."""

    provider: str
    status: str
    model_slug: str
    checked_url: str


def run_provider_smoke(settings: Settings | None = None) -> ProviderSmokeResult:
    """Hit the provider models endpoint to confirm backend credentials work."""

    resolved_settings = settings or get_settings()
    if not resolved_settings.provider_api_key:
        raise validation_error(
            "Provider API key is required for smoke coverage",
            code="SS-VALIDATION-002",
        )

    url = f"{resolved_settings.provider_base_url.rstrip('/')}/models"
    headers = {"Authorization": f"Bearer {resolved_settings.provider_api_key}"}
    try:
        response = httpx.get(url, headers=headers, timeout=resolved_settings.smoke_timeout_seconds)
        response.raise_for_status()
        payload = response.json()
    except httpx.HTTPError as exc:
        raise provider_error(
            "Provider smoke request failed",
            code="SS-PROVIDER-002",
            details={"reason": str(exc), "url": url},
        ) from exc

    model_ids = _extract_model_ids(payload)
    if resolved_settings.provider_model_slug not in model_ids:
        raise provider_error(
            "Expected provider model slug is not visible to the backend credentials",
            code="SS-PROVIDER-003",
            details={"model_slug": resolved_settings.provider_model_slug, "url": url},
        )

    return ProviderSmokeResult(
        provider=resolved_settings.provider_name,
        status="ok",
        model_slug=resolved_settings.provider_model_slug,
        checked_url=url,
    )


def _extract_model_ids(payload: object) -> set[str]:
    if not isinstance(payload, dict):
        return set()
    data = payload.get("data")
    if not isinstance(data, Sequence):
        return set()
    model_ids: set[str] = set()
    for entry in data:
        if isinstance(entry, dict):
            model_id = entry.get("id")
            if isinstance(model_id, str):
                model_ids.add(model_id)
    return model_ids


def main() -> None:
    """CLI entrypoint."""

    run_provider_smoke()
