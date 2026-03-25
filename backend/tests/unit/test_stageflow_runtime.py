from __future__ import annotations

import importlib

import pytest

from soft_skills_backend.application.container import build_container
from soft_skills_backend.config import Settings
from soft_skills_backend.domain.errors import AppError


def test_stageflow_runtime_requires_dependency(monkeypatch, tmp_path) -> None:
    real_import_module = importlib.import_module

    def _import_module(name: str, package: str | None = None):
        if name.startswith("stageflow"):
            raise ModuleNotFoundError(name)
        return real_import_module(name, package)

    monkeypatch.setattr(importlib, "import_module", _import_module)

    settings = Settings(
        environment="test", database_url=f"sqlite+pysqlite:///{tmp_path / 'stageflow.db'}"
    )
    with pytest.raises(AppError) as exc_info:
        build_container(settings)

    assert exc_info.value.code == "SS-ORCHESTRATION-002"


def test_stageflow_runtime_reports_available_dependency(tmp_path) -> None:
    settings = Settings(
        environment="test", database_url=f"sqlite+pysqlite:///{tmp_path / 'stageflow-present.db'}"
    )
    container = build_container(settings)

    assert container.stageflow_runtime.installed is True
    assert container.stageflow_runtime.pipeline_type_name == "Pipeline"
    assert "LoggingInterceptor" in container.stageflow_runtime.default_interceptor_names
    assert container.stageflow_runtime.runtime_objects is not None

    container.dispose()
