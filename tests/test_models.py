"""Tests for core data models."""

import pytest
from datetime import datetime
from agentwire.models import WireMessage, MessageType, Session


def test_wire_message_creation():
    """Test creating a WireMessage with required fields."""
    msg = WireMessage(
        session_id="test-session",
        sender="agent1",
        receiver="agent2",
        type=MessageType.TASK,
        content="Do something",
    )
    
    assert msg.session_id == "test-session"
    assert msg.sender == "agent1"
    assert msg.receiver == "agent2"
    assert msg.type == MessageType.TASK
    assert msg.content == "Do something"
    assert msg.id is not None  # Auto-generated UUID
    assert msg.tokens_in == 0
    assert msg.tokens_out == 0
    assert msg.cost_usd == 0.0
    assert isinstance(msg.timestamp, datetime)


def test_wire_message_with_tokens():
    """Test WireMessage with token and cost information."""
    msg = WireMessage(
        session_id="test-session",
        sender="agent1",
        receiver="llm",
        type=MessageType.TASK,
        content="Generate text",
        tokens_in=100,
        tokens_out=200,
        model="claude-sonnet-4-6",
        cost_usd=0.003,
        latency_ms=1500,
    )
    
    assert msg.tokens_in == 100
    assert msg.tokens_out == 200
    assert msg.model == "claude-sonnet-4-6"
    assert msg.cost_usd == 0.003
    assert msg.latency_ms == 1500


def test_message_type_enum():
    """Test MessageType enum values."""
    assert MessageType.TASK == "TASK"
    assert MessageType.RESULT == "RESULT"
    assert MessageType.ERROR == "ERROR"
    assert MessageType.TOOL_CALL == "TOOL_CALL"
    assert MessageType.TOOL_RESULT == "TOOL_RESULT"
    assert MessageType.SYSTEM == "SYSTEM"


def test_session_creation():
    """Test creating a Session."""
    now = datetime.utcnow()
    session = Session(
        id="session-1",
        name="Test Run",
        started_at=now,
        message_count=5,
        total_tokens=1000,
        total_cost_usd=0.05,
        agents=["agent1", "agent2"],
    )
    
    assert session.id == "session-1"
    assert session.name == "Test Run"
    assert session.started_at == now
    assert session.message_count == 5
    assert session.total_tokens == 1000
    assert session.total_cost_usd == 0.05
    assert session.agents == ["agent1", "agent2"]


def test_wire_message_serialization():
    """Test that WireMessage can be serialized to dict."""
    msg = WireMessage(
        session_id="test-session",
        sender="agent1",
        receiver="agent2",
        type=MessageType.RESULT,
        content="Task completed",
        metadata={"key": "value"},
        tags=["important"],
    )
    
    data = msg.model_dump()
    assert data["session_id"] == "test-session"
    assert data["sender"] == "agent1"
    assert data["type"] == "RESULT"
    assert data["metadata"] == {"key": "value"}
    assert data["tags"] == ["important"]
