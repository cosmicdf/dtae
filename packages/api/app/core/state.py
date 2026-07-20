from dtae.registry import ToolRegistry
from dtae.graph import ToolGraph
from dtae.retriever import ToolRetriever
from dtae.assembler import DynamicToolAssembler

from .config import settings


class AppState:
    registry: ToolRegistry
    graph: ToolGraph
    retriever: ToolRetriever

    # session_id -> assembler
    assemblers: dict[str, DynamicToolAssembler]

    def __init__(self) -> None:
        self.registry = ToolRegistry(embedding_model=settings.embedding_model)
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
