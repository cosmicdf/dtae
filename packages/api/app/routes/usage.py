from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.core.state import app_state

router = APIRouter(prefix="/usage", tags=["usage"])


class UsageIn(BaseModel):
    tool_id: str
    session_id: str = "default"
    step: int = 0


class UsageStats(BaseModel):
    tool_id: str
    usage_count: int
    avg_step_position: float


@router.post("/", status_code=204)
async def record_usage(body: UsageIn) -> None:
    if not app_state.registry.get(body.tool_id):
        raise HTTPException(status_code=404, detail="Tool not found")
    app_state.registry.record_usage(body.tool_id, body.step)
    assembler = app_state.assemblers.get(body.session_id)
    if assembler:
        assembler.record_tool_use(body.tool_id)


@router.get("/stats", response_model=list[UsageStats])
async def usage_stats() -> list[UsageStats]:
    return [
        UsageStats(
            tool_id=e.id,
            usage_count=e.usage_count,
            avg_step_position=e.avg_step_position,
        )
        for e in app_state.registry.all()
        if e.usage_count > 0
    ]
