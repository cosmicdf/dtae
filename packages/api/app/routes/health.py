from fastapi import APIRouter
from pydantic import BaseModel

from app.core.state import app_state

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    status: str
    tools_registered: int
    active_sessions: int


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        tools_registered=len(app_state.registry),
        active_sessions=len(app_state.assemblers),
    )
