"""Pipeline registry for discovery and visualization."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from soft_skills_backend.platform.db.models import (
    PipelineDefinitionRecord,
    StageDefinitionRecord,
)


@dataclass
class DiscoveredPipeline:
    """A discovered pipeline with its stage definitions."""

    name: str
    topology: str | None = None
    description: str | None = None
    stages: list[dict[str, Any]] = field(default_factory=list)


class PipelineRegistry:
    """Central registry for pipeline definitions.

    Pipelines register themselves at startup to enable:
    - Pipeline DAG visualization
    - Execution trace storage
    - Stage metrics aggregation
    """

    _instance: PipelineRegistry | None = None
    _pipelines: dict[str, DiscoveredPipeline] = {}

    def __new__(cls) -> PipelineRegistry:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._pipelines = {}
        return cls._instance

    @classmethod
    def reset(cls) -> None:
        """Reset the registry (for testing)."""
        cls._instance = None
        cls._pipelines = {}

    def register(self, pipeline: DiscoveredPipeline) -> None:
        """Register a pipeline definition."""
        self._pipelines[pipeline.name] = pipeline

    def get(self, name: str) -> DiscoveredPipeline | None:
        """Get a pipeline by name."""
        return self._pipelines.get(name)

    def list_all(self) -> list[DiscoveredPipeline]:
        """List all registered pipelines."""
        return list(self._pipelines.values())

    def to_records(self) -> tuple[list[PipelineDefinitionRecord], list[StageDefinitionRecord]]:
        """Convert all registered pipelines to database records.

        Returns a tuple of (pipeline_definitions, stage_definitions).
        """
        now = datetime.now(UTC)
        pipeline_records: dict[str, PipelineDefinitionRecord] = {}
        stage_records: list[StageDefinitionRecord] = []

        for pipeline in self._pipelines.values():
            stage_defs = []
            for stage_info in pipeline.stages:
                stage_def = StageDefinitionRecord(
                    pipeline_name=pipeline.name,
                    stage_name=stage_info["name"],
                    stage_kind=stage_info["kind"],
                    dependencies=stage_info.get("dependencies", []),
                    runner_class=stage_info.get("runner_class"),
                    description=stage_info.get("description"),
                )
                stage_records.append(stage_def)
                stage_defs.append(
                    {
                        "name": stage_info["name"],
                        "kind": stage_info["kind"],
                        "dependencies": stage_info.get("dependencies", []),
                        "runner_class": stage_info.get("runner_class"),
                    }
                )

            pipeline_records[pipeline.name] = PipelineDefinitionRecord(
                pipeline_name=pipeline.name,
                topology=pipeline.topology or pipeline.name,
                description=pipeline.description,
                stage_definitions=stage_defs,
                created_at=now,
                updated_at=now,
            )

        return list(pipeline_records.values()), stage_records


def register_pipeline(
    name: str,
    stages: list[dict[str, Any]],
    topology: str | None = None,
    description: str | None = None,
) -> None:
    """Register a pipeline with the global registry.

    Args:
        name: The pipeline name
        stages: List of stage definitions with keys: name, kind, dependencies, runner_class
        topology: Optional topology name
        description: Optional description
    """
    pipeline = DiscoveredPipeline(
        name=name,
        topology=topology or name,
        description=description,
        stages=stages,
    )
    PipelineRegistry().register(pipeline)
