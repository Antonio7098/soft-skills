"""Database-backed prompt registry with built-in prompt syncing and render tracking."""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any
from uuid import uuid4

from soft_skills_backend.config import Settings
from soft_skills_backend.engines.marking.contracts.models import RenderedPrompt
from soft_skills_backend.modules.admin.domain.prompt_validation import (
    PromptValidationError,
    validate_prompt,
)
from soft_skills_backend.modules.admin.infra.prompt_repository import PromptRepository
from soft_skills_backend.shared.errors import orchestration_error, validation_error


@dataclass(frozen=True, slots=True)
class RenderResult:
    """Rendered prompt plus observability metadata."""

    rendered: RenderedPrompt
    event_id: str
    latency_ms: int
    success: bool
    prompt_version_id: int
    error_code: str | None = None


class PromptRegistry:
    """Strict prompt registry for assistant and generation workflows."""

    def __init__(
        self,
        *,
        settings: Settings,
        prompts: PromptRepository,
    ) -> None:
        self._settings = settings
        self._prompts = prompts

    def render(
        self,
        name: str,
        *,
        version: str,
        variables: dict[str, object],
        trace_id: str | None = None,
        pipeline_run_id: str | None = None,
        tokens: int | None = None,
    ) -> RenderResult:
        """Render one prompt version and record render analytics."""

        del pipeline_run_id
        self.sync_builtins()
        start_time = time.monotonic()
        event_id = uuid4().hex
        record = self._prompts.get_by_name_version(name, version)
        if record is None:
            raise orchestration_error(
                "Prompt version was not found in the registry",
                code="SS-ORCHESTRATION-208",
                details={"prompt_name": name, "prompt_version": version},
            )

        try:
            validate_prompt(
                template=record.template,
                variables=variables,
                variables_schema=record.variables_schema,
                output_schema=record.output_schema,
            )
            rendered = RenderedPrompt(
                name=record.prompt_id,
                version=record.version,
                content=record.template.format(**variables),
            )
        except PromptValidationError as exc:
            latency_ms = int((time.monotonic() - start_time) * 1000)
            error_code = f"SS-VALIDATION-PROMPT-{exc.stage.upper()}"
            self._prompts.record_render_event(
                event_id=event_id,
                prompt_version_id=record.id,
                success=False,
                latency_ms=latency_ms,
                tokens=tokens,
                error_code=error_code,
                trace_id=trace_id,
            )
            self._upsert_metrics(
                prompt_version_id=record.id,
                success=False,
                latency_ms=latency_ms,
                tokens=tokens or 0,
            )
            raise validation_error(
                "Prompt rendering failed validation",
                code=error_code,
                details={
                    "prompt_name": name,
                    "prompt_version": version,
                    "stage": exc.stage,
                    **exc.details,
                },
            ) from exc

        latency_ms = int((time.monotonic() - start_time) * 1000)
        self._prompts.record_render_event(
            event_id=event_id,
            prompt_version_id=record.id,
            success=True,
            latency_ms=latency_ms,
            tokens=tokens,
            error_code=None,
            trace_id=trace_id,
        )
        self._upsert_metrics(
            prompt_version_id=record.id,
            success=True,
            latency_ms=latency_ms,
            tokens=tokens or 0,
        )
        return RenderResult(
            rendered=rendered,
            event_id=event_id,
            latency_ms=latency_ms,
            success=True,
            prompt_version_id=record.id,
        )

    def ensure_seeded(self) -> None:
        """Ensure built-in prompts are present in the registry."""

        self.sync_builtins()

    def sync_builtins(self) -> None:
        """Synchronize built-in prompts into the registry, updating stale definitions."""

        self._prompts.sync_builtins(self._built_in_definitions())

    def _upsert_metrics(
        self,
        *,
        prompt_version_id: int,
        success: bool,
        latency_ms: int,
        tokens: int,
    ) -> None:
        existing = self._prompts.get_render_metrics(prompt_version_id)
        if existing is None:
            self._prompts.upsert_render_metrics(
                prompt_version_id=prompt_version_id,
                render_count=1,
                success_count=1 if success else 0,
                failure_count=0 if success else 1,
                avg_latency_ms=float(latency_ms),
                total_tokens=tokens,
            )
            return
        render_count = existing.render_count + 1
        success_count = existing.success_count + (1 if success else 0)
        failure_count = existing.failure_count + (0 if success else 1)
        total_tokens = existing.total_tokens + tokens
        weighted_latency = (
            ((existing.avg_latency_ms or 0.0) * existing.render_count) + latency_ms
        ) / render_count
        self._prompts.upsert_render_metrics(
            prompt_version_id=prompt_version_id,
            render_count=render_count,
            success_count=success_count,
            failure_count=failure_count,
            avg_latency_ms=weighted_latency,
            total_tokens=total_tokens,
        )

    def _built_in_definitions(self) -> Any:
        from soft_skills_backend.modules.admin.domain.builtin_prompts import (
            built_in_prompt_definitions,
        )

        return built_in_prompt_definitions(self._settings)
