"""OpenRouter pricing helpers."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any, cast

import httpx

from soft_skills_backend.config import Settings

_PRICING_CACHE_FILE = Path(__file__).parent.parent / "cache" / "openrouter_pricing.json"
_PRICING_CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)


@lru_cache(maxsize=1)
def get_cached_pricing() -> dict[str, dict[str, float]]:
    """Get cached pricing from file, or empty dict if none."""
    if _PRICING_CACHE_FILE.exists():
        try:
            return cast(dict[str, dict[str, float]], json.loads(_PRICING_CACHE_FILE.read_text()))
        except Exception:
            return {}
    return {}


def save_pricing_cache(pricing: dict[str, dict[str, float]]) -> None:
    """Save pricing to cache file."""
    _PRICING_CACHE_FILE.write_text(json.dumps(pricing))
    get_cached_pricing.cache_clear()


def _extract_price_per_1m(pricing: dict[str, object] | None) -> float | None:
    """Extract price per 1M tokens from OpenRouter pricing object."""
    if not pricing:
        return None
    prompt_price = pricing.get("prompt", {})
    if isinstance(prompt_price, dict):
        return prompt_price.get("price_per_1m")
    return None


def _extract_completion_price_per_1m(pricing: dict[str, object] | None) -> float | None:
    """Extract completion price per 1M tokens from OpenRouter pricing object."""
    if not pricing:
        return None
    completion_price = pricing.get("completion", {})
    if isinstance(completion_price, dict):
        return completion_price.get("price_per_1m")
    return None


def fetch_and_cache_pricing(settings: Settings) -> dict[str, dict[str, float]]:
    """Fetch pricing from OpenRouter API and cache it."""
    if not settings.openrouter_api_key:
        return {}

    cache: dict[str, dict[str, float]] = {}

    import asyncio

    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    async def _fetch() -> dict[str, object]:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://openrouter.ai/api/v1/models",
                headers={"Authorization": f"Bearer {settings.openrouter_api_key}"},
                timeout=60.0,
            )
            response.raise_for_status()
            return cast(dict[str, object], response.json())

    data = loop.run_until_complete(_fetch())

    for m in cast(list[dict[str, object]], data.get("data", [])):
        model_id = cast(str, m.get("id"))
        pricing = m.get("pricing")
        if model_id and pricing:
            cache[model_id] = {
                "prompt_price_per_1m": _extract_price_per_1m(
                    cast(dict[str, object] | None, pricing)
                )
                or 0,
                "completion_price_per_1m": _extract_completion_price_per_1m(
                    cast(dict[str, object] | None, pricing)
                )
                or 0,
            }

    save_pricing_cache(cache)
    return cache


def calculate_cost(
    model_id: str,
    prompt_tokens: int,
    completion_tokens: int,
) -> float:
    """Calculate cost in USD for a given model and token counts."""
    pricing = get_cached_pricing().get(model_id)
    if not pricing:
        return 0.0

    prompt_price = pricing.get("prompt_price_per_1m", 0)
    completion_price = pricing.get("completion_price_per_1m", 0)

    prompt_cost = (prompt_tokens / 1_000_000) * prompt_price
    completion_cost = (completion_tokens / 1_000_000) * completion_price

    return round(prompt_cost + completion_cost, 6)
