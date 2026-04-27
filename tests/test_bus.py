"""Tests for the FastAPI bus server."""

import pytest
from httpx import AsyncClient, ASGITransport
from datetime import datetime

from agentwire.bus import app, store
from agentwire.models import WireMessage, MessageType


@pytest.fixture
async def client():
    """Create an async test client."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    # Clean up after each test
    await store.clear()


@pytest.mark.asyncio
async def test_create_message(client):
    """Test POST /api/messages endpoint."""
    msg_data = {
        "session_id": "test-session-1",
        "sender": "agent1",
        "receiver": "agent2",
        "type": "TASK",
        "content": "Do something important",
        "tokens_in": 50,
        "tokens_out": 100,
    }
    
    response = await client.post("/api/messages", json=msg_data)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "id" in data


@pytest.mark.asyncio
async def test_create_message_with_cost_calculation(client):
    """Test that cost is auto-calculated when model is provided."""
    msg_data = {
        "session_id": "test-session-2",
        "sender": "agent1",
        "receiver": "llm",
        "type": "TASK",
        "content": "Generate text",
        "tokens_in": 1000,
        "tokens_out": 2000,
        "model": "claude-sonnet-4-6",
    }
    
    response = await client.post("/api/messages", json=msg_data)
    assert response.status_code == 200
    
    # Verify the message was stored with calculated cost
    sessions_response = await client.get("/api/sessions")
    sessions = sessions_response.json()
    assert len(sessions) > 0
    
    # Get messages for the session
    messages_response = await client.get(f"/api/sessions/test-session-2/messages")
    messages = messages_response.json()
    assert len(messages) == 1
    
    # Cost should be: 1000 * 0.000003 + 2000 * 0.000015 = 0.003 + 0.03 = 0.033
    assert messages[0]["cost_usd"] == 0.033


@pytest.mark.asyncio
async def test_get_sessions(client):
    """Test GET /api/sessions endpoint."""
    # Create a few messages in different sessions
    for i in range(3):
        msg_data = {
            "session_id": f"session-{i}",
            "sender": f"agent{i}",
            "receiver": "agent-next",
            "type": "TASK",
            "content": f"Task {i}",
        }
        await client.post("/api/messages", json=msg_data)
    
    response = await client.get("/api/sessions")
    assert response.status_code == 200
    sessions = response.json()
    assert len(sessions) == 3
    
    # Check session structure
    session = sessions[0]
    assert "id" in session
    assert "started_at" in session
    assert "message_count" in session
    assert session["message_count"] >= 1


@pytest.mark.asyncio
async def test_get_session_by_id(client):
    """Test GET /api/sessions/{id} endpoint."""
    # Create a message
    msg_data = {
        "session_id": "specific-session",
        "sender": "agent1",
        "receiver": "agent2",
        "type": "RESULT",
        "content": "Task completed",
    }
    await client.post("/api/messages", json=msg_data)
    
    response = await client.get("/api/sessions/specific-session")
    assert response.status_code == 200
    session = response.json()
    assert session["id"] == "specific-session"
    assert session["message_count"] == 1


@pytest.mark.asyncio
async def test_get_session_not_found(client):
    """Test GET /api/sessions/{id} with non-existent session."""
    response = await client.get("/api/sessions/nonexistent")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_session_messages(client):
    """Test GET /api/sessions/{id}/messages endpoint."""
    session_id = "message-test-session"
    
    # Create multiple messages in order
    for i in range(5):
        msg_data = {
            "session_id": session_id,
            "sender": f"agent{i}",
            "receiver": f"agent{i+1}",
            "type": "TASK",
            "content": f"Message {i}",
        }
        await client.post("/api/messages", json=msg_data)
    
    response = await client.get(f"/api/sessions/{session_id}/messages")
    assert response.status_code == 200
    messages = response.json()
    assert len(messages) == 5
    
    # Verify messages are ordered by timestamp
    for i, msg in enumerate(messages):
        assert msg["content"] == f"Message {i}"


@pytest.mark.asyncio
async def test_get_stats(client):
    """Test GET /api/stats endpoint."""
    # Create messages across multiple sessions
    for session_idx in range(2):
        for msg_idx in range(3):
            msg_data = {
                "session_id": f"stats-session-{session_idx}",
                "sender": "agent1",
                "receiver": "agent2",
                "type": "TASK",
                "content": "Test message",
                "tokens_in": 100,
                "tokens_out": 200,
                "model": "gpt-4o-mini",
            }
            await client.post("/api/messages", json=msg_data)
    
    response = await client.get("/api/stats")
    assert response.status_code == 200
    stats = response.json()
    
    assert stats["total_messages"] == 6
    assert stats["total_sessions"] == 2
    assert stats["total_tokens"] == 6 * 300  # 6 messages * 300 tokens each
    assert stats["total_cost_usd"] > 0


@pytest.mark.asyncio
async def test_delete_session(client):
    """Test DELETE /api/sessions/{id} endpoint."""
    # Create a session with messages
    session_id = "delete-test-session"
    msg_data = {
        "session_id": session_id,
        "sender": "agent1",
        "receiver": "agent2",
        "type": "TASK",
        "content": "To be deleted",
    }
    await client.post("/api/messages", json=msg_data)
    
    # Verify it exists
    response = await client.get(f"/api/sessions/{session_id}")
    assert response.status_code == 200
    
    # Delete it
    delete_response = await client.delete(f"/api/sessions/{session_id}")
    assert delete_response.status_code == 200
    
    # Verify it's gone
    response = await client.get(f"/api/sessions/{session_id}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_clear_all(client):
    """Test DELETE /api/messages endpoint."""
    # Create some messages
    for i in range(3):
        msg_data = {
            "session_id": f"clear-session-{i}",
            "sender": "agent1",
            "receiver": "agent2",
            "type": "TASK",
            "content": f"Message {i}",
        }
        await client.post("/api/messages", json=msg_data)
    
    # Verify they exist
    stats = await client.get("/api/stats")
    assert stats.json()["total_messages"] > 0
    
    # Clear all
    response = await client.delete("/api/messages")
    assert response.status_code == 200
    
    # Verify everything is gone
    stats = await client.get("/api/stats")
    assert stats.json()["total_messages"] == 0
    assert stats.json()["total_sessions"] == 0


@pytest.mark.asyncio
async def test_message_round_trip(client):
    """Test that a message can be posted and retrieved with all fields intact."""
    original_msg = {
        "id": "test-msg-123",
        "session_id": "round-trip-session",
        "parent_id": "parent-msg-456",
        "sender": "researcher",
        "receiver": "writer",
        "type": "RESULT",
        "content": "Here are the research findings...",
        "metadata": {"source": "web", "confidence": 0.95},
        "tokens_in": 500,
        "tokens_out": 1500,
        "model": "claude-sonnet-4-6",
        "latency_ms": 2500,
        "tags": ["research", "important"],
    }
    
    # Post the message
    post_response = await client.post("/api/messages", json=original_msg)
    assert post_response.status_code == 200
    
    # Retrieve it
    get_response = await client.get("/api/sessions/round-trip-session/messages")
    messages = get_response.json()
    assert len(messages) == 1
    
    retrieved_msg = messages[0]
    assert retrieved_msg["id"] == original_msg["id"]
    assert retrieved_msg["session_id"] == original_msg["session_id"]
    assert retrieved_msg["parent_id"] == original_msg["parent_id"]
    assert retrieved_msg["sender"] == original_msg["sender"]
    assert retrieved_msg["receiver"] == original_msg["receiver"]
    assert retrieved_msg["type"] == original_msg["type"]
    assert retrieved_msg["content"] == original_msg["content"]
    assert retrieved_msg["metadata"] == original_msg["metadata"]
    assert retrieved_msg["tokens_in"] == original_msg["tokens_in"]
    assert retrieved_msg["tokens_out"] == original_msg["tokens_out"]
    assert retrieved_msg["model"] == original_msg["model"]
    assert retrieved_msg["latency_ms"] == original_msg["latency_ms"]
    assert retrieved_msg["tags"] == original_msg["tags"]
    assert retrieved_msg["cost_usd"] > 0  # Should be auto-calculated
