"""Environment setup for smoke suites."""

from __future__ import annotations

import io
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager, redirect_stderr, redirect_stdout
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Protocol

import httpx

from soft_skills_backend.config import Settings
from soft_skills_backend.shared.errors import AppError, validation_error
from soft_skills_backend.shared.ports.models import ProviderCompletion
from soft_skills_backend.shared.ports.telemetry import ProviderCallContext

from .backend import SmokeBackendClient

SMOKE_PROVIDER_TIMEOUT_SECONDS = 60.0


class ProviderSmokePreflight:
    """Validates that provider-backed smoke execution can start."""

    def assert_ready(self, settings: Settings) -> None:
        try:
            self._build_provider(settings).assert_configured()
        except AppError as exc:
            raise validation_error(
                "Provider API key is required for smoke coverage",
                code="SS-VALIDATION-002",
            ) from exc

    def build_provider(self, settings: Settings) -> _ConfiguredProvider:
        return self._build_provider(settings)

    def _build_provider(self, settings: Settings) -> _ConfiguredProvider:
        from soft_skills_backend.platform.providers.llm.openai_compatible import (
            OpenAICompatibleLLMProvider,
        )

        return OpenAICompatibleLLMProvider(
            settings=settings,
            provider_call_logger=_NoOpProviderCallLogger(),
        )


class SmokeApplicationSessionFactory:
    """Builds an isolated backend application session for smoke execution."""

    def __init__(
        self,
        *,
        provider_max_retries: int = 0,
        assessment_validation_retries: int = 0,
    ) -> None:
        self._provider_max_retries = provider_max_retries
        self._assessment_validation_retries = assessment_validation_retries

    @asynccontextmanager
    async def open(self, settings: Settings) -> AsyncIterator[SmokeBackendClient]:
        from soft_skills_backend.app import create_app

        with TemporaryDirectory(prefix="soft-skills-smoke-") as temp_dir:
            smoke_settings = self._build_smoke_settings(settings, temp_dir)
            app = create_app(smoke_settings)
            self._migrate(smoke_settings)

            transport = httpx.ASGITransport(app=app)
            async with httpx.AsyncClient(
                transport=transport,
                base_url="http://testserver",
            ) as client:
                yield SmokeBackendClient(client)

    def _build_smoke_settings(self, settings: Settings, temp_dir: str) -> Settings:
        database_path = Path(temp_dir) / "smoke.db"
        return settings.model_copy(
            update={
                "environment": "test",
                "database_url": f"sqlite+pysqlite:///{database_path}",
                "smoke_timeout_seconds": SMOKE_PROVIDER_TIMEOUT_SECONDS,
                "provider_max_retries": self._provider_max_retries,
                "assessment_validation_retries": self._assessment_validation_retries,
            }
        )

    def _migrate(self, settings: Settings) -> None:
        from alembic.config import Config

        from alembic import command

        alembic_config = Config(str(Path(__file__).resolve().parents[4] / "alembic.ini"))
        alembic_config.set_main_option("sqlalchemy.url", settings.database_url)

        previous_levels = {
            logger_name: logging.getLogger(logger_name).level
            for logger_name in ("alembic", "alembic.runtime.plugins", "sqlalchemy")
        }
        for logger_name in previous_levels:
            logging.getLogger(logger_name).setLevel(logging.CRITICAL)

        buffer = io.StringIO()
        previous_disable = logging.root.manager.disable
        try:
            logging.disable(logging.CRITICAL)
            with redirect_stdout(buffer), redirect_stderr(buffer):
                command.upgrade(alembic_config, "head")
        finally:
            logging.disable(previous_disable)
            for logger_name, level in previous_levels.items():
                logging.getLogger(logger_name).setLevel(level)


class _NoOpProviderCallLogger:
    async def log_call_start(self, **_: object) -> str:
        return "smoke-preflight"

    async def log_call_end(self, _call_id: object, **_: object) -> None:
        return None


class _ConfiguredProvider(Protocol):
    def assert_configured(self) -> None: ...

    @property
    def provider_name(self) -> str: ...

    @property
    def model_slug(self) -> str: ...

    async def complete_json(
        self,
        *,
        messages: list[dict[str, str]],
        call_context: ProviderCallContext,
    ) -> ProviderCompletion: ...
