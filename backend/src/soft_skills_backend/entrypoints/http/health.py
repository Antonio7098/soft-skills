"""Health service for readiness and liveness checks."""

from __future__ import annotations

from pydantic import BaseModel
from sqlalchemy.orm import Session, sessionmaker

from soft_skills_backend.config import Settings
from soft_skills_backend.platform.db.session import ping_database
from soft_skills_backend.platform.workflows.stageflow_runtime import StageflowRuntime


class HealthCheck(BaseModel):
    """A single health check outcome."""

    status: str
    detail: str


class ReadinessPayload(BaseModel):
    """Readiness response body."""

    status: str
    service: str
    version: str
    environment: str
    checks: dict[str, HealthCheck]
    stageflow: dict[str, str | bool | list[str]]
    otel: dict[str, str | bool]


class HealthService:
    """Evaluate foundational service health."""

    def __init__(
        self,
        *,
        settings: Settings,
        session_factory: sessionmaker[Session],
        stageflow_runtime: StageflowRuntime,
    ) -> None:
        self._settings = settings
        self._session_factory = session_factory
        self._stageflow_runtime = stageflow_runtime

    def liveness(self) -> ReadinessPayload:
        """Return a minimal liveness payload."""

        return ReadinessPayload(
            status="alive",
            service=self._settings.app_name,
            version=self._settings.app_version,
            environment=self._settings.environment,
            checks={},
            stageflow={
                "installed": self._stageflow_runtime.installed,
                "pipeline_type": self._stageflow_runtime.pipeline_type_name,
            },
            otel={
                "enabled": self._settings.otel_enabled,
                "service_name": self._settings.otel_service_name,
            },
        )

    def readiness(self) -> ReadinessPayload:
        """Return detailed readiness information."""

        database_check = HealthCheck(status="ready", detail="database roundtrip succeeded")
        try:
            ping_database(self._session_factory)
        except Exception as exc:
            database_check = HealthCheck(status="failed", detail=str(exc))

        otel_endpoint_check = HealthCheck(status="ready", detail="OTLP endpoint not configured")
        if self._settings.otel_enabled and self._settings.otel_exporter_otlp_endpoint:
            otel_endpoint_check = HealthCheck(
                status="configured",
                detail=f"OTLP endpoint: {self._settings.otel_exporter_otlp_endpoint}",
            )
        elif not self._settings.otel_enabled:
            otel_endpoint_check = HealthCheck(status="disabled", detail="OpenTelemetry is disabled")

        overall_status = "ready"
        if database_check.status != "ready":
            overall_status = "degraded"

        return ReadinessPayload(
            status=overall_status,
            service=self._settings.app_name,
            version=self._settings.app_version,
            environment=self._settings.environment,
            checks={
                "database": database_check,
                "otel_exporter": otel_endpoint_check,
            },
            stageflow={
                "installed": self._stageflow_runtime.installed,
                "status": "ready",
                "pipeline_type": self._stageflow_runtime.pipeline_type_name,
                "pipeline_context_type": self._stageflow_runtime.pipeline_context_type_name,
                "interceptor_names": list(self._stageflow_runtime.default_interceptor_names),
            },
            otel={
                "enabled": self._settings.otel_enabled,
                "service_name": self._settings.otel_service_name,
                "endpoint": self._settings.otel_exporter_otlp_endpoint or "not configured",
            },
        )
