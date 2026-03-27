"""Pipeline visualization smoke suite contracts."""

from __future__ import annotations

from pydantic import BaseModel


class PipelineVisualizationSmokeResult(BaseModel):
    """Result of the pipeline visualization smoke suite."""

    list_pipelines_returns_list: bool
    list_pipelines_count: int
    get_pipeline_dag_returns_dag: bool
    dag_has_stages: bool
    dag_stage_count: int
    list_pipeline_runs_returns_list: bool
    get_pipeline_trace_returns_trace: bool
    get_pipeline_metrics_returns_metrics: bool
    metrics_has_stage_metrics: bool
    metrics_pipeline_name: str
    metrics_stage_count: int
    pipeline_definitions_stored: bool
    stage_definitions_stored: bool
    execution_traces_stored: bool
