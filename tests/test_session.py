"""Tests for session context manager."""

import pytest
from unittest.mock import patch, MagicMock

from agentwire.session import session, get_current_session, _set_session
from agentwire.models import MessageType


def test_get_current_session_default():
    """Test getting current session returns default when no context."""
    from agentwire.emitter import _config
    session_id = get_current_session()
    assert session_id == _config.default_session


def test_session_context_manager():
    """Test session context manager sets and restores session ID."""
    original_session = get_current_session()
    
    with patch("agentwire.session.emit_sync") as mock_emit:
        with session("test-session-123", name="Test Session"):
            # Inside context, session should be set
            assert get_current_session() == "test-session-123"
            
            # Should have emitted session_start
            assert mock_emit.call_count == 1
            start_msg = mock_emit.call_args_list[0][0][0]
            assert start_msg.type == MessageType.SYSTEM
            assert start_msg.session_id == "test-session-123"
            assert "started" in start_msg.content.lower()
            assert start_msg.metadata["event"] == "session_start"
            assert start_msg.metadata["name"] == "Test Session"
        
        # After context, should have emitted session_end
        assert mock_emit.call_count == 2
        end_msg = mock_emit.call_args_list[1][0][0]
        assert end_msg.type == MessageType.SYSTEM
        assert end_msg.session_id == "test-session-123"
        assert "ended" in end_msg.content.lower()
        assert end_msg.metadata["event"] == "session_end"
    
    # After context, session should be restored
    assert get_current_session() == original_session


def test_nested_sessions():
    """Test that nested sessions work correctly."""
    with patch("agentwire.session.emit_sync"):
        with session("outer-session"):
            assert get_current_session() == "outer-session"
            
            with session("inner-session"):
                assert get_current_session() == "inner-session"
            
            # After inner context, should restore to outer
            assert get_current_session() == "outer-session"


def test_session_without_name():
    """Test session context manager without a name."""
    with patch("agentwire.session.emit_sync") as mock_emit:
        with session("no-name-session"):
            assert get_current_session() == "no-name-session"
        
        # Check that messages were emitted without name in metadata
        start_msg = mock_emit.call_args_list[0][0][0]
        assert "name" not in start_msg.metadata or start_msg.metadata.get("name") is None


def test_session_exception_handling():
    """Test that session end is emitted even if exception occurs."""
    with patch("agentwire.session.emit_sync") as mock_emit:
        try:
            with session("error-session"):
                raise ValueError("Test error")
        except ValueError:
            pass
        
        # Should have emitted both start and end
        assert mock_emit.call_count == 2
        end_msg = mock_emit.call_args_list[1][0][0]
        assert end_msg.metadata["event"] == "session_end"


def test_session_yields_session_id():
    """Test that session context manager yields the session ID."""
    with patch("agentwire.session.emit_sync"):
        with session("yield-test") as session_id:
            assert session_id == "yield-test"
