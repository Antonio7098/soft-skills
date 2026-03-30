"""Top-level API router."""

from __future__ import annotations

from fastapi import APIRouter

from soft_skills_backend.entrypoints.http.routes import (
    admin,
    admin_agent,
    assistant,
    attempts,
    auth,
    collections,
    evaluations,
    events,
    generation,
    health,
    organisations,
    practice_runs,
    progress,
    providers,
    skills,
    users,
    voice,
)

api_router = APIRouter()
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])
api_router.include_router(admin_agent.router, prefix="/admin-agent", tags=["admin-agent"])
api_router.include_router(evaluations.router, prefix="/admin/evaluations", tags=["evaluations"])
api_router.include_router(events.router, prefix="/events", tags=["events"])
api_router.include_router(assistant.router, prefix="/assistant", tags=["assistant"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(skills.router, prefix="/skills", tags=["skills"])
api_router.include_router(generation.router, prefix="", tags=["generation"])
api_router.include_router(collections.router, prefix="/collections", tags=["collections"])
api_router.include_router(attempts.router, prefix="/attempts", tags=["attempts"])
api_router.include_router(practice_runs.router, prefix="/practice-runs", tags=["practice-runs"])
api_router.include_router(progress.router, prefix="/progress", tags=["progress"])
api_router.include_router(providers.router, prefix="/providers", tags=["providers"])
api_router.include_router(organisations.router, prefix="/organisations", tags=["organisations"])
api_router.include_router(voice.router, prefix="/voice", tags=["voice"])
