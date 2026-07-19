from __future__ import annotations

from collections import defaultdict


class ToolGraph:
    """Weighted co-occurrence graph built from live agent usage."""

    def __init__(self, window: int = 3, threshold: float = 0.3) -> None:
        self._window = window
        self._threshold = threshold
        self._edges: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))
        self._max_weight: dict[str, float] = defaultdict(float)

    def record_step(self, tool_ids: list[str]) -> None:
        for i, a in enumerate(tool_ids):
            for b in tool_ids[max(0, i - self._window): i]:
                self._edges[a][b] += 1.0
                self._edges[b][a] += 0.5
                self._max_weight[a] = max(self._max_weight[a], self._edges[a][b])
                self._max_weight[b] = max(self._max_weight[b], self._edges[b][a])

    def neighbors(self, tool_id: str) -> list[str]:
        edges = self._edges.get(tool_id, {})
        max_w = self._max_weight.get(tool_id, 1.0) or 1.0
        return [t for t, w in edges.items() if w / max_w >= self._threshold]

    def edge_weight(self, a: str, b: str) -> float:
        return self._edges.get(a, {}).get(b, 0.0)

    def cluster(self, tool_id: str) -> list[str]:
        return [tool_id] + self.neighbors(tool_id)
