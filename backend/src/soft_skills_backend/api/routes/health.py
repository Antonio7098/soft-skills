"""Health endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Request

from soft_skills_backend.api.schemas import ApiEnvelope, ok_response
from soft_skills_backend.application.health import ReadinessPayload

router = APIRouter()


@router.get("/readiness", response_model=ApiEnvelope[ReadinessPayload])
async def readiness(request: Request) -> ApiEnvelope[ReadinessPayload]:
    return ok_response(request, request.app.state.container.health_service.readiness())


@router.get("/liveness", response_model=ApiEnvelope[ReadinessPayload])
async def liveness(request: Request) -> ApiEnvelope[ReadinessPayload]:
    return ok_response(request, request.app.state.container.health_service.liveness())
