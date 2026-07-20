import logging

from dtae.registry import ToolRegistry
from dtae.graph import ToolGraph
from dtae.retriever import ToolRetriever
from dtae.assembler import DynamicToolAssembler

from .config import settings

logger = logging.getLogger(__name__)


def _build_registry() -> ToolRegistry:
    try:
        from app.storage.qdrant_registry import QdrantRegistry
        registry = QdrantRegistry(
            qdrant_url=settings.qdrant_url,
            embedding_model=settings.embedding_model,
        )
        if registry.is_persistent:
            logger.info("Using Qdrant-backed registry at %s", settings.qdrant_url)
            return registry
        logger.warning("Qdrant unavailable, falling back to in-memory registry")
    except Exception as exc:
        logger.warning("Could not init Qdrant registry: %s — using in-memory", exc)
    return ToolRegistry(embedding_model=settings.embedding_model)


class AppState:
    registry: ToolRegistry
    graph: ToolGraph
    retriever: ToolRetriever
    assemblers: dict[str, DynamicToolAssembler]

    def __init__(self) -> None:
        self.registry = _build_registry()
        self.graph = ToolGraph()
        self.retriever = ToolRetriever(self.registry, self.graph)
        self.assemblers = {}

    def get_or_create_assembler(self, session_id: str) -> DynamicToolAssembler:
        if session_id not in self.assemblers:
            self.assemblers[session_id] = DynamicToolAssembler(
                registry=self.registry,
                max_tools=settings.max_tools_default,
                max_tool_tokens=settings.max_tool_tokens_default,
            )
        return self.assemblers[session_id]


app_state = AppState()
