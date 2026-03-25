"""Application settings."""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration."""

    model_config = SettingsConfigDict(
        env_prefix="SOFT_SKILLS_",
        env_file=".env",
        extra="ignore",
    )

    app_name: str = "SoftSkills Backend"
    app_version: str = "0.1.0"
    environment: str = "local"
    api_prefix: str = "/api"
    cors_allowed_origins: tuple[str, ...] = ("*",)
    database_url: str = "sqlite+pysqlite:///./softskills.db"
    log_level: str = "INFO"
    stageflow_required: bool = False
    stageflow_event_queue_size: int = Field(default=1000, ge=1)
    provider_name: str = "openai"
    provider_base_url: str = "https://api.openai.com/v1"
    provider_model_slug: str = "gpt-4.1-mini"
    provider_api_key: str | None = None
    openrouter_api_key: str | None = Field(
        default=None,
        validation_alias="OPENROUTER_API_KEY",
    )
    openrouter_base_url: str = Field(
        default="https://openrouter.ai/api/v1",
        validation_alias="OPENROUTER_BASE_URL",
    )
    llm_marking_model: str | None = Field(
        default=None,
        validation_alias="LLM_MARKING_MODEL",
    )
    smoke_timeout_seconds: float = Field(default=10.0, gt=0)
    provider_max_retries: int = Field(default=2, ge=0, le=5)
    provider_retry_backoff_seconds: float = Field(default=0.25, gt=0, le=10.0)
    assessment_prompt_version: str = "assessment.quick-practice.v1"
    assessment_output_schema_version: str = "quick-practice-assessment-output.v1"
    scoring_config_version: str = "quick-practice-marking-config.v1"
    assessment_validation_retries: int = Field(default=1, ge=0, le=3)

    @field_validator("cors_allowed_origins", mode="before")
    @classmethod
    def _normalize_cors_allowed_origins(
        cls, value: str | tuple[str, ...] | list[str]
    ) -> tuple[str, ...]:
        if isinstance(value, str):
            return tuple(part.strip() for part in value.split(",") if part.strip())
        return tuple(value)

    @property
    def is_sqlite(self) -> bool:
        return self.database_url.startswith("sqlite")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached settings."""

    return Settings()
