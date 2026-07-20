from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ToolEntry:
    id: str
    name: str
    description: str
    parameters: dict[str, Any]
    tags: list[str] = field(default_factory=list)
    embedding: list[float] = field(default_factory=list)
    usage_count: int = 0
    avg_step_position: float = 0.0
    requires: list[str] = field(default_factory=list)
    conflicts_with: list[str] = field(default_factory=list)


class ToolRegistry:
    def __init__(self, embedding_model: str = "nomic-ai/nomic-embed-text-v1.5") -> None:
        self._tools: dict[str, ToolEntry] = {}
        self._embedder = self._load_embedder(embedding_model)

    def _load_embedder(self, model: str) -> Any:
        if os.getenv("DTAE_DISABLE_EMBEDDINGS", "").lower() == "true":
            return None
        try:
            from fastembed import TextEmbedding
            return TextEmbedding(model_name=model)
        except ImportError:
            return None

    def register(self, entry: ToolEntry) -> None:
        if self._embedder and not entry.embedding:
            entry.embedding = list(next(self._embedder.embed([entry.description])))
        self._tools[entry.id] = entry

    def register_dict(self, tool: dict[str, Any]) -> None:
        entry = ToolEntry(
            id=tool["name"],
            name=tool["name"],
            description=tool.get("description", ""),
            parameters=tool.get("parameters", {}),
            tags=tool.get("tags", []),
        )
        self.register(entry)

    def get(self, tool_id: str) -> ToolEntry | None:
        return self._tools.get(tool_id)

    def all(self) -> list[ToolEntry]:
        return list(self._tools.values())

    def record_usage(self, tool_id: str, step: int) -> None:
        entry = self._tools.get(tool_id)
        if entry:
            total = entry.usage_count * entry.avg_step_position + step
            entry.usage_count += 1
            entry.avg_step_position = total / entry.usage_count

    def __len__(self) -> int:
        return len(self._tools)
