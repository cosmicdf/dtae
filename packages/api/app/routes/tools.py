from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Any

from app.core.state import app_state
from dtae.registry import ToolEntry

router = APIRouter(prefix="/tools", tags=["tools"])


class ToolIn(BaseModel):
    name: str
    description: str
    parameters: dict[str, Any] = {}
    tags: list[str] = []


class ToolOut(BaseModel):
    id: str
    name: str
    description: str
    parameters: dict[str, Any]
    tags: list[str]
    usage_count: int
    avg_step_position: float


def _to_out(entry: ToolEntry) -> ToolOut:
    return ToolOut(
        id=entry.id,
        name=entry.name,
        description=entry.description,
        parameters=entry.parameters,
        tags=entry.tags,
        usage_count=entry.usage_count,
        avg_step_position=entry.avg_step_position,
    )


@router.get("/", response_model=list[ToolOut])
async def list_tools() -> list[ToolOut]:
    return [_to_out(e) for e in app_state.registry.all()]


@router.post("/", response_model=ToolOut, status_code=201)
async def register_tool(body: ToolIn) -> ToolOut:
    entry = ToolEntry(
        id=body.name,
        name=body.name,
        description=body.description,
        parameters=body.parameters,
        tags=body.tags,
    )
    app_state.registry.register(entry)
    return _to_out(app_state.registry.get(entry.id))  # type: ignore[arg-type]


@router.delete("/{tool_id}", status_code=204)
async def delete_tool(tool_id: str) -> None:
    if not app_state.registry.get(tool_id):
        raise HTTPException(status_code=404, detail="Tool not found")
    app_state.registry._tools.pop(tool_id)
