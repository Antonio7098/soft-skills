from __future__ import annotations

import sys
from collections.abc import AsyncGenerator
from pathlib import Path

import httpx
import pytest
import pytest_asyncio

SRC_PATH = Path(__file__).resolve().parents[1] / "src"
src_str = str(SRC_PATH)
if src_str not in sys.path:
    sys.path.insert(0, src_str)

from soft_skills_backend.app import create_app
from soft_skills_backend.config import Settings


@pytest.fixture()
def test_settings(tmp_path: Path) -> Settings:
    return Settings(
        environment="test",
        database_url=f"sqlite+pysqlite:///{tmp_path / 'test.db'}",
    )


@pytest.fixture()
def app(test_settings: Settings):
    return create_app(test_settings)


@pytest_asyncio.fixture()
async def client(app) -> AsyncGenerator[httpx.AsyncClient, None]:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as async_client:
        yield async_client
