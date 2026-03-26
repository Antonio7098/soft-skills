"""Content generation smoke result contracts."""

from __future__ import annotations

from pydantic import BaseModel


class ContentGenerationTimingSample(BaseModel):
    """Latency and scale snapshot for one generation flow."""

    flow_name: str
    generation_mode: str
    elapsed_ms: int
    collection_id: str
    generation_artifact_id: str | None = None
    provider: str | None = None
    model_slug: str | None = None
    prompt_items_count: int = 0
    scenarios_count: int = 0
    expected_llm_calls: int = 0
    expected_subpipelines: int = 0


class ContentGenerationSmokeResult(BaseModel):
    """Result of content generation smoke suite."""

    status: str
    generation_mode: str
    collection_id: str
    provider: str | None = None
    model_slug: str | None = None
    generation_artifact_id: str | None = None
    prompt_items_count: int | None = None
    scenarios_count: int | None = None
    error_code: str | None = None


class ContentGenerationLatencyEnvelopeResult(BaseModel):
    """Result of the high-latency generation envelope suite."""

    status: str
    provider: str | None = None
    model_slug: str | None = None
    total_elapsed_ms: int
    max_flow_elapsed_ms: int
    total_expected_llm_calls: int
    total_expected_subpipelines: int
    samples: list[ContentGenerationTimingSample]
