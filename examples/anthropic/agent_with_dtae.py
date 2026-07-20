"""
Anthropic SDK agent example using DTAE for just-in-time tool assembly.

Run:
    pip install dtae-core anthropic
    ANTHROPIC_API_KEY=your_key python agent_with_dtae.py
"""

from __future__ import annotations

import json
import os
from typing import Any

import anthropic

from dtae import DynamicToolAssembler, ToolEntry, ToolRegistry


# ---------------------------------------------------------------------------
# 1. Tool implementations
# ---------------------------------------------------------------------------

def read_file(path: str) -> str:
    try:
        with open(path) as f:
            return f.read()
    except FileNotFoundError:
        return f"File not found: {path}"


def list_directory(path: str = ".") -> str:
    import os as _os
    return "\n".join(sorted(_os.listdir(path)))


def run_python(code: str) -> str:
    import io, contextlib
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):
            exec(code, {})  # noqa: S102
        return buf.getvalue() or "(no output)"
    except Exception as e:
        return f"Error: {e}"


def web_search(query: str) -> str:
    return f"[stub] Search results for: {query}"


def write_file(path: str, content: str) -> str:
    with open(path, "w") as f:
        f.write(content)
    return f"Written {len(content)} bytes to {path}"


HANDLERS: dict[str, Any] = {
    "read_file": read_file,
    "list_directory": list_directory,
    "run_python": run_python,
    "web_search": web_search,
    "write_file": write_file,
}

# Anthropic tool definitions (full set)
ALL_TOOL_DEFS = [
    {
        "name": "read_file",
        "description": "Read the contents of a file at the given path.",
        "input_schema": {
            "type": "object",
            "properties": {"path": {"type": "string", "description": "File path to read"}},
            "required": ["path"],
        },
    },
    {
        "name": "list_directory",
        "description": "List files in a directory.",
        "input_schema": {
            "type": "object",
            "properties": {"path": {"type": "string", "description": "Directory path", "default": "."}},
        },
    },
    {
        "name": "run_python",
        "description": "Execute a Python code snippet and return stdout output.",
        "input_schema": {
            "type": "object",
            "properties": {"code": {"type": "string", "description": "Python code to execute"}},
            "required": ["code"],
        },
    },
    {
        "name": "web_search",
        "description": "Search the web for information about a topic.",
        "input_schema": {
            "type": "object",
            "properties": {"query": {"type": "string", "description": "Search query"}},
            "required": ["query"],
        },
    },
    {
        "name": "write_file",
        "description": "Write text content to a file at the given path.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "content": {"type": "string"},
            },
            "required": ["path", "content"],
        },
    },
]

TOOL_DEF_MAP = {t["name"]: t for t in ALL_TOOL_DEFS}


# ---------------------------------------------------------------------------
# 2. DTAE setup
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

    for td in ALL_TOOL_DEFS:
        entry = ToolEntry(
            id=td["name"],
            name=td["name"],
            description=td["description"],
            parameters=td["input_schema"],
            tags=tag_map.get(td["name"], []),
            embedding=[],
        )
        registry._tools[entry.id] = entry

    return registry


registry = build_registry()
assembler = DynamicToolAssembler(registry=registry, max_tools=3)
client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])


# ---------------------------------------------------------------------------
# 3. Agent loop
# ---------------------------------------------------------------------------

def run_agent(task: str, phase: str = "execution", max_steps: int = 10) -> str:
    messages: list[dict[str, Any]] = [{"role": "user", "content": task}]

    for step in range(max_steps):
        # Pick relevant tools for this step
        active_entries = assembler.assemble(
            query=messages[-1]["content"] if isinstance(messages[-1]["content"], str) else task,
            phase=phase,
        )
        active_tools = [TOOL_DEF_MAP[e.id] for e in active_entries if e.id in TOOL_DEF_MAP]

        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=4096,
            tools=active_tools,
            messages=messages,
        )

        # Append assistant response
        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason == "end_turn":
            # Extract final text
            for block in response.content:
                if hasattr(block, "text"):
                    return block.text
            return "(done)"

        if response.stop_reason == "tool_use":
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    handler = HANDLERS.get(block.name)
                    if handler:
                        result = handler(**block.input)
                        assembler.record_tool_use(block.name)
                    else:
                        result = f"Unknown tool: {block.name}"
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": str(result),
                    })
            messages.append({"role": "user", "content": tool_results})

    return "(max steps reached)"


# ---------------------------------------------------------------------------
# 4. Run
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    answer = run_agent(
        task="List the files in the current directory, then write a file called hello.txt with 'Hello from DTAE!'",
        phase="execution",
    )
    print(answer)
