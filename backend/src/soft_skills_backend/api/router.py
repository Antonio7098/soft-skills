"""Top-level API router."""

from __future__ import annotations

from fastapi import APIRouter

from soft_skills_backend.api.routes import (
    attempts,
    auth,
    collections,
    health,
    progress,
    skills,
    users,
)

api_router = APIRouter()
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(skills.router, prefix="/skills", tags=["skills"])
api_router.include_router(collections.router, prefix="/collections", tags=["collections"])
api_router.include_router(attempts.router, prefix="/attempts", tags=["attempts"])
api_router.include_router(progress.router, prefix="/progress", tags=["progress"])
