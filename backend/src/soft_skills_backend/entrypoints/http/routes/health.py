"""Health endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Request

from soft_skills_backend.entrypoints.http.health import ReadinessPayload
from soft_skills_backend.entrypoints.http.schemas import ApiEnvelope, ok_response

router = APIRouter()


@router.get("/readiness", response_model=ApiEnvelope[ReadinessPayload])
async def readiness(request: Request) -> ApiEnvelope[ReadinessPayload]:
    return ok_response(request, request.app.state.container.health_service.readiness())


@router.get("/liveness", response_model=ApiEnvelope[ReadinessPayload])
async def liveness(request: Request) -> ApiEnvelope[ReadinessPayload]:
    return ok_response(request, request.app.state.container.health_service.liveness())
