"""Shared Stageflow prompt render stage for registry-backed prompt execution."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from stageflow.core import StageContext

from soft_skills_backend.modules.admin.domain.prompt_registry import PromptRegistry
from soft_skills_backend.platform.workflows.stageflow import (
    StageflowStageResult,
    metadata_value,
    ok_output,
    pipeline_run_id_from_context,
    request_id_from_context,
)
from soft_skills_backend.shared.errors import orchestration_error


@dataclass(frozen=True, slots=True)
class PromptRenderRequest:
    """One prompt render request emitted by an upstream stage."""

    name: str
    version: str
    variables: dict[str, object] = field(default_factory=dict)
    tokens: int = 0


def create_prompt_render_stage(
    *,
    prompt_registry: PromptRegistry,
    request_stage_name: str,
) -> Any:
    """Return a Stageflow transform that renders a prompt request strictly via the registry."""

    async def prompt_render_transform(ctx: StageContext) -> Any:
        request = ctx.inputs.require_from(request_stage_name, "payload")
        if not isinstance(request, PromptRenderRequest):
            raise orchestration_error(
                "Prompt render stage received an invalid prompt request payload",
                code="SS-ORCHESTRATION-209",
                details={
                    "request_stage_name": request_stage_name,
                    "payload_type": type(request).__name__,
                },
            )
        result = prompt_registry.render(
            request.name,
            version=request.version,
            variables=request.variables,
            trace_id=metadata_value(ctx, "trace_id"),
            pipeline_run_id=pipeline_run_id_from_context(ctx),
            tokens=request.tokens,
        )
        return ok_output(
            StageflowStageResult(
                payload=result.rendered,
                summary={
                    "request_id": request_id_from_context(ctx),
                    "prompt_name": result.rendered.name,
                    "prompt_version": result.rendered.version,
                    "prompt_version_id": result.prompt_version_id,
                    "render_event_id": result.event_id,
                    "latency_ms": result.latency_ms,
                    "render_success": result.success,
                },
            )
        )

    return prompt_render_transform
