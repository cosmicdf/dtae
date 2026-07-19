# DTAE — Dynamic Tool Assembly Engine

<div align="center">

[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python](https://img.shields.io/badge/python-3.11%2B-blue?logo=python&logoColor=white)](https://www.python.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0%2B-blue?logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![CI Python](https://github.com/cosmicdf/dtae/actions/workflows/ci-python.yml/badge.svg)](https://github.com/cosmicdf/dtae/actions/workflows/ci-python.yml)
[![CI TypeScript](https://github.com/cosmicdf/dtae/actions/workflows/ci-typescript.yml/badge.svg)](https://github.com/cosmicdf/dtae/actions/workflows/ci-typescript.yml)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)

**Give your agent the right tools at the right time — not all of them at once.**

[Overview](#overview) · [Architecture](#architecture) · [Quick Start](#quick-start) · [Integrations](#integrations) · [Contributing](#contributing)

</div>

---

## Overview

AI agents today are shipped with dozens — sometimes hundreds — of tools loaded into the context window at once. This causes:

- **Context bloat** — tool descriptions consume 10–40% of the available token budget
- **Decision paralysis** — models perform worse when choosing from too many options
- **Context rot** — reasoning quality degrades as the window fills

**DTAE** solves this by dynamically assembling a small, relevant subset of tools at each step of the agent's reasoning loop — loading only what the agent needs, when it needs it.

```
Traditional:  [ALL 80 TOOLS loaded at start] → Agent → Action
DTAE:         Query → Retrieve top-8 → [8 TOOLS] → Agent → Action → re-evaluate → [6 TOOLS] → ...
```

Typical result: **~60% reduction in tool-description token usage** across a full agent run.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        DTAE Core                            │
│                                                             │
│   ┌─────────────────┐      ┌──────────────────────┐        │
│   │  Tool Registry  │      │    Tool Retriever     │        │
│   │  - metadata     │◄─────│  - semantic scoring   │        │
│   │  - embeddings   │      │  - phase-aware rank   │        │
│   │  - usage stats  │      │  - budget trimming    │        │
│   └─────────────────┘      └──────────────────────┘        │
│           ▲                           ▲                     │
│           │                           │                     │
│   ┌───────┴────────┐      ┌───────────┴──────────┐         │
│   │   Tool Graph   │      │   Context Monitor    │         │
│   │  (co-usage)    │      │  (trigger control)   │         │
│   └────────────────┘      └──────────────────────┘         │
└─────────────────────────────────────────────────────────────┘
          ▲                             │
          │                             ▼
   Tool Definitions               Agent (LLM)
   (MCP / local / API)            ReAct Loop
```

### Components

| Component | Description |
|---|---|
| **Tool Registry** | Stores all tool definitions with pre-computed embeddings and usage metadata |
| **Tool Retriever** | Scores and ranks tools using semantic similarity, session recency, co-usage, and task phase |
| **Tool Graph** | Weighted co-occurrence graph — tools frequently used together are loaded as clusters |
| **Context Monitor** | Decides when to trigger reassembly: on intent drift, tool errors, periodic refresh, or context pressure |

### Retrieval Scoring

```
score(tool) =
  α × semantic_similarity(query, tool_description)
+ β × session_recency(tool, last_N_steps)
+ γ × co_usage_score(tool, current_active_tools)
+ δ × task_phase_prior(tool, current_phase)
```

Default weights: `α=0.5 · β=0.2 · γ=0.2 · δ=0.1` — fully configurable.

---

## Quick Start

### Requirements

- Python 3.11+
- Node.js 20+ (for MCP server)

### Install Core (Python)

```bash
pip install dtae-core
```

### Basic Usage

```python
from dtae import ToolRegistry, DynamicToolAssembler

# Register your tools
registry = ToolRegistry()
registry.register_from_mcp("filesystem-mcp://localhost:3001")
registry.register_from_mcp("browser-mcp://localhost:3002")
registry.register_local(my_custom_tools)

# Create assembler
assembler = DynamicToolAssembler(registry=registry, max_tools=8)

# In your agent loop
tools = assembler.assemble(
    query="Fix the failing tests in src/auth/",
    context=agent_context
)
# → returns 6–10 tools relevant to the current step
```

### Install MCP Server (TypeScript)

```bash
npm install -g @dtae/mcp-server
dtae-mcp --registry http://localhost:8000 --port 3100
```

Connect your agent to `dtae-mcp` instead of individual tool servers. DTAE acts as an intelligent proxy, forwarding calls while controlling what's visible in context.

---

## Integrations

### LangGraph

```python
from dtae.integrations.langgraph import DTAERetrieverNode

retriever_node = DTAERetrieverNode(assembler=assembler)

graph = StateGraph(AgentState)
graph.add_node("retrieve_tools", retriever_node)
graph.add_node("agent", call_model)
graph.add_node("tools", tool_executor)

graph.add_conditional_edges("tools", should_reassemble, {
    True: "retrieve_tools",
    False: "agent"
})
```

### OpenAI Function Calling

```python
from dtae.integrations.openai import DTAEOpenAI

client = DTAEOpenAI(registry=registry, max_tools=10)

response = client.chat.completions.create(
    model="gpt-4o",
    messages=messages,
    # tools= is handled dynamically by DTAE — no need to pass it
)
```

### Claude (Anthropic SDK)

```python
from dtae.integrations.anthropic import DTAEAnthropic

client = DTAEAnthropic(registry=registry, max_tools=10)

response = client.messages.create(
    model="claude-sonnet-4-6",
    messages=messages,
    # tools assembled automatically
)
```

---

## Configuration

```python
assembler = DynamicToolAssembler(
    registry=registry,

    # How many tools to keep in context at once
    max_tools=8,

    # Max tokens to spend on tool descriptions
    max_tool_tokens=2000,

    # Reassembly triggers
    refresh_every_n_steps=5,
    reassemble_on_tool_error=True,
    reassemble_on_intent_drift=True,
    context_pressure_threshold=0.65,   # reassemble when context > 65% full

    # Scoring weights
    weights={"semantic": 0.5, "recency": 0.2, "co_usage": 0.2, "phase": 0.1},

    # Always include these tools regardless of score
    always_include=["task_complete", "ask_clarification"],
)
```

---

## Project Structure

```
dtae/
├── packages/
│   ├── core/                  # Python — core engine
│   │   ├── dtae/
│   │   │   ├── registry.py    # Tool storage + embedding
│   │   │   ├── retriever.py   # Scoring + ranking
│   │   │   ├── graph.py       # Co-usage graph
│   │   │   └── monitor.py     # Reassembly triggers
│   │   ├── tests/
│   │   └── pyproject.toml
│   └── mcp-server/            # TypeScript — MCP proxy server
│       ├── src/
│       │   ├── server.ts
│       │   └── proxy.ts
│       ├── package.json
│       └── tsconfig.json
└── .github/
    └── workflows/             # CI for both packages
```

---

## Roadmap

- [x] Core retrieval engine (semantic + graph scoring)
- [x] MCP server proxy
- [x] LangGraph integration
- [x] OpenAI + Anthropic SDK integrations
- [ ] DTAE Cloud (hosted registry + analytics)
- [ ] Tool Marketplace (third-party tool publishers)
- [ ] Description Optimizer (AI-assisted tool description rewriting)
- [ ] Trace Analyzer (harness-level failure diagnosis)

---

## Contributing

Contributions are welcome. Please read [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

```bash
# Clone and install dev dependencies
git clone https://github.com/cosmicdf/dtae
cd dtae

# Python core
cd packages/core && pip install -e ".[dev]"

# TypeScript MCP server
cd packages/mcp-server && npm install
```

---

## License

Apache License 2.0 — see [LICENSE](LICENSE) for details.

---

<div align="center">
  <sub>Built by <a href="https://github.com/cosmicdf">cosmicdf</a> · Inspired by <a href="https://www.langchain.com/blog/the-anatomy-of-an-agent-harness">The Anatomy of an Agent Harness</a></sub>
</div>
