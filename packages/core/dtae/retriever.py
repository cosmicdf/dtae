from __future__ import annotations

import math
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .registry import ToolEntry, ToolRegistry
    from .graph import ToolGraph


@dataclass
class RetrievalWeights:
    semantic: float = 0.5
    recency: float = 0.2
    co_usage: float = 0.2
    phase: float = 0.1


PHASE_TAGS: dict[str, list[str]] = {
    "planning": ["read", "search", "list", "inspect"],
    "execution": ["write", "run", "bash", "create", "call"],
    "verification": ["test", "diff", "log", "check", "verify"],
    "reporting": ["write", "summarize", "format"],
}


class ToolRetriever:
    def __init__(
        self,
        registry: ToolRegistry,
        graph: ToolGraph | None = None,
        weights: RetrievalWeights | None = None,
    ) -> None:
        self._registry = registry
        self._graph = graph
        self._weights = weights or RetrievalWeights()

    def retrieve(
        self,
        query_embedding: list[float],
        k: int = 8,
        active_tool_ids: list[str] | None = None,
        recent_tool_ids: list[str] | None = None,
        phase: str = "execution",
        always_include: list[str] | None = None,
    ) -> list[ToolEntry]:
        always_include = always_include or []
        active_tool_ids = active_tool_ids or []
        recent_tool_ids = recent_tool_ids or []

        scored: list[tuple[float, ToolEntry]] = []
        for entry in self._registry.all():
            if entry.id in always_include:
                continue
            score = self._score(
                entry, query_embedding, active_tool_ids, recent_tool_ids, phase
            )
            scored.append((score, entry))

        scored.sort(key=lambda x: x[0], reverse=True)
        top = [e for _, e in scored[:k]]

        # inject always-include tools
        pinned = [self._registry.get(tid) for tid in always_include if self._registry.get(tid)]
        return pinned + top  # type: ignore[return-value]

    def _score(
        self,
        entry: ToolEntry,
        query_embedding: list[float],
        active_ids: list[str],
        recent_ids: list[str],
        phase: str,
    ) -> float:
        w = self._weights

        sem = self._cosine(query_embedding, entry.embedding) if entry.embedding else 0.0
        rec = 1.0 if entry.id in recent_ids else 0.0
        co = 0.0
        if self._graph:
            neighbors = self._graph.neighbors(entry.id)
            overlap = set(neighbors) & set(active_ids)
            co = len(overlap) / max(len(neighbors), 1)
        phase_tags = PHASE_TAGS.get(phase, [])
        ph = sum(1 for t in entry.tags if t in phase_tags) / max(len(phase_tags), 1)

        return w.semantic * sem + w.recency * rec + w.co_usage * co + w.phase * ph

    @staticmethod
    def _cosine(a: list[float], b: list[float]) -> float:
        if not a or not b or len(a) != len(b):
            return 0.0
        dot = sum(x * y for x, y in zip(a, b))
        mag_a = math.sqrt(sum(x * x for x in a))
        mag_b = math.sqrt(sum(x * x for x in b))
        if mag_a == 0 or mag_b == 0:
            return 0.0
        return dot / (mag_a * mag_b)
