# Contributing to DTAE

Thank you for your interest in contributing. This document covers how to get started.

## Project layout

```
dtae/
├── packages/core/        Python engine — registry, retriever, graph, monitor
├── packages/api/         FastAPI REST server
├── packages/mcp-server/  TypeScript MCP proxy
└── examples/             Usage examples per integration
```

## Setup

```bash
git clone https://github.com/cosmicdf/dtae
cd dtae

# Python core
cd packages/core
pip install -e ".[dev]"

# TypeScript MCP server
cd ../mcp-server
npm install
```

## Running tests

```bash
# Python core
cd packages/core
python -m pytest tests/ -v

# API
cd packages/api
DTAE_DISABLE_EMBEDDINGS=true python -m pytest tests/ -v

# TypeScript
cd packages/mcp-server
npm test
```

## Linting and type checks

```bash
# Python
python -m ruff check dtae tests
python -m mypy dtae

# TypeScript
npm run typecheck
npm run lint
```

## What to work on

Check the [roadmap in README.md](README.md#roadmap) and open issues. Good first issues are tagged [`good first issue`](https://github.com/cosmicdf/dtae/issues?q=label%3A%22good+first+issue%22).

## Pull request checklist

- [ ] Tests pass locally
- [ ] New code has type annotations (Python) or TypeScript types
- [ ] No new dependencies added without discussion in an issue first
- [ ] Description explains *why*, not just *what*

## Commit style

```
type: short description

feat:     new feature
fix:      bug fix
docs:     documentation only
test:     tests only
refactor: no functional change
chore:    build, CI, deps
```

## License

By contributing, you agree your contributions are licensed under Apache 2.0.
