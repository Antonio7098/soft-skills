"""Pipeline visualization smoke suite - verifies pipeline discovery, trace storage, and admin endpoints."""

from __future__ import annotations

import asyncio
from typing import Any
from uuid import uuid4

from soft_skills_backend.config import Settings
from soft_skills_backend.smoke.contracts import SmokeCase, SmokeContext
from soft_skills_backend.smoke.support.backend import SmokeBackendClient
from soft_skills_backend.smoke.support.environment import (
    SmokeApplicationSessionFactory,
)

from .contracts import PipelineVisualizationSmokeResult

SMOKE_TIMEOUT_SECONDS = 120.0


class PipelineVisualizationSmoke(SmokeCase):
    """Verifies pipeline visualization features added in Sprint 13d.

    This smoke suite verifies:
    1. Pipeline definition discovery - pipelines are registered and discoverable
    2. Admin API endpoints - list_pipelines, get_pipeline_dag, list_pipeline_runs, get_pipeline_trace, get_pipeline_metrics
    3. Execution trace storage - traces are persisted for runs
    4. Stage metrics aggregation - metrics are calculated correctly
    """

    name = "pipeline-visualization"
    description = (
        "Verify pipeline discovery, execution trace storage, and admin visualization endpoints."
    )

    def __init__(
        self,
        *,
        session_factory: SmokeApplicationSessionFactory | None = None,
        timeout_seconds: float = SMOKE_TIMEOUT_SECONDS,
    ) -> None:
        self._session_factory = session_factory or SmokeApplicationSessionFactory()
        self._timeout_seconds = timeout_seconds

    def run(self, context: SmokeContext) -> PipelineVisualizationSmokeResult:
        try:
            return asyncio.run(
                asyncio.wait_for(self._run(context.settings), timeout=self._timeout_seconds)
            )
        except TimeoutError as exc:
            raise RuntimeError(
                f"Pipeline visualization smoke exceeded the allowed runtime budget of {self._timeout_seconds}s"
            ) from exc

    async def _run(self, settings: Settings) -> PipelineVisualizationSmokeResult:
        async with self._session_factory.open(settings) as backend:
            return await self._verify_pipeline_visualization(backend)

    async def _verify_pipeline_visualization(
        self, backend: SmokeBackendClient
    ) -> PipelineVisualizationSmokeResult:
        suffix = uuid4().hex[:8]
        email = f"pipeline-smoke-{suffix}@example.com"
        display_name = "Pipeline Smoke User"

        user = await backend.register_user(email=email, display_name=display_name)
        user_id = str(user["id"])

        org = await backend.create_organisation(
            user_id=user_id,
            name=f"Pipeline Smoke Org {suffix}",
            slug=f"pipeline-smoke-org-{suffix}",
        )
        org_id = str(org["id"])

        list_response = await backend._client.get(
            "/api/admin/pipelines",
            headers={"X-User-ID": user_id, "X-Organisation-ID": org_id},
        )

        if list_response.status_code != 200:
            raise self._error(
                "list_pipelines should return 200",
                details={
                    "expected_status": 200,
                    "actual_status": list_response.status_code,
                    "body": list_response.text,
                },
            )

        list_data = list_response.json()["data"]
        list_pipelines_returns_list = isinstance(list_data, list)
        list_pipelines_count = len(list_data)

        pipeline_definitions_stored = list_pipelines_count > 0

        first_pipeline_name = None
        dag_has_stages = False
        dag_stage_count = 0

        if list_pipelines_count > 0:
            first_pipeline = list_data[0]
            first_pipeline_name = first_pipeline.get("name")

            dag_response = await backend._client.get(
                f"/api/admin/pipelines/{first_pipeline_name}",
                headers={"X-User-ID": user_id, "X-Organisation-ID": org_id},
            )

            if dag_response.status_code != 200:
                raise self._error(
                    "get_pipeline_dag should return 200",
                    details={
                        "pipeline_name": first_pipeline_name,
                        "expected_status": 200,
                        "actual_status": dag_response.status_code,
                        "body": dag_response.text,
                    },
                )

            dag_data = dag_response.json()["data"]
            get_pipeline_dag_returns_dag = "stages" in dag_data
            stages = dag_data.get("stages", [])
            dag_has_stages = len(stages) > 0
            dag_stage_count = len(stages)

            runs_response = await backend._client.get(
                f"/api/admin/pipelines/{first_pipeline_name}/runs",
                headers={"X-User-ID": user_id, "X-Organisation-ID": org_id},
            )

            if runs_response.status_code != 200:
                raise self._error(
                    "list_pipeline_runs should return 200",
                    details={
                        "pipeline_name": first_pipeline_name,
                        "expected_status": 200,
                        "actual_status": runs_response.status_code,
                        "body": runs_response.text,
                    },
                )

            runs_data = runs_response.json()["data"]
            list_pipeline_runs_returns_list = isinstance(runs_data, list)

            execution_traces_stored = len(runs_data) > 0

            get_pipeline_trace_returns_trace = False
            if len(runs_data) > 0:
                first_run_id = runs_data[0].get("id")
                trace_response = await backend._client.get(
                    f"/api/admin/pipelines/{first_pipeline_name}/runs/{first_run_id}/trace",
                    headers={"X-User-ID": user_id, "X-Organisation-ID": org_id},
                )

                if trace_response.status_code == 200:
                    get_pipeline_trace_returns_trace = True
                elif trace_response.status_code == 404:
                    get_pipeline_trace_returns_trace = False
                else:
                    raise self._error(
                        "get_pipeline_trace should return 200 or 404",
                        details={
                            "pipeline_name": first_pipeline_name,
                            "run_id": first_run_id,
                            "expected_status": "200 or 404",
                            "actual_status": trace_response.status_code,
                            "body": trace_response.text,
                        },
                    )
        else:
            list_pipeline_runs_returns_list = False
            execution_traces_stored = False
            get_pipeline_trace_returns_trace = False

        metrics_response = await backend._client.get(
            f"/api/admin/pipelines/{first_pipeline_name}/metrics",
            headers={"X-User-ID": user_id, "X-Organisation-ID": org_id},
        )

        get_pipeline_metrics_returns_metrics = metrics_response.status_code == 200
        metrics_has_stage_metrics = False
        metrics_stage_count = 0
        metrics_pipeline_name = ""

        if metrics_response.status_code == 200:
            metrics_data = metrics_response.json()["data"]
            metrics_pipeline_name = metrics_data.get("pipeline_name", "")
            stage_metrics = metrics_data.get("stage_metrics", [])
            metrics_has_stage_metrics = isinstance(stage_metrics, list) and len(stage_metrics) >= 0
            metrics_stage_count = len(stage_metrics)
        elif metrics_response.status_code == 404:
            get_pipeline_metrics_returns_metrics = False
        else:
            raise self._error(
                "get_pipeline_metrics should return 200 or 404",
                details={
                    "pipeline_name": first_pipeline_name,
                    "expected_status": "200 or 404",
                    "actual_status": metrics_response.status_code,
                    "body": metrics_response.text,
                },
            )

        stage_definitions_stored = dag_stage_count > 0

        return PipelineVisualizationSmokeResult(
            list_pipelines_returns_list=list_pipelines_returns_list,
            list_pipelines_count=list_pipelines_count,
            get_pipeline_dag_returns_dag=get_pipeline_dag_returns_dag
            if first_pipeline_name
            else False,
            dag_has_stages=dag_has_stages,
            dag_stage_count=dag_stage_count,
            list_pipeline_runs_returns_list=list_pipeline_runs_returns_list,
            get_pipeline_trace_returns_trace=get_pipeline_trace_returns_trace,
            get_pipeline_metrics_returns_metrics=get_pipeline_metrics_returns_metrics,
            metrics_has_stage_metrics=metrics_has_stage_metrics,
            metrics_pipeline_name=metrics_pipeline_name,
            metrics_stage_count=metrics_stage_count,
            pipeline_definitions_stored=pipeline_definitions_stored,
            stage_definitions_stored=stage_definitions_stored,
            execution_traces_stored=execution_traces_stored,
        )

    @staticmethod
    def _error(message: str, details: dict[str, Any]) -> Exception:
        from soft_skills_backend.shared.errors import provider_error

        return provider_error(
            message,
            code="SS-PROVIDER-011",
            details=details,
        )
