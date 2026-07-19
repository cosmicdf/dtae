from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class AssemblyTrigger(str, Enum):
    PERIODIC = "periodic"
    TOOL_ERROR = "tool_error"
    INTENT_DRIFT = "intent_drift"
    CONTEXT_PRESSURE = "context_pressure"
    MANUAL = "manual"


@dataclass
class AgentEvent:
    step: int
    context_usage_pct: float
    last_output: str = ""
    tool_error: bool = False
    tool_error_reason: str = ""


TOOL_MISMATCH_ERRORS = {"tool_not_found", "invalid_tool", "wrong_arguments"}


class ContextMonitor:
    def __init__(
        self,
        refresh_every_n_steps: int = 5,
        context_pressure_threshold: float = 0.65,
        intent_drift_threshold: float = 0.4,
        reassemble_on_tool_error: bool = True,
    ) -> None:
        self._refresh_every = refresh_every_n_steps
        self._pressure_threshold = context_pressure_threshold
        self._drift_threshold = intent_drift_threshold
        self._on_tool_error = reassemble_on_tool_error
        self._initial_embedding: list[float] = []

    def set_initial_intent(self, embedding: list[float]) -> None:
        self._initial_embedding = embedding

    def should_reassemble(self, event: AgentEvent) -> tuple[bool, AssemblyTrigger | None]:
        if self._on_tool_error and event.tool_error:
            if event.tool_error_reason in TOOL_MISMATCH_ERRORS:
                return True, AssemblyTrigger.TOOL_ERROR

        if event.context_usage_pct >= self._pressure_threshold:
            return True, AssemblyTrigger.CONTEXT_PRESSURE

        if event.step > 0 and event.step % self._refresh_every == 0:
            return True, AssemblyTrigger.PERIODIC

        return False, None
