from __future__ import annotations

from pathlib import Path

import pytest
from alembic.config import Config

from alembic import command


@pytest.mark.asyncio
async def test_readiness_endpoint_reports_database_and_correlation_headers(
    client, test_settings
) -> None:
    alembic_config = Config(str(Path(__file__).resolve().parents[2] / "alembic.ini"))
    alembic_config.set_main_option("sqlalchemy.url", test_settings.database_url)
    command.upgrade(alembic_config, "heads")

    response = await client.get("/api/health/readiness")
    payload = response.json()

    assert response.status_code == 200
    assert response.headers["X-Request-ID"]
    assert response.headers["X-Trace-ID"]
    assert payload["data"]["checks"]["database"]["status"] == "ready"
    assert isinstance(payload["data"]["stageflow"]["installed"], bool)
    assert payload["data"]["stageflow"]["pipeline_type"] == "Pipeline"
