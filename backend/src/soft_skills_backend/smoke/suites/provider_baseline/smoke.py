"""Direct low-level provider smoke suite."""

from __future__ import annotations

import asyncio

from soft_skills_backend.config import Settings
from soft_skills_backend.shared.errors import provider_error
from soft_skills_backend.shared.ports.telemetry import ProviderCallContext
from soft_skills_backend.smoke.contracts import SmokeCase, SmokeContext
from soft_skills_backend.smoke.support.environment import ProviderSmokePreflight

from .contracts import ProviderBaselineSmokeResult

SMOKE_FLOW_TIMEOUT_SECONDS = 120.0


class ProviderBaselineSmoke(SmokeCase):
    """Validate the base LLM provider path independently of app workflows."""

    name = "provider-baseline"
    description = "Validate the base JSON LLM provider adapter against the configured provider."

    def __init__(
        self,
        *,
        preflight: ProviderSmokePreflight | None = None,
        flow_timeout_seconds: float = SMOKE_FLOW_TIMEOUT_SECONDS,
    ) -> None:
        self._preflight = preflight or ProviderSmokePreflight()
        self._flow_timeout_seconds = flow_timeout_seconds

    def run(self, context: SmokeContext) -> ProviderBaselineSmokeResult:
        self._preflight.assert_ready(context.settings)
        try:
            return asyncio.run(
                asyncio.wait_for(self._run(context.settings), timeout=self._flow_timeout_seconds)
            )
        except TimeoutError as exc:
            raise provider_error(
                "Smoke flow exceeded the allowed runtime budget",
                code="SS-PROVIDER-012",
                details={"timeout_seconds": self._flow_timeout_seconds},
            ) from exc

    async def _run(self, settings: Settings) -> ProviderBaselineSmokeResult:
        provider = self._preflight.build_provider(settings)
        completion = await provider.complete_json(
            messages=[
                {
                    "role": "system",
                    "content": "Return a compact JSON object.",
                },
                {
                    "role": "user",
                    "content": 'Respond only with JSON containing {"status":"ok","kind":"provider_smoke"}.',
                },
            ],
            call_context=ProviderCallContext(
                operation="provider_smoke",
                request_id="provider-smoke",
                trace_id="provider-smoke",
                pipeline_run_id="provider-smoke",
                workflow_id="provider-smoke",
                user_id="provider-smoke",
            ),
        )
        preview = completion.content if isinstance(completion.content, str) else str(completion.content)
        return ProviderBaselineSmokeResult(
            status="ok",
            provider=provider.provider_name,
            model_slug=completion.model_slug,
            response_preview=preview[:160],
        )


def run_provider_smoke(settings: Settings | None = None) -> ProviderBaselineSmokeResult:
    """Execute the provider baseline smoke suite."""

    return ProviderBaselineSmoke().run(SmokeContext.create(settings))
