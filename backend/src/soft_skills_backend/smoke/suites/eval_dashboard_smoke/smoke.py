"""Evaluation dashboard smoke suite."""

from __future__ import annotations

import asyncio

from soft_skills_backend.config import Settings
from soft_skills_backend.platform.db.models import EvaluationRunRecord
from soft_skills_backend.shared.errors import provider_error
from soft_skills_backend.smoke.contracts import SmokeCase, SmokeContext
from soft_skills_backend.smoke.support.actors import SmokeActorBootstrap
from soft_skills_backend.smoke.support.environment import (
    ProviderSmokePreflight,
    SmokeApplicationSessionFactory,
)

from .contracts import EvalDashboardSmokeResult

SMOKE_FLOW_TIMEOUT_SECONDS = 420.0


class EvalDashboardSmoke(SmokeCase):
    """Run evaluation suites and verify dashboard APIs return correct aggregated data."""

    name = "eval-dashboard"
    description = "Run evaluation suites and verify dashboard, benchmark, and case-detail APIs."

    def __init__(
        self,
        *,
        preflight: ProviderSmokePreflight | None = None,
        session_factory: SmokeApplicationSessionFactory | None = None,
        flow_timeout_seconds: float = SMOKE_FLOW_TIMEOUT_SECONDS,
    ) -> None:
        self._preflight = preflight or ProviderSmokePreflight()
        self._session_factory = session_factory or SmokeApplicationSessionFactory()
        self._flow_timeout_seconds = flow_timeout_seconds

    def run(self, context: SmokeContext) -> EvalDashboardSmokeResult:
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

    async def _run(self, settings: Settings) -> EvalDashboardSmokeResult:
        async with self._session_factory.open(settings) as backend:
            actors = await SmokeActorBootstrap(backend).prepare()

            run_payload = await backend.run_evaluation(
                user_id=actors.admin_id,
                suite_id="marking_benchmark_v1",
                case_ids=["interview-pushback-01", "scenario-launch-tradeoff-02"],
            )
            run_id = str(run_payload["evaluation_run_id"])

            dashboard = await backend.get_evaluation_dashboard(user_id=actors.admin_id)
            if dashboard["total_runs"] < 1:
                raise provider_error(
                    "Dashboard did not show evaluation runs after execution",
                    code="SS-PROVIDER-023",
                    details={"total_runs": dashboard["total_runs"]},
                )

            benchmark = await backend.get_evaluation_benchmark(user_id=actors.admin_id)
            if benchmark["total_runs"] < 1:
                raise provider_error(
                    "Benchmark did not show evaluation runs after execution",
                    code="SS-PROVIDER-024",
                    details={"total_runs": benchmark["total_runs"]},
                )

            comparison = await backend.compare_evaluation_runs(
                user_id=actors.admin_id, run_ids=[run_id]
            )
            if comparison["run_count"] < 1:
                raise provider_error(
                    "Comparison did not find the evaluation run",
                    code="SS-PROVIDER-025",
                    details={"run_id": run_id, "run_count": comparison["run_count"]},
                )

            session_factory = backend.session_factory
            if session_factory is None:
                raise provider_error(
                    "Smoke backend session factory was unavailable",
                    code="SS-PROVIDER-021",
                    details={"operation": "eval dashboard smoke persistence checks"},
                )

            with session_factory() as session:
                persisted = session.get(EvaluationRunRecord, run_id)
                if persisted is None:
                    raise provider_error(
                        "Evaluation run was not persisted",
                        code="SS-PROVIDER-022",
                        details={"evaluation_run_id": run_id},
                    )

            return EvalDashboardSmokeResult(
                status="ok",
                evaluation_run_id=run_id,
                dashboard_total_runs=dashboard["total_runs"],
                benchmark_total_runs=benchmark["total_runs"],
                benchmark_model_count=len(benchmark.get("models", [])),
                comparison_run_count=comparison["run_count"],
            )
