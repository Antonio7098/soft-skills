"""Evaluation smoke suite."""

from __future__ import annotations

import asyncio

from soft_skills_backend.config import Settings
from soft_skills_backend.platform.db.models import EvaluationCaseResultRecord, EvaluationRunRecord
from soft_skills_backend.shared.errors import provider_error
from soft_skills_backend.smoke.contracts import SmokeCase, SmokeContext
from soft_skills_backend.smoke.support.actors import SmokeActorBootstrap
from soft_skills_backend.smoke.support.environment import (
    ProviderSmokePreflight,
    SmokeApplicationSessionFactory,
)

from .contracts import EvaluationSmokeResult, EvaluationSuiteSmokeItem

SMOKE_FLOW_TIMEOUT_SECONDS = 420.0


class EvaluationSmoke(SmokeCase):
    """Run both admin evaluation suites end to end."""

    name = "evaluation-benchmark"
    description = "Run rich-score and quick-practice evaluation suites end to end."

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

    def run(self, context: SmokeContext) -> EvaluationSmokeResult:
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

    async def _run(self, settings: Settings) -> EvaluationSmokeResult:
        async with self._session_factory.open(settings) as backend:
            actors = await SmokeActorBootstrap(backend).prepare()
            suites = await backend.list_evaluation_suites(user_id=actors.admin_id)
            suite_ids = {str(item["suite_id"]) for item in suites}
            required_suite_ids = {"marking_benchmark_v1", "quick_practice_benchmark_v1"}
            if not required_suite_ids.issubset(suite_ids):
                raise provider_error(
                    "Expected evaluation suites were not registered",
                    code="SS-PROVIDER-020",
                    details={
                        "required_suite_ids": sorted(required_suite_ids),
                        "available_suite_ids": sorted(suite_ids),
                    },
                )

            run_payloads = [
                await backend.run_evaluation(
                    user_id=actors.admin_id,
                    suite_id="marking_benchmark_v1",
                    case_ids=["interview-pushback-01", "scenario-launch-tradeoff-02"],
                ),
                await backend.run_evaluation(
                    user_id=actors.admin_id,
                    suite_id="quick_practice_benchmark_v1",
                    case_ids=["quick-reset-deadline-01", "quick-vague-reassurance-02"],
                ),
            ]

            items: list[EvaluationSuiteSmokeItem] = []
            session_factory = backend.session_factory
            if session_factory is None:
                raise provider_error(
                    "Smoke backend session factory was unavailable",
                    code="SS-PROVIDER-021",
                    details={"operation": "evaluation smoke persistence checks"},
                )
            with session_factory() as session:
                for payload in run_payloads:
                    run_id = str(payload["evaluation_run_id"])
                    persisted = session.get(EvaluationRunRecord, run_id)
                    if persisted is None:
                        raise provider_error(
                            "Evaluation smoke could not load the persisted run",
                            code="SS-PROVIDER-022",
                            details={"evaluation_run_id": run_id},
                        )
                    case_result_count = (
                        session.query(EvaluationCaseResultRecord)
                        .filter(EvaluationCaseResultRecord.evaluation_run_id == run_id)
                        .count()
                    )
                    selected_case_count = int(persisted.summary.get("selected_case_count", 0))
                    items.append(
                        EvaluationSuiteSmokeItem(
                            suite_id=persisted.suite_id,
                            evaluation_run_id=run_id,
                            benchmark_set_version=persisted.benchmark_set_version,
                            selected_case_count=selected_case_count,
                            case_result_count=case_result_count,
                            passed=bool(persisted.passed),
                            total_tokens=int(persisted.aggregate_metrics.get("total_tokens", 0)),
                        )
                    )

            return EvaluationSmokeResult(
                status="ok",
                available_suite_ids=sorted(suite_ids),
                runs=items,
            )
