# DTAE + LangGraph Example

Demonstrates DTAE dynamically selecting tools at each step of a LangGraph agent loop.

## What it shows

- Registry built from LangChain tool definitions
- `DynamicToolAssembler` selects top-3 relevant tools per step (out of 5 total)
- Tool usage recorded back to DTAE so the co-usage graph learns
- Works with `claude-sonnet-4-6` or any LangChain-compatible model

## Run

```bash
pip install dtae-core langgraph langchain-anthropic
export ANTHROPIC_API_KEY=your_key
python agent_with_dtae.py
```
