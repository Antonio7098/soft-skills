from __future__ import annotations

import httpx
import pytest
from fastapi import FastAPI

from soft_skills_backend.api.error_handlers import register_error_handlers
from soft_skills_backend.config import Settings
from soft_skills_backend.domain.errors import validation_error
from soft_skills_backend.observability.middleware import RequestContextMiddleware


@pytest.mark.asyncio
async def test_app_error_handler_returns_stable_envelope() -> None:
    app = FastAPI()
    app.add_middleware(RequestContextMiddleware)
    register_error_handlers(app, Settings(environment="test"))

    @app.get("/boom")
    async def boom() -> None:
        raise validation_error("Bad request", details={"field": "name"})

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get("/boom")
    payload = response.json()

    assert response.status_code == 422
    assert payload["error"]["code"] == "SS-VALIDATION-001"
    assert payload["error"]["category"] == "validation"
    assert payload["meta"]["request_id"]
    assert payload["meta"]["trace_id"]
