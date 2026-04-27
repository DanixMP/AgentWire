"""Tests for graph endpoint."""

import pytest
from httpx import AsyncClient, ASGITransport

from agentwire.bus import app, store
from agentwire.models import MessageType


@pytest.fixture
async def client():
    """Create an async test client."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    # Clean up after each test
    await store.clear()


@pytest.mark.asyncio
async def test_graph_endpoint_empty_session(client):
    """Test graph endpoint with non-existent session."""
    response = await client.get("/api/sessions/nonexistent/graph")
    assert response.status_code == 200
    data = response.json()
    assert data["nodes"] == []
    assert data["edges"] == []


@pytest.mark.asyncio
async def test_graph_endpoint_with_messages(client):
    """Test graph endpoint with a simple message flow."""
    session_id = "graph-test-session"
    
    # Create a simple flow: orchestrator → researcher → writer
    messages = [
        {
            "session_id": session_id,
            "sender": "orchestrator",
            "receiver": "researcher",
            "type": "TASK",
            "content": "Research quantum computing",
            "tokens_in": 100,
            "tokens_out": 0,
        },
        {
            "session_id": session_id,
            "sender": "researcher",
            "receiver": "orchestrator",
            "type": "RESULT",
            "content": "Found 10 papers",
            "tokens_in": 500,
            "tokens_out": 200,
            "latency_ms": 2000,
        },
        {
            "session_id": session_id,
            "sender": "orchestrator",
            "receiver": "writer",
            "type": "TASK",
            "content": "Write article",
            "tokens_in": 200,
            "tokens_out": 0,
        },
        {
            "session_id": session_id,
            "sender": "writer",
            "receiver": "orchestrator",
            "type": "RESULT",
            "content": "Article complete",
            "tokens_in": 300,
            "tokens_out": 500,
            "latency_ms": 3000,
        },
    ]
    
    for msg in messages:
        await client.post("/api/messages", json=msg)
    
    # Get graph
    response = await client.get(f"/api/sessions/{session_id}/graph")
    assert response.status_code == 200
    data = response.json()
    
    # Check nodes
    assert len(data["nodes"]) == 3
    node_ids = {node["id"] for node in data["nodes"]}
    assert node_ids == {"orchestrator", "researcher", "writer"}
    
    # Check orchestrator node
    orchestrator = next(n for n in data["nodes"] if n["id"] == "orchestrator")
    assert orchestrator["message_count"] == 2  # Sent 2 messages
    assert orchestrator["total_tokens"] == 300  # 100 + 200
    assert orchestrator["dominant_type"] == "TASK"
    
    # Check edges
    assert len(data["edges"]) == 4
    
    # Check orchestrator → researcher edge
    orch_to_res = next(
        e for e in data["edges"]
        if e["source"] == "orchestrator" and e["target"] == "researcher"
    )
    assert orch_to_res["count"] == 1
    assert orch_to_res["dominant_type"] == "TASK"
    assert orch_to_res["total_tokens"] == 100
    
    # Check researcher → orchestrator edge
    res_to_orch = next(
        e for e in data["edges"]
        if e["source"] == "researcher" and e["target"] == "orchestrator"
    )
    assert res_to_orch["count"] == 1
    assert res_to_orch["dominant_type"] == "RESULT"
    assert res_to_orch["avg_latency_ms"] == 2000


@pytest.mark.asyncio
async def test_graph_filters_system_messages(client):
    """Test that system/broadcast/unknown receivers are filtered out."""
    session_id = "filter-test-session"
    
    messages = [
        {
            "session_id": session_id,
            "sender": "system",
            "receiver": "broadcast",
            "type": "SYSTEM",
            "content": "Session started",
        },
        {
            "session_id": session_id,
            "sender": "agent1",
            "receiver": "unknown",
            "type": "TASK",
            "content": "Task",
        },
        {
            "session_id": session_id,
            "sender": "agent1",
            "receiver": "agent2",
            "type": "TASK",
            "content": "Real task",
        },
    ]
    
    for msg in messages:
        await client.post("/api/messages", json=msg)
    
    response = await client.get(f"/api/sessions/{session_id}/graph")
    data = response.json()
    
    # Should have nodes for system and agent1, agent2
    # But only edge for agent1 → agent2
    assert len(data["edges"]) == 1
    assert data["edges"][0]["source"] == "agent1"
    assert data["edges"][0]["target"] == "agent2"


@pytest.mark.asyncio
async def test_graph_calculates_dominant_type(client):
    """Test that dominant message type is calculated correctly."""
    session_id = "dominant-test-session"
    
    # Send 3 TASK and 1 RESULT from agent1
    for i in range(3):
        await client.post("/api/messages", json={
            "session_id": session_id,
            "sender": "agent1",
            "receiver": "agent2",
            "type": "TASK",
            "content": f"Task {i}",
        })
    
    await client.post("/api/messages", json={
        "session_id": session_id,
        "sender": "agent1",
        "receiver": "agent2",
        "type": "RESULT",
        "content": "Result",
    })
    
    response = await client.get(f"/api/sessions/{session_id}/graph")
    data = response.json()
    
    # agent1 node should have TASK as dominant type (3 vs 1)
    agent1 = next(n for n in data["nodes"] if n["id"] == "agent1")
    assert agent1["dominant_type"] == "TASK"
    
    # Edge should also have TASK as dominant
    edge = data["edges"][0]
    assert edge["dominant_type"] == "TASK"
    assert edge["count"] == 4


@pytest.mark.asyncio
async def test_graph_handles_bidirectional_edges(client):
    """Test that bidirectional communication creates separate edges."""
    session_id = "bidirectional-test"
    
    messages = [
        {
            "session_id": session_id,
            "sender": "agent1",
            "receiver": "agent2",
            "type": "TASK",
            "content": "Request",
        },
        {
            "session_id": session_id,
            "sender": "agent2",
            "receiver": "agent1",
            "type": "RESULT",
            "content": "Response",
        },
    ]
    
    for msg in messages:
        await client.post("/api/messages", json=msg)
    
    response = await client.get(f"/api/sessions/{session_id}/graph")
    data = response.json()
    
    # Should have 2 edges (one in each direction)
    assert len(data["edges"]) == 2
    
    edge1 = next(e for e in data["edges"] if e["source"] == "agent1")
    assert edge1["target"] == "agent2"
    
    edge2 = next(e for e in data["edges"] if e["source"] == "agent2")
    assert edge2["target"] == "agent1"
