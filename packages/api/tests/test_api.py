import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "ok"
    assert "tools_registered" in data
    assert "active_sessions" in data


def test_register_and_list_tools():
    r = client.post("/tools/", json={
        "name": "read_file",
        "description": "Read contents of a file",
        "parameters": {"type": "object", "properties": {"path": {"type": "string"}}},
        "tags": ["read", "filesystem"],
    })
    assert r.status_code == 201
    tool = r.json()
    assert tool["id"] == "read_file"

    r = client.get("/tools/")
    assert r.status_code == 200
    ids = [t["id"] for t in r.json()]
    assert "read_file" in ids


def test_assemble_returns_tools():
    # Register a tool first
    client.post("/tools/", json={
        "name": "bash_tool",
        "description": "Execute bash commands",
        "tags": ["run", "execution"],
    })

    r = client.post("/assemble/", json={
        "query": "run the test suite",
        "phase": "execution",
        "session_id": "test-session",
    })
    assert r.status_code == 200
    data = r.json()
    assert "tools" in data
    assert data["session_id"] == "test-session"
    assert data["token_estimate"] >= 0


def test_usage_record_and_stats():
    # Register tool
    client.post("/tools/", json={
        "name": "write_file",
        "description": "Write content to a file",
        "tags": ["write", "filesystem"],
    })

    r = client.post("/usage/", json={
        "tool_id": "write_file",
        "session_id": "test-session",
        "step": 2,
    })
    assert r.status_code == 204

    r = client.get("/usage/stats")
    assert r.status_code == 200
    stats = {s["tool_id"]: s for s in r.json()}
    assert "write_file" in stats
    assert stats["write_file"]["usage_count"] == 1


def test_assemble_invalid_phase_falls_back():
    r = client.post("/assemble/", json={
        "query": "anything",
        "phase": "nonexistent_phase",
        "session_id": "fallback-test",
    })
    assert r.status_code == 200
