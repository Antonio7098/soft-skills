"""Application factory and ASGI entrypoint."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from soft_skills_backend.config import Settings, get_settings
from soft_skills_backend.entrypoints.http.error_handlers import register_error_handlers
from soft_skills_backend.entrypoints.http.router import api_router
from soft_skills_backend.platform.container import AppContainer, build_container
from soft_skills_backend.platform.observability.logging import configure_logging, get_logger
from soft_skills_backend.platform.observability.middleware import RequestContextMiddleware


def create_app(settings: Settings | None = None, container: AppContainer | None = None) -> FastAPI:
    """Create a configured FastAPI application."""

    resolved_settings = settings or get_settings()
    configure_logging(resolved_settings.log_level)
    resolved_container = container or build_container(resolved_settings)
    logger = get_logger("soft_skills_backend.app")

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        resolved_container.background_tasks.attach(asyncio.get_running_loop())
        logger.info(
            "application.startup",
            environment=resolved_settings.environment,
            database_url=resolved_settings.database_url,
            stageflow_installed=resolved_container.stageflow_runtime.installed,
        )
        try:
            yield
        finally:
            await resolved_container.background_tasks.shutdown()
            resolved_container.dispose()
            logger.info("application.shutdown")

    app = FastAPI(
        title=resolved_settings.app_name,
        description="AI-driven simulation, assessment, and progression platform",
        version=resolved_settings.app_version,
        lifespan=lifespan,
    )
    app.state.container = resolved_container

    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(resolved_settings.cors_allowed_origins),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(RequestContextMiddleware)

    register_error_handlers(app, resolved_settings)
    app.include_router(api_router, prefix=resolved_settings.api_prefix)

    @app.get("/", tags=["root"])
    async def root() -> dict[str, str]:
        return {
            "message": resolved_settings.app_name,
            "version": resolved_settings.app_version,
            "environment": resolved_settings.environment,
        }

    return app


app = create_app()
