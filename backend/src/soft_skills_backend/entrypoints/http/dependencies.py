"""FastAPI dependency helpers."""

from __future__ import annotations

from typing import cast

from fastapi import Request

from soft_skills_backend.entrypoints.http.health import HealthService
from soft_skills_backend.modules.admin import AdminService
from soft_skills_backend.modules.assistant import AssistantService
from soft_skills_backend.modules.assistant.infra.realtime import AssistantRealtimeBroker
from soft_skills_backend.modules.catalog import CatalogService
from soft_skills_backend.modules.evaluation import EvaluationService
from soft_skills_backend.modules.identity import IdentityService
from soft_skills_backend.modules.organisations import OrganisationService
from soft_skills_backend.modules.practice import PracticeService
from soft_skills_backend.modules.progression import ProgressionService
from soft_skills_backend.modules.taxonomy import TaxonomyService
from soft_skills_backend.platform.container import AppContainer
from soft_skills_backend.shared.auth import Actor, HeaderAuthProvider


def get_container(request: Request) -> AppContainer:
    """Return the application container."""

    return cast(AppContainer, request.app.state.container)


def get_health_service(request: Request) -> HealthService:
    """Return the health service from the composition root."""

    return get_container(request).health_service


def get_auth_provider(request: Request) -> HeaderAuthProvider:
    return get_container(request).auth_provider


def require_actor(request: Request) -> Actor:
    return get_auth_provider(request).require_actor(request)


def require_admin_actor(request: Request) -> Actor:
    return get_auth_provider(request).require_org_admin(request)


def require_verification_actor(request: Request, collection_id: str) -> Actor:
    actor = require_actor(request)
    if actor.organisation_id is None:
        return actor
    if not actor.is_org_admin:
        from soft_skills_backend.shared.errors import auth_error

        raise auth_error(
            "Organisation admin access is required",
            code="SS-AUTH-004",
            status_code=403,
            details={"user_id": actor.user_id, "organisation_id": actor.organisation_id},
        )
    return actor


def require_org_admin_actor(request: Request) -> Actor:
    return get_auth_provider(request).require_org_admin(request)


def optional_actor(request: Request) -> Actor | None:
    return get_auth_provider(request).optional_actor(request)


def get_identity_service(request: Request) -> IdentityService:
    return get_container(request).identity_service


def get_admin_service(request: Request) -> AdminService:
    return get_container(request).admin_service


def get_taxonomy_service(request: Request) -> TaxonomyService:
    return get_container(request).taxonomy_service


def get_assistant_service(request: Request) -> AssistantService:
    return get_container(request).assistant_service


def get_assistant_broker(request: Request) -> AssistantRealtimeBroker:
    return get_container(request).assistant_broker


def get_catalog_service(request: Request) -> CatalogService:
    return get_container(request).catalog_service


def get_evaluation_service(request: Request) -> EvaluationService:
    return get_container(request).evaluation_service


def get_practice_service(request: Request) -> PracticeService:
    return get_container(request).practice_service


def get_progression_service(request: Request) -> ProgressionService:
    return get_container(request).progression_service


def get_organisation_service(request: Request) -> OrganisationService:
    return get_container(request).organisation_service
