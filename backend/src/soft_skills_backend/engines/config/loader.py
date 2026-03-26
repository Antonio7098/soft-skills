"""Load reviewed JSON config artifacts for app-agnostic engines."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from pydantic import BaseModel, ValidationError

from soft_skills_backend.engines.config.models import (
    CatalogGenerationRuntimeConfig,
    MarkingRuntimeConfig,
)
from soft_skills_backend.engines.progression import ProgressionEngineConfig
from soft_skills_backend.engines.recommendation import RecommendationEngineConfig
from soft_skills_backend.shared.errors import validation_error

_ARTIFACTS_DIR = Path(__file__).resolve().parent / "artifacts"


@lru_cache(maxsize=1)
def load_progression_engine_config() -> ProgressionEngineConfig:
    """Load the reviewed progression config artifact."""

    return _load_json_artifact(
        "soft_skills_progression_engine.v1.json",
        ProgressionEngineConfig,
    )


@lru_cache(maxsize=1)
def load_recommendation_engine_config() -> RecommendationEngineConfig:
    """Load the reviewed recommendation config artifact."""

    return _load_json_artifact(
        "soft_skills_recommendation_engine.v1.json",
        RecommendationEngineConfig,
    )


@lru_cache(maxsize=1)
def load_marking_runtime_config() -> MarkingRuntimeConfig:
    """Load the reviewed marking runtime config artifact."""

    return _load_json_artifact(
        "soft_skills_marking_runtime.v1.json",
        MarkingRuntimeConfig,
    )


@lru_cache(maxsize=1)
def load_catalog_generation_runtime_config() -> CatalogGenerationRuntimeConfig:
    """Load the reviewed creator-generation config artifact."""

    return _load_json_artifact(
        "soft_skills_catalog_generation_runtime.v1.json",
        CatalogGenerationRuntimeConfig,
    )


def _load_json_artifact(filename: str, model_type: type[BaseModel]) -> BaseModel:
    path = _ARTIFACTS_DIR / filename
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise validation_error(
            "Engine config artifact was not found",
            code="SS-VALIDATION-038",
            status_code=500,
            details={"path": str(path)},
        ) from exc
    except json.JSONDecodeError as exc:
        raise validation_error(
            "Engine config artifact contained invalid JSON",
            code="SS-VALIDATION-039",
            status_code=500,
            details={"path": str(path), "reason": str(exc)},
        ) from exc
    try:
        return model_type.model_validate(payload)
    except ValidationError as exc:
        raise validation_error(
            "Engine config artifact failed schema validation",
            code="SS-VALIDATION-040",
            status_code=500,
            details={"path": str(path), "reason": str(exc)},
        ) from exc
