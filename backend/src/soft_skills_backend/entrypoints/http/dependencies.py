"""FastAPI dependency helpers."""

from __future__ import annotations

from typing import cast

from fastapi import Request

from soft_skills_backend.entrypoints.http.health import HealthService
from soft_skills_backend.modules.admin import AdminService
from soft_skills_backend.modules.catalog import CatalogService
from soft_skills_backend.modules.identity import IdentityService
from soft_skills_backend.modules.practice import QuickPracticeService
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
    return get_auth_provider(request).require_admin(request)


def optional_actor(request: Request) -> Actor | None:
    return get_auth_provider(request).optional_actor(request)


def get_identity_service(request: Request) -> IdentityService:
    return get_container(request).identity_service


def get_admin_service(request: Request) -> AdminService:
    return get_container(request).admin_service


def get_taxonomy_service(request: Request) -> TaxonomyService:
    return get_container(request).taxonomy_service


def get_catalog_service(request: Request) -> CatalogService:
    return get_container(request).catalog_service


def get_practice_service(request: Request) -> QuickPracticeService:
    return get_container(request).practice_service


def get_progression_service(request: Request) -> ProgressionService:
    return get_container(request).progression_service
