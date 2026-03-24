"""SoftSkills Backend Application"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from soft_skills_backend.api.routes import (
    health,
    auth,
    users,
    skills,
    collections,
    attempts,
    progress,
)
from soft_skills_backend.observability.logging import setup_logging

setup_logging()

app = FastAPI(
    title="SoftSkills Backend",
    description="AI-driven simulation, assessment, and progression platform",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/api/health", tags=["health"])
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(skills.router, prefix="/api/skills", tags=["skills"])
app.include_router(collections.router, prefix="/api/collections", tags=["collections"])
app.include_router(attempts.router, prefix="/api/attempts", tags=["attempts"])
app.include_router(progress.router, prefix="/api/progress", tags=["progress"])


@app.get("/")
async def root():
    return {"message": "SoftSkills Backend", "version": "0.1.0"}
