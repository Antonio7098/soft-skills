"""Health endpoints"""

from fastapi import APIRouter

router = APIRouter()


@router.get("/readiness")
async def readiness():
    return {"status": "ready"}


@router.get("/liveness")
async def liveness():
    return {"status": "alive"}
