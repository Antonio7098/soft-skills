"""Provider model endpoints."""

from __future__ import annotations

import httpx

from fastapi import APIRouter, Request

from soft_skills_backend.config import Settings
from soft_skills_backend.entrypoints.http.schemas import ApiEnvelope, ok_response
from soft_skills_backend.platform.providers.openrouter_pricing import (
    calculate_cost,
    fetch_and_cache_pricing,
    get_cached_pricing,
)

router = APIRouter()


@router.get("/providers/openrouter/models", response_model=ApiEnvelope[list[dict]])
async def list_openrouter_models(
    request: Request, force_refresh: bool = False
) -> ApiEnvelope[list[dict]]:
    """List available models from OpenRouter with pricing."""
    settings: Settings = request.app.state.settings

    if not settings.openrouter_api_key:
        return ok_response(request, [])

    # Try to use cache unless force refresh
    cache = get_cached_pricing() if not force_refresh else {}

    # If cache is empty, fetch from API
    if not cache:
        cache = fetch_and_cache_pricing(settings)

    # Need to fetch model list from API regardless
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://openrouter.ai/api/v1/models",
            headers={"Authorization": f"Bearer {settings.openrouter_api_key}"},
            timeout=30.0,
        )
        response.raise_for_status()
        data = response.json()

    models = [
        {
            "id": m.get("id"),
            "name": m.get("name"),
            "provider": "openrouter",
            "pricing": cache.get(m.get("id")) if cache.get(m.get("id")) else None,
        }
        for m in data.get("data", [])
        if m.get("id") and m.get("name")
    ]

    return ok_response(request, models)


@router.get(
    "/providers/openrouter/pricing", response_model=ApiEnvelope[dict[str, dict[str, float]]]
)
async def get_openrouter_pricing(request: Request) -> ApiEnvelope[dict[str, dict[str, float]]]:
    """Get cached OpenRouter pricing data."""
    return ok_response(request, get_cached_pricing())


@router.post(
    "/providers/openrouter/pricing/refresh", response_model=ApiEnvelope[dict[str, dict[str, float]]]
)
async def refresh_openrouter_pricing(request: Request) -> ApiEnvelope[dict[str, dict[str, float]]]:
    """Force refresh OpenRouter pricing data from API."""
    settings: Settings = request.app.state.settings

    if not settings.openrouter_api_key:
        return ok_response(request, {})

    cache = fetch_and_cache_pricing(settings)

    return ok_response(request, cache)


@router.get("/providers/openrouter/cost")
async def calculate_openrouter_cost(
    request: Request,
    model_id: str,
    prompt_tokens: int,
    completion_tokens: int,
) -> dict[str, float]:
    """Calculate cost for a model with given token counts."""
    cost = calculate_cost(model_id, prompt_tokens, completion_tokens)
    return {"cost_usd": cost}
