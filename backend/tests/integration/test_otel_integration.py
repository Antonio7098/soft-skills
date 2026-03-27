"""Tests for OpenTelemetry integration and telemetry module."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from pathlib import Path

import httpx
import pytest
import pytest_asyncio
from alembic.config import Config

from alembic import command
from soft_skills_backend.app import create_app
from soft_skills_backend.config import Settings


@pytest.fixture()
def test_settings_with_otel(tmp_path: Path) -> Settings:
    return Settings(
        environment="test",
        database_url=f"sqlite+pysqlite:///{tmp_path / 'test.db'}",
        otel_enabled=True,
        otel_service_name="test-service",
        otel_exporter_otlp_endpoint="http://localhost:4317",
    )


@pytest.fixture()
def test_settings_without_otel(tmp_path: Path) -> Settings:
    return Settings(
        environment="test",
        database_url=f"sqlite+pysqlite:///{tmp_path / 'test.db'}",
        otel_enabled=False,
    )


@pytest.fixture()
def app_with_otel(test_settings_with_otel: Settings):
    return create_app(test_settings_with_otel)


@pytest.fixture()
def app_without_otel(test_settings_without_otel: Settings):
    return create_app(test_settings_without_otel)


@pytest_asyncio.fixture()
async def client_with_otel(app_with_otel) -> AsyncGenerator[httpx.AsyncClient, None]:
    transport = httpx.ASGITransport(app=app_with_otel)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as async_client:
        yield async_client


@pytest_asyncio.fixture()
async def client_without_otel(app_without_otel) -> AsyncGenerator[httpx.AsyncClient, None]:
    transport = httpx.ASGITransport(app=app_without_otel)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as async_client:
        yield async_client


@pytest.mark.asyncio
async def test_liveness_endpoint_includes_otel_info(
    client_without_otel,
    test_settings_without_otel,
) -> None:
    response = await client_without_otel.get("/api/health/liveness")
    payload = response.json()

    assert response.status_code == 200
    assert payload["data"]["status"] == "alive"
    assert payload["data"]["otel"]["enabled"] is False
    assert payload["data"]["otel"]["service_name"] == test_settings_without_otel.otel_service_name


@pytest.mark.asyncio
async def test_readiness_endpoint_includes_otel_checks(
    client_without_otel,
    test_settings_without_otel,
) -> None:
    alembic_config = Config(str(Path(__file__).resolve().parents[2] / "alembic.ini"))
    alembic_config.set_main_option("sqlalchemy.url", test_settings_without_otel.database_url)
    command.upgrade(alembic_config, "head")

    response = await client_without_otel.get("/api/health/readiness")
    payload = response.json()

    assert response.status_code == 200
    assert payload["data"]["otel"]["enabled"] is False
    assert "otel_exporter" in payload["data"]["checks"]


@pytest.mark.asyncio
async def test_trace_context_propagation_headers_present(
    client_without_otel,
) -> None:
    response = await client_without_otel.get("/api/health/liveness")

    assert response.status_code == 200
    assert response.headers.get("X-Request-ID")
    assert response.headers.get("X-Trace-ID")
    assert response.headers.get("traceparent") is not None


@pytest.mark.asyncio
async def test_trace_context_injected_in_response(
    client_without_otel,
) -> None:
    response = await client_without_otel.get("/api/health/liveness")

    assert response.status_code == 200
    traceparent = response.headers.get("traceparent")
    assert traceparent is not None
    parts = traceparent.split("-")
    assert len(parts) == 4
    assert parts[0] == "00"
    assert len(parts[1]) == 32
    assert parts[3] == "01"
