from __future__ import annotations

import os
from typing import Any

from dtae.registry import ToolEntry, ToolRegistry


def _qdrant_available() -> bool:
    try:
        import qdrant_client  # noqa: F401
        return True
    except ImportError:
        return False


class QdrantRegistry(ToolRegistry):
    """Registry backed by Qdrant for persistent storage across restarts."""

    COLLECTION = "dtae_tools"
    VECTOR_SIZE = 768  # nomic-embed-text-v1.5

    def __init__(self, qdrant_url: str, embedding_model: str) -> None:
        super().__init__(embedding_model=embedding_model)
        self._qdrant_url = qdrant_url
        self._client: Any = None
        self._qdrant_ready = False
        self._init_qdrant()

    def _init_qdrant(self) -> None:
        if not _qdrant_available():
            return
        try:
            from qdrant_client import QdrantClient
            from qdrant_client.models import Distance, VectorParams

            self._client = QdrantClient(url=self._qdrant_url, timeout=5)
            collections = [c.name for c in self._client.get_collections().collections]
            if self.COLLECTION not in collections:
                self._client.create_collection(
                    collection_name=self.COLLECTION,
                    vectors_config=VectorParams(size=self.VECTOR_SIZE, distance=Distance.COSINE),
                )
            self._qdrant_ready = True
            self._load_from_qdrant()
        except Exception:
            self._qdrant_ready = False

    def _load_from_qdrant(self) -> None:
        if not self._qdrant_ready or not self._client:
            return
        try:
            results = self._client.scroll(
                collection_name=self.COLLECTION,
                with_vectors=True,
                with_payload=True,
                limit=10_000,
            )
            for point in results[0]:
                p = point.payload or {}
                entry = ToolEntry(
                    id=p.get("id", ""),
                    name=p.get("name", ""),
                    description=p.get("description", ""),
                    parameters=p.get("parameters", {}),
                    tags=p.get("tags", []),
                    embedding=list(point.vector) if point.vector else [],
                    usage_count=p.get("usage_count", 0),
                    avg_step_position=p.get("avg_step_position", 0.0),
                )
                self._tools[entry.id] = entry
        except Exception:
            pass

    def register(self, entry: ToolEntry) -> None:
        super().register(entry)
        self._upsert_to_qdrant(entry)

    def _upsert_to_qdrant(self, entry: ToolEntry) -> None:
        if not self._qdrant_ready or not self._client or not entry.embedding:
            return
        try:
            from qdrant_client.models import PointStruct

            self._client.upsert(
                collection_name=self.COLLECTION,
                points=[
                    PointStruct(
                        id=abs(hash(entry.id)) % (2**63),
                        vector=entry.embedding,
                        payload={
                            "id": entry.id,
                            "name": entry.name,
                            "description": entry.description,
                            "parameters": entry.parameters,
                            "tags": entry.tags,
                            "usage_count": entry.usage_count,
                            "avg_step_position": entry.avg_step_position,
                        },
                    )
                ],
            )
        except Exception:
            pass

    def record_usage(self, tool_id: str, step: int) -> None:
        super().record_usage(tool_id, step)
        entry = self._tools.get(tool_id)
        if entry:
            self._upsert_to_qdrant(entry)

    @property
    def is_persistent(self) -> bool:
        return self._qdrant_ready
