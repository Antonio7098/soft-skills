"""Unit tests for pipeline registry."""

from __future__ import annotations

from soft_skills_backend.platform.workflows.pipeline_registry import (
    DiscoveredPipeline,
    PipelineRegistry,
    register_pipeline,
)


class TestPipelineRegistry:
    """Tests for PipelineRegistry singleton."""

    def setup_method(self) -> None:
        PipelineRegistry.reset()

    def test_singleton_pattern(self) -> None:
        """Registry should be a singleton."""
        reg1 = PipelineRegistry()
        reg2 = PipelineRegistry()
        assert reg1 is reg2

    def test_register_and_get_pipeline(self) -> None:
        """Should register a pipeline and retrieve it."""
        pipeline = DiscoveredPipeline(
            name="test-pipeline",
            topology="test-topology",
            description="Test description",
            stages=[],
        )
        registry = PipelineRegistry()
        registry.register(pipeline)

        retrieved = registry.get("test-pipeline")
        assert retrieved is not None
        assert retrieved.name == "test-pipeline"
        assert retrieved.topology == "test-topology"
        assert retrieved.description == "Test description"

    def test_get_nonexistent_pipeline(self) -> None:
        """Should return None for unregistered pipeline."""
        registry = PipelineRegistry()
        assert registry.get("nonexistent") is None

    def test_list_all_pipelines(self) -> None:
        """Should list all registered pipelines."""
        pipeline1 = DiscoveredPipeline(name="pipeline-1", stages=[])
        pipeline2 = DiscoveredPipeline(name="pipeline-2", stages=[])
        registry = PipelineRegistry()
        registry.register(pipeline1)
        registry.register(pipeline2)

        all_pipelines = registry.list_all()
        assert len(all_pipelines) == 2
        names = {p.name for p in all_pipelines}
        assert names == {"pipeline-1", "pipeline-2"}

    def test_to_records(self) -> None:
        """Should convert registered pipelines to database records."""
        pipeline = DiscoveredPipeline(
            name="test-pipeline",
            topology="test-topology",
            description="Test description",
            stages=[
                {
                    "name": "stage-1",
                    "kind": "WORK",
                    "dependencies": [],
                    "runner_class": "TestRunner",
                },
                {
                    "name": "stage-2",
                    "kind": "TRANSFORM",
                    "dependencies": ["stage-1"],
                    "runner_class": "AnotherRunner",
                },
            ],
        )
        registry = PipelineRegistry()
        registry.register(pipeline)

        pipeline_records, stage_records = registry.to_records()

        assert len(pipeline_records) == 1
        pipeline_record = pipeline_records[0]
        assert pipeline_record.pipeline_name == "test-pipeline"
        assert pipeline_record.topology == "test-topology"
        assert pipeline_record.description == "Test description"

        assert len(stage_records) == 2
        stage1 = next(s for s in stage_records if s.stage_name == "stage-1")
        stage2 = next(s for s in stage_records if s.stage_name == "stage-2")

        assert stage1.stage_kind == "WORK"
        assert stage1.dependencies == []
        assert stage1.runner_class == "TestRunner"

        assert stage2.stage_kind == "TRANSFORM"
        assert stage2.dependencies == ["stage-1"]
        assert stage2.runner_class == "AnotherRunner"

    def test_reset_clears_pipelines(self) -> None:
        """Reset should clear all registered pipelines."""
        pipeline = DiscoveredPipeline(name="test-pipeline", stages=[])
        registry = PipelineRegistry()
        registry.register(pipeline)

        PipelineRegistry.reset()

        new_registry = PipelineRegistry()
        assert new_registry.list_all() == []


class TestRegisterPipelineHelper:
    """Tests for register_pipeline helper function."""

    def setup_method(self) -> None:
        PipelineRegistry.reset()

    def test_register_pipeline_helper(self) -> None:
        """register_pipeline should register pipeline with global registry."""
        register_pipeline(
            name="helper-pipeline",
            stages=[
                {"name": "stage-1", "kind": "WORK", "dependencies": []},
            ],
            topology="helper-topology",
            description="Helper test",
        )

        registry = PipelineRegistry()
        pipeline = registry.get("helper-pipeline")
        assert pipeline is not None
        assert pipeline.name == "helper-pipeline"
        assert pipeline.topology == "helper-topology"
        assert pipeline.description == "Helper test"
        assert len(pipeline.stages) == 1

    def test_register_pipeline_defaults_topology_to_name(self) -> None:
        """If topology not provided, should default to pipeline name."""
        register_pipeline(
            name="my-pipeline",
            stages=[],
        )

        registry = PipelineRegistry()
        pipeline = registry.get("my-pipeline")
        assert pipeline is not None
        assert pipeline.topology == "my-pipeline"


class TestDiscoveredPipeline:
    """Tests for DiscoveredPipeline dataclass."""

    def test_discovered_pipeline_creation(self) -> None:
        """Should create DiscoveredPipeline with all fields."""
        pipeline = DiscoveredPipeline(
            name="test",
            topology="test-topo",
            description="Test pipeline",
            stages=[{"name": "s1", "kind": "WORK", "dependencies": []}],
        )
        assert pipeline.name == "test"
        assert pipeline.topology == "test-topo"
        assert pipeline.description == "Test pipeline"
        assert len(pipeline.stages) == 1

    def test_discovered_pipeline_defaults(self) -> None:
        """Should have sensible defaults."""
        pipeline = DiscoveredPipeline(name="minimal")
        assert pipeline.topology is None
        assert pipeline.description is None
        assert pipeline.stages == []
