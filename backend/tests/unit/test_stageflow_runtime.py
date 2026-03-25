from __future__ import annotations

import importlib.util

import pytest

from soft_skills_backend.application.container import build_container
from soft_skills_backend.config import Settings


def test_stageflow_runtime_reports_missing_dependency(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(importlib.util, "find_spec", lambda name: None if name == "stageflow" else None)

    settings = Settings(
        environment="test",
        database_url=f"sqlite+pysqlite:///{tmp_path / 'stageflow.db'}",
        stageflow_required=False,
    )
    container = build_container(settings)

    assert container.stageflow_runtime.installed is False
    assert "stageflow-core" in str(container.stageflow_runtime.missing_reason)

    container.dispose()


def test_stageflow_runtime_reports_available_dependency(tmp_path) -> None:
    settings = Settings(
        environment="test",
        database_url=f"sqlite+pysqlite:///{tmp_path / 'stageflow-present.db'}",
        stageflow_required=False,
    )
    container = build_container(settings)

    if container.stageflow_runtime.installed:
        assert container.stageflow_runtime.pipeline_type_name == "Pipeline"
        assert "LoggingInterceptor" in container.stageflow_runtime.default_interceptor_names
        assert container.stageflow_runtime.runtime_objects is not None
    else:
        pytest.skip("Stageflow is not installed in this interpreter")

    container.dispose()
