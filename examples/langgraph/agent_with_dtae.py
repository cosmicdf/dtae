"""
LangGraph agent example using DTAE for just-in-time tool assembly.

Run:
    pip install dtae-core langgraph langchain-anthropic
    python agent_with_dtae.py
"""

from __future__ import annotations

import os
from typing import Annotated, TypedDict

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, ToolMessage
from langchain_core.tools import tool
from langgraph.graph import END, StateGraph
from langgraph.graph.message import add_messages

from dtae import DynamicToolAssembler, ToolEntry, ToolRegistry


# ---------------------------------------------------------------------------
# 1. Define your tools (normally these come from MCPs or your own functions)
# ---------------------------------------------------------------------------

@tool
def read_file(path: str) -> str:
    """Read the contents of a file at the given path."""
    try:
        with open(path) as f:
            return f.read()
    except FileNotFoundError:
        return f"File not found: {path}"


@tool
def list_directory(path: str = ".") -> str:
    """List files in a directory."""
    import os as _os
    try:
        entries = _os.listdir(path)
        return "\n".join(sorted(entries))
    except Exception as e:
        return str(e)


@tool
def run_python(code: str) -> str:
    """Execute a Python code snippet and return stdout."""
    import io, contextlib
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):
            exec(code, {})  # noqa: S102
        return buf.getvalue() or "(no output)"
    except Exception as e:
        return f"Error: {e}"


@tool
def web_search(query: str) -> str:
    """Search the web for information (stub — replace with real search API)."""
    return f"[stub] Search results for: {query}"


@tool
def write_file(path: str, content: str) -> str:
    """Write content to a file."""
    with open(path, "w") as f:
        f.write(content)
    return f"Written {len(content)} bytes to {path}"


ALL_TOOLS = [read_file, list_directory, run_python, web_search, write_file]
TOOL_MAP = {t.name: t for t in ALL_TOOLS}


# ---------------------------------------------------------------------------
# 2. Build DTAE registry from LangChain tool definitions
# ---------------------------------------------------------------------------

def build_registry() -> ToolRegistry:
    registry = ToolRegistry.__new__(ToolRegistry)
    registry._tools = {}
    registry._embedder = None

    tag_map = {
        "read_file": ["read", "filesystem"],
        "list_directory": ["read", "filesystem"],
        "run_python": ["run", "execution", "code"],
        "web_search": ["search", "read"],
        "write_file": ["write", "filesystem"],
    }

    for lc_tool in ALL_TOOLS:
        entry = ToolEntry(
            id=lc_tool.name,
            name=lc_tool.name,
            description=lc_tool.description,
            parameters=lc_tool.args_schema.schema() if lc_tool.args_schema else {},
            tags=tag_map.get(lc_tool.name, []),
            embedding=[],
        )
        registry._tools[entry.id] = entry

    return registry


# ---------------------------------------------------------------------------
# 3. Agent state and graph
# ---------------------------------------------------------------------------

class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    current_phase: str


registry = build_registry()
assembler = DynamicToolAssembler(registry=registry, max_tools=3, always_include=[])
llm = ChatAnthropic(model="claude-sonnet-4-6", api_key=os.environ["ANTHROPIC_API_KEY"])


def retrieve_tools_node(state: AgentState) -> dict:
    """Pick the right tools for the current step."""
    last_human = next(
        (m.content for m in reversed(state["messages"]) if isinstance(m, HumanMessage)),
        "",
    )
    tools = assembler.assemble(query=str(last_human), phase=state["current_phase"])
    # Bind only the retrieved tools to the LLM for this step
    active_lc_tools = [TOOL_MAP[t.id] for t in tools if t.id in TOOL_MAP]
    state["_active_tools"] = active_lc_tools  # type: ignore[typeddict-unknown-key]
    return state


def agent_node(state: AgentState) -> dict:
    active_tools = state.get("_active_tools", list(TOOL_MAP.values()))  # type: ignore[attr-defined]
    bound_llm = llm.bind_tools(active_tools)
    response = bound_llm.invoke(state["messages"])
    return {"messages": [response]}


def tool_node(state: AgentState) -> dict:
    last_message = state["messages"][-1]
    assert isinstance(last_message, AIMessage)
    results = []
    for call in last_message.tool_calls:
        lc_tool = TOOL_MAP.get(call["name"])
        if lc_tool:
            result = lc_tool.invoke(call["args"])
            assembler.record_tool_use(call["name"])
        else:
            result = f"Unknown tool: {call['name']}"
        results.append(ToolMessage(content=str(result), tool_call_id=call["id"]))
    return {"messages": results}


def should_continue(state: AgentState) -> str:
    last = state["messages"][-1]
    if isinstance(last, AIMessage) and last.tool_calls:
        return "tools"
    return END


# ---------------------------------------------------------------------------
# 4. Build and compile the graph
# ---------------------------------------------------------------------------

graph = StateGraph(AgentState)
graph.add_node("retrieve_tools", retrieve_tools_node)
graph.add_node("agent", agent_node)
graph.add_node("tools", tool_node)

graph.set_entry_point("retrieve_tools")
graph.add_edge("retrieve_tools", "agent")
graph.add_conditional_edges("agent", should_continue, {"tools": "tools", END: END})
graph.add_edge("tools", "retrieve_tools")

app = graph.compile()


# ---------------------------------------------------------------------------
# 5. Run
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    result = app.invoke({
        "messages": [HumanMessage(content="List files in the current directory, then read README.md")],
        "current_phase": "execution",
    })
    for msg in result["messages"]:
        role = "Human" if isinstance(msg, HumanMessage) else "AI" if isinstance(msg, AIMessage) else "Tool"
        print(f"\n[{role}]\n{msg.content}")
