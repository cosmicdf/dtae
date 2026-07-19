import pytest
from dtae.registry import ToolEntry, ToolRegistry
from dtae.graph import ToolGraph
from dtae.retriever import ToolRetriever
from dtae.monitor import AgentEvent, AssemblyTrigger, ContextMonitor


def make_entry(name: str, tags: list[str] | None = None) -> ToolEntry:
    return ToolEntry(
        id=name,
        name=name,
        description=f"Tool for {name}",
        parameters={},
        tags=tags or [],
        embedding=[0.1, 0.2, 0.3],
    )


class TestToolRegistry:
    def test_register_and_get(self):
        registry = ToolRegistry.__new__(ToolRegistry)
        registry._tools = {}
        registry._embedder = None

        entry = make_entry("read_file", ["read", "filesystem"])
        registry.register(entry)

        assert registry.get("read_file") == entry
        assert len(registry) == 1

    def test_record_usage(self):
        registry = ToolRegistry.__new__(ToolRegistry)
        registry._tools = {}
        registry._embedder = None

        entry = make_entry("bash")
        registry.register(entry)
        registry.record_usage("bash", step=3)

        assert registry.get("bash").usage_count == 1
        assert registry.get("bash").avg_step_position == 3.0

    def test_all_returns_list(self):
        registry = ToolRegistry.__new__(ToolRegistry)
        registry._tools = {}
        registry._embedder = None

        registry.register(make_entry("a"))
        registry.register(make_entry("b"))

        assert len(registry.all()) == 2


class TestToolGraph:
    def test_record_and_neighbors(self):
        graph = ToolGraph(window=3, threshold=0.0)
        graph.record_step(["read_file", "write_file", "bash"])

        neighbors = graph.neighbors("read_file")
        assert "write_file" in neighbors or "bash" in neighbors

    def test_cluster_includes_self(self):
        graph = ToolGraph(threshold=0.0)
        graph.record_step(["a", "b"])
        cluster = graph.cluster("a")
        assert "a" in cluster


class TestContextMonitor:
    def test_periodic_trigger(self):
        monitor = ContextMonitor(refresh_every_n_steps=3)
        event = AgentEvent(step=3, context_usage_pct=0.1)
        should, trigger = monitor.should_reassemble(event)
        assert should is True
        assert trigger == AssemblyTrigger.PERIODIC

    def test_context_pressure_trigger(self):
        monitor = ContextMonitor(context_pressure_threshold=0.65)
        event = AgentEvent(step=1, context_usage_pct=0.8)
        should, trigger = monitor.should_reassemble(event)
        assert should is True
        assert trigger == AssemblyTrigger.CONTEXT_PRESSURE

    def test_tool_error_trigger(self):
        monitor = ContextMonitor(reassemble_on_tool_error=True)
        event = AgentEvent(
            step=1,
            context_usage_pct=0.1,
            tool_error=True,
            tool_error_reason="tool_not_found",
        )
        should, trigger = monitor.should_reassemble(event)
        assert should is True
        assert trigger == AssemblyTrigger.TOOL_ERROR

    def test_no_trigger(self):
        monitor = ContextMonitor(refresh_every_n_steps=10, context_pressure_threshold=0.9)
        event = AgentEvent(step=1, context_usage_pct=0.2)
        should, _ = monitor.should_reassemble(event)
        assert should is False


class TestToolRetriever:
    def _make_registry(self) -> ToolRegistry:
        registry = ToolRegistry.__new__(ToolRegistry)
        registry._tools = {}
        registry._embedder = None
        for name, tags in [
            ("read_file", ["read", "filesystem"]),
            ("write_file", ["write", "filesystem"]),
            ("bash", ["run", "execution"]),
            ("web_search", ["search", "read"]),
        ]:
            registry.register(make_entry(name, tags))
        return registry

    def test_retrieve_returns_k_or_less(self):
        registry = self._make_registry()
        retriever = ToolRetriever(registry)
        results = retriever.retrieve(query_embedding=[0.1, 0.2, 0.3], k=2)
        assert len(results) <= 2

    def test_always_include_pinned(self):
        registry = self._make_registry()
        retriever = ToolRetriever(registry)
        results = retriever.retrieve(
            query_embedding=[0.1, 0.2, 0.3],
            k=2,
            always_include=["bash"],
        )
        ids = [t.id for t in results]
        assert "bash" in ids
