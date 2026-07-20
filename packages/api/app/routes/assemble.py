from fastapi import APIRouter
from pydantic import BaseModel
from typing import Any

from app.core.state import app_state

router = APIRouter(prefix="/assemble", tags=["assemble"])

_PHASE_VALUES = {"planning", "execution", "verification", "reporting"}


class AssembleRequest(BaseModel):
    query: str
    phase: str = "execution"
    session_id: str = "default"
    max_tools: int | None = None
    force: bool = False


class ToolSlim(BaseModel):
    id: str
    name: str
    description: str
    parameters: dict[str, Any]
    tags: list[str]


class AssembleResponse(BaseModel):
    tools: list[ToolSlim]
    count: int
    session_id: str
    token_estimate: int


@router.post("/", response_model=AssembleResponse)
async def assemble(body: AssembleRequest) -> AssembleResponse:
    phase = body.phase if body.phase in _PHASE_VALUES else "execution"
    assembler = app_state.get_or_create_assembler(body.session_id)

    if body.max_tools is not None:
        assembler._max_tools = body.max_tools

    tools = assembler.assemble(query=body.query, phase=phase, force=body.force)

    token_estimate = sum(
        int(len(t.description) * 0.25) + 20 for t in tools
    )

    return AssembleResponse(
        tools=[
            ToolSlim(
                id=t.id,
                name=t.name,
                description=t.description,
                parameters=t.parameters,
                tags=t.tags,
            )
            for t in tools
        ],
        count=len(tools),
        session_id=body.session_id,
        token_estimate=token_estimate,
    )
