"""Users endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Request

from soft_skills_backend.entrypoints.http.dependencies import get_identity_service, require_actor
from soft_skills_backend.entrypoints.http.schemas import ApiEnvelope, ok_response
from soft_skills_backend.modules.identity import UpdateProfileCommand, UserView

router = APIRouter()


@router.get("/me", response_model=ApiEnvelope[UserView])
async def get_me(request: Request) -> ApiEnvelope[UserView]:
    actor = await require_actor(request)
    service = get_identity_service(request)
    return ok_response(request, service.get_user(actor.user_id))


@router.patch("/me/profile", response_model=ApiEnvelope[UserView])
async def update_profile(request: Request, command: UpdateProfileCommand) -> ApiEnvelope[UserView]:
    actor = await require_actor(request)
    service = get_identity_service(request)
    return ok_response(request, service.update_profile(actor.user_id, command))
