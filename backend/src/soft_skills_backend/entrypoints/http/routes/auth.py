"""Auth endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Request

from soft_skills_backend.entrypoints.http.dependencies import get_identity_service
from soft_skills_backend.entrypoints.http.schemas import ApiEnvelope, ok_response
from soft_skills_backend.modules.identity import LoginUserCommand, RegisterUserCommand, UserView

router = APIRouter()


@router.post("/register", response_model=ApiEnvelope[UserView])
async def register(request: Request, command: RegisterUserCommand) -> ApiEnvelope[UserView]:
    service = get_identity_service(request)
    return ok_response(request, service.register_user(command))


@router.post("/login", response_model=ApiEnvelope[UserView])
async def login(request: Request, command: LoginUserCommand) -> ApiEnvelope[UserView]:
    service = get_identity_service(request)
    return ok_response(request, service.login_user(command))
