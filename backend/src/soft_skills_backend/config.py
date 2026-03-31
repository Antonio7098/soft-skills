"""Application settings."""

from __future__ import annotations

from enum import StrEnum
from functools import lru_cache
from typing import Annotated

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class LLMTaskKind(StrEnum):
    ASSISTANT = "assistant"
    ADMIN_AGENT = "admin_agent"
    MARKING_PER_SKILL = "marking_per_skill"
    MARKING_AGGREGATION = "marking_aggregation"
    CREATOR_BLUEPRINT = "creator_blueprint"
    CREATOR_PROMPT_ITEM = "creator_prompt_item"
    CREATOR_SCENARIO = "creator_scenario"


class Settings(BaseSettings):
    """Runtime configuration."""

    model_config = SettingsConfigDict(
        env_prefix="SOFT_SKILLS_",
        env_file=".env",
        extra="ignore",
        populate_by_name=True,
    )

    app_name: str = "SoftSkills Backend"
    app_version: str = "0.1.0"
    environment: str = "local"
    api_prefix: str = "/api"
    cors_allowed_origins: Annotated[tuple[str, ...], NoDecode] = ("*",)
    database_url: str = "sqlite+pysqlite:///./softskills.db"
    log_level: str = "INFO"
    stageflow_event_queue_size: int = Field(default=1000, ge=1)
    provider_name: str = "groq"
    provider_base_url: str = "https://openrouter.ai/api/v1"
    provider_api_key: str | None = None
    openrouter_api_key: str | None = Field(
        default=None,
        validation_alias="OPENROUTER_API_KEY",
    )
    openrouter_base_url: str = Field(
        default="https://openrouter.ai/api/v1",
        validation_alias="OPENROUTER_BASE_URL",
    )
    smoke_timeout_seconds: float = Field(default=10.0, gt=0)
    llm_assistant_timeout_seconds: float = Field(default=20.0, gt=0, le=120.0)
    llm_assistant_max_retries: int = Field(default=1, ge=0, le=3)
    llm_assistant_conversation_history_limit: int = Field(default=8, ge=2, le=24)
    llm_assistant_recent_attempt_limit: int = Field(default=3, ge=0, le=10)
    llm_admin_agent_timeout_seconds: float = Field(default=20.0, gt=0, le=120.0)
    tool_approval_timeout_seconds: float = Field(default=60.0, gt=0, le=300.0)
    tool_approval_auto_allow: Annotated[tuple[str, ...], NoDecode] = (
        "query_user_context",
        "query_admin_data",
        "start_collection_practice",
        "get_active_practice",
        "submit_active_practice_response",
        "end_active_practice",
        "generate_collection",
        "generate_prompt_items",
    )
    provider_max_retries: int = Field(default=2, ge=0, le=5)
    provider_retry_backoff_seconds: float = Field(default=0.25, gt=0, le=10.0)
    assessment_validation_retries: int = Field(default=1, ge=0, le=3)
    creator_generation_validation_retries: int = Field(default=2, ge=0, le=3)
    otel_enabled: bool = Field(default=False)
    otel_service_name: str = Field(default="soft-skills-backend")
    otel_exporter_otlp_endpoint: str | None = Field(
        default=None,
        validation_alias="OTEL_EXPORTER_OTLP_ENDPOINT",
    )

    llm_assistant_model: str = Field(default="openai/gpt-oss-20b")
    llm_assistant_prompt_version: str = Field(default="assistant.chat.v1")
    llm_admin_agent_model: str | None = Field(default=None)
    llm_admin_agent_planning_prompt_version: str = Field(default="admin-agent.plan.v1")
    admin_agent_runtime_config_version: str = Field(default="admin-agent.runtime.v1")
    admin_agent_query_timeout_seconds: float = Field(default=5.0, gt=0, le=30.0)
    admin_agent_query_row_limit: int = Field(default=50, ge=1, le=200)
    admin_agent_conversation_history_limit: int = Field(default=4, ge=0, le=10)

    llm_marking_per_skill_model: str | None = Field(default=None)
    llm_marking_per_skill_prompt_version: str = Field(
        default="assessment.quick-practice.v1",
    )
    llm_marking_aggregation_model: str | None = Field(default=None)
    llm_marking_aggregation_prompt_version: str = Field(
        default="assessment.aggregation.v1",
    )
    llm_marking_timeout_seconds: float = Field(default=30.0, gt=0, le=300.0)

    llm_creator_blueprint_model: str | None = Field(default=None)
    llm_creator_blueprint_prompt_version: str = Field(
        default="creator.collection.structured-blueprint.v3",
    )
    llm_creator_prompt_item_model: str | None = Field(default=None)
    llm_creator_prompt_item_prompt_version: str = Field(
        default="creator.prompt-item.worker.v1",
    )
    llm_creator_scenario_model: str | None = Field(default=None)
    llm_creator_scenario_prompt_version: str = Field(
        default="creator.scenario.worker.v1",
    )

    llm_default_model: str = Field(default="openai/gpt-oss-20b")
    llm_default_backup_model: str | None = Field(default=None)

    groq_api_key: str | None = Field(
        default=None,
        validation_alias="GROQ_API_KEY",
    )
    groq_base_url: str = Field(
        default="https://api.groq.com/openai/v1",
        validation_alias="GROQ_BASE_URL",
    )
    groq_default_model: str = Field(default="llama-3.3-70b-versatile")
    groq_default_backup_model: str | None = Field(default="llama-3.1-8b-instant")

    groq_llm_assistant_model: str | None = Field(default=None)
    groq_llm_admin_agent_model: str | None = Field(default=None)
    groq_llm_marking_per_skill_model: str | None = Field(default=None)
    groq_llm_marking_aggregation_model: str | None = Field(default=None)
    groq_llm_creator_blueprint_model: str | None = Field(default=None)
    groq_llm_creator_prompt_item_model: str | None = Field(default=None)
    groq_llm_creator_scenario_model: str | None = Field(default=None)

    deepgram_api_key: str | None = Field(
        default=None,
        validation_alias="DEEPGRAM_API_KEY",
    )
    deepgram_model: str = Field(default="nova-3")
    deepgram_language: str = Field(default="en-US")

    @field_validator("cors_allowed_origins", mode="before")
    @classmethod
    def _normalize_cors_allowed_origins(
        cls, value: str | tuple[str, ...] | list[str]
    ) -> tuple[str, ...]:
        if isinstance(value, str):
            return tuple(part.strip() for part in value.split(",") if part.strip())
        return tuple(value)

    @field_validator("tool_approval_auto_allow", mode="before")
    @classmethod
    def _normalize_tool_approval_auto_allow(
        cls, value: str | tuple[str, ...] | list[str]
    ) -> tuple[str, ...]:
        if isinstance(value, str):
            return tuple(part.strip() for part in value.split(",") if part.strip())
        return tuple(value)

    @property
    def is_sqlite(self) -> bool:
        return self.database_url.startswith("sqlite")

    def get_llm_model_for_task(self, task: LLMTaskKind) -> str:
        """Resolve the effective model slug for a given LLM task."""
        match task:
            case LLMTaskKind.ASSISTANT:
                return self.llm_assistant_model
            case LLMTaskKind.ADMIN_AGENT:
                return self.llm_admin_agent_model or self.llm_default_model
            case LLMTaskKind.MARKING_PER_SKILL:
                return self.llm_marking_per_skill_model or self.llm_default_model
            case LLMTaskKind.MARKING_AGGREGATION:
                return self.llm_marking_aggregation_model or self.llm_default_model
            case LLMTaskKind.CREATOR_BLUEPRINT:
                return self.llm_creator_blueprint_model or self.llm_default_model
            case LLMTaskKind.CREATOR_PROMPT_ITEM:
                return self.llm_creator_prompt_item_model or self.llm_default_model
            case LLMTaskKind.CREATOR_SCENARIO:
                return self.llm_creator_scenario_model or self.llm_default_model

    def get_llm_prompt_version_for_task(self, task: LLMTaskKind) -> str:
        """Resolve the prompt version for a given LLM task."""
        match task:
            case LLMTaskKind.ASSISTANT:
                return self.llm_assistant_prompt_version
            case LLMTaskKind.ADMIN_AGENT:
                return self.llm_admin_agent_planning_prompt_version
            case LLMTaskKind.MARKING_PER_SKILL:
                return self.llm_marking_per_skill_prompt_version
            case LLMTaskKind.MARKING_AGGREGATION:
                return self.llm_marking_aggregation_prompt_version
            case LLMTaskKind.CREATOR_BLUEPRINT:
                return self.llm_creator_blueprint_prompt_version
            case LLMTaskKind.CREATOR_PROMPT_ITEM:
                return self.llm_creator_prompt_item_prompt_version
            case LLMTaskKind.CREATOR_SCENARIO:
                return self.llm_creator_scenario_prompt_version

    @property
    def creator_structured_generation_prompt_version(self) -> str:
        return self.llm_creator_blueprint_prompt_version

    @property
    def creator_chat_generation_prompt_version(self) -> str:
        return self.llm_creator_blueprint_prompt_version


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached settings."""

    return Settings()
