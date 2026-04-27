"""Tests for WebSocket functionality."""

import pytest
import asyncio
from httpx import AsyncClient, ASGITransport
from fastapi.testclient import TestClient

from agentwire.bus import app, store, manager
from agentwire.models import WireMessage, MessageType


@pytest.fixture
async def client():
    """Create an async test client."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    # Clean up after each test
    await store.clear()
    manager.active_connections.clear()


@pytest.mark.asyncio
async def test_websocket_connection():
    """Test WebSocket connection and disconnection."""
    test_client = TestClient(app)
    
    with test_client.websocket_connect("/ws") as websocket:
        # Connection should be established
        assert len(manager.active_connections) == 1
        
        # Send ping
        websocket.send_text("ping")
        response = websocket.receive_text()
        assert response == "pong"
    
    # After context, connection should be closed
    assert len(manager.active_connections) == 0


@pytest.mark.asyncio
async def test_websocket_receives_new_messages():
    """Test that WebSocket clients receive new messages."""
    test_client = TestClient(app)
    
    with test_client.websocket_connect("/ws") as websocket:
        # Post a message via REST API
        msg_data = {
            "session_id": "ws-test-session",
            "sender": "agent1",
            "receiver": "agent2",
            "type": "TASK",
            "content": "Test message for WebSocket",
        }
        
        # Use a separate client to post the message
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            await ac.post("/api/messages", json=msg_data)
        
        # WebSocket should receive the message
        data = websocket.receive_json()
        assert data["event"] == "message"
        assert data["data"]["content"] == "Test message for WebSocket"
        assert data["data"]["sender"] == "agent1"


@pytest.mark.asyncio
async def test_websocket_receives_session_events():
    """Test that WebSocket clients receive session start/end events."""
    test_client = TestClient(app)
    
    with test_client.websocket_connect("/ws") as websocket:
        # Post a session start message
        start_msg = {
            "session_id": "event-test-session",
            "sender": "system",
            "receiver": "broadcast",
            "type": "SYSTEM",
            "content": "Session started",
            "metadata": {"event": "session_start", "name": "Test Session"},
        }
        
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            await ac.post("/api/messages", json=start_msg)
        
        # Should receive the message event
        msg_event = websocket.receive_json()
        assert msg_event["event"] == "message"
        
        # Should receive the session_start event
        session_event = websocket.receive_json()
        assert session_event["event"] == "session_start"
        assert session_event["data"]["session_id"] == "event-test-session"
        assert session_event["data"]["name"] == "Test Session"


@pytest.mark.asyncio
async def test_websocket_sends_recent_messages_on_connect():
    """Test that WebSocket sends recent messages when connecting with session_id."""
    # First, create some messages
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        for i in range(5):
            msg_data = {
                "session_id": "history-session",
                "sender": f"agent{i}",
                "receiver": "agent-next",
                "type": "TASK",
                "content": f"Message {i}",
            }
            await ac.post("/api/messages", json=msg_data)
    
    # Now connect with session_id
    test_client = TestClient(app)
    with test_client.websocket_connect("/ws?session_id=history-session") as websocket:
        # Should receive the 5 recent messages
        messages_received = []
        for _ in range(5):
            data = websocket.receive_json()
            if data["event"] == "message":
                messages_received.append(data["data"]["content"])
        
        assert len(messages_received) == 5
        assert "Message 0" in messages_received
        assert "Message 4" in messages_received


@pytest.mark.asyncio
async def test_multiple_websocket_clients():
    """Test that multiple WebSocket clients all receive broadcasts."""
    test_client = TestClient(app)
    
    with test_client.websocket_connect("/ws") as ws1, \
         test_client.websocket_connect("/ws") as ws2:
        
        # Both should be connected
        assert len(manager.active_connections) == 2
        
        # Post a message
        msg_data = {
            "session_id": "multi-client-session",
            "sender": "agent1",
            "receiver": "agent2",
            "type": "RESULT",
            "content": "Broadcast to all",
        }
        
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            await ac.post("/api/messages", json=msg_data)
        
        # Both clients should receive the message
        data1 = ws1.receive_json()
        data2 = ws2.receive_json()
        
        assert data1["event"] == "message"
        assert data2["event"] == "message"
        assert data1["data"]["content"] == "Broadcast to all"
        assert data2["data"]["content"] == "Broadcast to all"


@pytest.mark.asyncio
async def test_connection_manager_disconnect():
    """Test ConnectionManager disconnect method."""
    from unittest.mock import MagicMock
    
    # Create mock WebSocket
    mock_ws = MagicMock()
    
    # Add to connections
    manager.active_connections.append(mock_ws)
    assert len(manager.active_connections) == 1
    
    # Disconnect
    manager.disconnect(mock_ws)
    assert len(manager.active_connections) == 0


@pytest.mark.asyncio
async def test_broadcast_handles_disconnected_clients():
    """Test that broadcast handles disconnected clients gracefully."""
    from unittest.mock import AsyncMock, MagicMock
    
    # Create mock WebSockets - one working, one failing
    working_ws = AsyncMock()
    failing_ws = AsyncMock()
    failing_ws.send_json.side_effect = Exception("Connection lost")
    
    # Add both to connections
    manager.active_connections = [working_ws, failing_ws]
    
    # Broadcast a message
    await manager.broadcast({"event": "test", "data": {}})
    
    # Working connection should have received the message
    working_ws.send_json.assert_called_once()
    
    # Failing connection should be removed
    assert failing_ws not in manager.active_connections
    assert working_ws in manager.active_connections
