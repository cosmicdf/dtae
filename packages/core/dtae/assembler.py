from __future__ import annotations

from typing import Any

from .graph import ToolGraph
from .monitor import AgentEvent, AssemblyTrigger, ContextMonitor
from .registry import ToolEntry, ToolRegistry
from .retriever import RetrievalWeights, ToolRetriever

_AVG_TOKENS_PER_CHAR = 0.25


class DynamicToolAssembler:
    def __init__(
        self,
        registry: ToolRegistry,
        max_tools: int = 8,
        max_tool_tokens: int = 2000,
        refresh_every_n_steps: int = 5,
        context_pressure_threshold: float = 0.65,
        reassemble_on_tool_error: bool = True,
        weights: RetrievalWeights | None = None,
        always_include: list[str] | None = None,
    ) -> None:
        self._registry = registry
        self._max_tools = max_tools
        self._max_tool_tokens = max_tool_tokens
        self._always_include = always_include or []

        self._graph = ToolGraph()
        self._retriever = ToolRetriever(registry, self._graph, weights)
        self._monitor = ContextMonitor(
            refresh_every_n_steps=refresh_every_n_steps,
            context_pressure_threshold=context_pressure_threshold,
            reassemble_on_tool_error=reassemble_on_tool_error,
        )

        self._current_tools: list[ToolEntry] = []
        self._recent_tool_ids: list[str] = []
        self._embedder: Any = None
        self._step = 0

        try:
            from fastembed import TextEmbedding
            self._embedder = TextEmbedding()
        except ImportError:
            pass

    def assemble(
        self,
        query: str,
        phase: str = "execution",
        force: bool = False,
    ) -> list[ToolEntry]:
        event = AgentEvent(
            step=self._step,
            context_usage_pct=0.0,
        )
        should, _ = self._monitor.should_reassemble(event)

        if force or should or not self._current_tools:
            embedding = self._embed(query)
            candidates = self._retriever.retrieve(
                query_embedding=embedding,
                k=self._max_tools,
                active_tool_ids=[t.id for t in self._current_tools],
                recent_tool_ids=self._recent_tool_ids[-10:],
                phase=phase,
                always_include=self._always_include,
            )
            self._current_tools = self._trim_to_budget(candidates)

        self._step += 1
        return self._current_tools

    def record_tool_use(self, tool_id: str) -> None:
        self._registry.record_usage(tool_id, self._step)
        self._recent_tool_ids.append(tool_id)
        active = [t.id for t in self._current_tools]
        self._graph.record_step(active)

    def _trim_to_budget(self, tools: list[ToolEntry]) -> list[ToolEntry]:
        result: list[ToolEntry] = []
        tokens_used = 0
        for tool in tools:
            cost = int(len(tool.description) * _AVG_TOKENS_PER_CHAR) + 20
            if tokens_used + cost > self._max_tool_tokens:
                break
            result.append(tool)
            tokens_used += cost
        return result

    def _embed(self, text: str) -> list[float]:
        if self._embedder:
            return list(next(self._embedder.embed([text])))
        return []

    @property
    def current_tools(self) -> list[ToolEntry]:
        return self._current_tools
