# DTAE + Anthropic SDK Example

Demonstrates DTAE with the raw Anthropic Python SDK — no framework required.

## What it shows

- Minimal agent loop with `client.messages.create`
- DTAE assembles the tool subset passed to each API call
- `record_tool_use` updates the co-usage graph after each call

## Run

```bash
pip install dtae-core anthropic
export ANTHROPIC_API_KEY=your_key
python agent_with_dtae.py
```
