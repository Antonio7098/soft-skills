"""Auth endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Request

from soft_skills_backend.api.dependencies import get_identity_service
from soft_skills_backend.api.schemas import ApiEnvelope, ok_response
from soft_skills_backend.application.identity import RegisterUserCommand, UserView

router = APIRouter()


@router.post("/register", response_model=ApiEnvelope[UserView])
async def register(request: Request, command: RegisterUserCommand) -> ApiEnvelope[UserView]:
    service = get_identity_service(request)
    return ok_response(request, service.register_user(command))
