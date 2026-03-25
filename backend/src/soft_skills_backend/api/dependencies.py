"""FastAPI dependency helpers."""

from __future__ import annotations

from typing import cast

from fastapi import Request

from soft_skills_backend.application.auth import Actor, HeaderAuthProvider
from soft_skills_backend.application.catalog import CatalogService
from soft_skills_backend.application.container import AppContainer
from soft_skills_backend.application.health import HealthService
from soft_skills_backend.application.identity import IdentityService
from soft_skills_backend.application.practice.quick_practice import QuickPracticeService
from soft_skills_backend.application.taxonomy import TaxonomyService


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


def get_taxonomy_service(request: Request) -> TaxonomyService:
    return get_container(request).taxonomy_service


def get_catalog_service(request: Request) -> CatalogService:
    return get_container(request).catalog_service


def get_practice_service(request: Request) -> QuickPracticeService:
    return get_container(request).practice_service
