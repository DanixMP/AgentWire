"""Tests for the message emitter."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import httpx

from agentwire.emitter import configure, emit, emit_sync, _config
from agentwire.models import WireMessage, MessageType


def test_configure_with_kwargs():
    """Test configuring with keyword arguments."""
    configure(
        bus_url="http://test:9999",
        default_session="test-session",
        enabled=False,
    )
    
    assert _config.bus_url == "http://test:9999"
    assert _config.default_session == "test-session"
    assert _config.enabled is False
    
    # Reset to defaults
    configure(
        bus_url="http://localhost:7433",
        default_session="default",
        enabled=True,
    )


def test_configure_with_env_vars(monkeypatch):
    """Test configuring with environment variables."""
    monkeypatch.setenv("AGENTWIRE_URL", "http://env:8888")
    monkeypatch.setenv("AGENTWIRE_SESSION", "env-session")
    monkeypatch.setenv("AGENTWIRE_ENABLED", "false")
    
    configure()
    
    assert _config.bus_url == "http://env:8888"
    assert _config.default_session == "env-session"
    assert _config.enabled is False
    
    # Reset
    configure(
        bus_url="http://localhost:7433",
        default_session="default",
        enabled=True,
    )


def test_configure_kwargs_override_env(monkeypatch):
    """Test that kwargs override environment variables."""
    monkeypatch.setenv("AGENTWIRE_URL", "http://env:8888")
    
    configure(bus_url="http://override:7777")
    
    assert _config.bus_url == "http://override:7777"
    
    # Reset
    configure(bus_url="http://localhost:7433")


@pytest.mark.asyncio
async def test_emit_when_disabled():
    """Test that emit does nothing when disabled."""
    configure(enabled=False)
    
    msg = WireMessage(
        session_id="test",
        sender="agent1",
        receiver="agent2",
        type=MessageType.TASK,
        content="Test",
    )
    
    # Should not raise and should not make any HTTP calls
    with patch("httpx.AsyncClient") as mock_client:
        await emit(msg)
        mock_client.assert_not_called()
    
    # Reset
    configure(enabled=True)


@pytest.mark.asyncio
async def test_emit_handles_http_errors():
    """Test that emit logs warnings but doesn't raise on HTTP errors."""
    configure(enabled=True, bus_url="http://localhost:7433")
    
    msg = WireMessage(
        session_id="test",
        sender="agent1",
        receiver="agent2",
        type=MessageType.TASK,
        content="Test",
    )
    
    # Mock httpx to raise an error
    with patch("httpx.AsyncClient") as mock_client:
        mock_instance = AsyncMock()
        mock_instance.__aenter__.return_value = mock_instance
        mock_instance.__aexit__.return_value = None
        mock_instance.post.side_effect = httpx.HTTPError("Connection failed")
        mock_client.return_value = mock_instance
        
        # Should not raise
        from agentwire.emitter import _emit_async
        await _emit_async(msg)


def test_emit_sync_creates_background_thread():
    """Test that emit_sync runs in a background thread."""
    msg = WireMessage(
        session_id="test",
        sender="agent1",
        receiver="agent2",
        type=MessageType.TASK,
        content="Test",
    )
    
    with patch("threading.Thread") as mock_thread:
        mock_thread_instance = MagicMock()
        mock_thread.return_value = mock_thread_instance
        
        emit_sync(msg)
        
        # Verify thread was created and started
        mock_thread.assert_called_once()
        mock_thread_instance.start.assert_called_once()
        
        # Verify daemon=True was set
        call_kwargs = mock_thread.call_args[1]
        assert call_kwargs.get("daemon") is True
