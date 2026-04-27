"""Tests for agent wrapper."""

import pytest
from unittest.mock import patch, MagicMock
import time

from agentwire.wrapper import wrap, AgentProxy
from agentwire.models import MessageType


class DummyAgent:
    """Dummy agent for testing."""
    
    def __init__(self):
        self.state = "initial"
    
    def run(self, task: str) -> str:
        """Simulate running a task."""
        time.sleep(0.01)  # Small delay to test latency
        return f"Completed: {task}"
    
    def invoke(self, prompt: str) -> dict:
        """Simulate invoking with a prompt."""
        return {"result": f"Response to: {prompt}"}
    
    def other_method(self) -> str:
        """Method that should not be intercepted."""
        return "other"


def test_wrap_creates_proxy():
    """Test that wrap returns an AgentProxy."""
    agent = DummyAgent()
    wrapped = wrap(agent, name="test-agent")
    
    assert isinstance(wrapped, AgentProxy)
    assert wrapped._name == "test-agent"
    assert wrapped._agent is agent


def test_proxy_forwards_attributes():
    """Test that proxy forwards attribute access."""
    agent = DummyAgent()
    wrapped = wrap(agent, name="test-agent")
    
    # Should be able to access attributes
    assert wrapped.state == "initial"
    
    # Should be able to set attributes
    wrapped.state = "modified"
    assert agent.state == "modified"


def test_proxy_intercepts_run_method():
    """Test that proxy intercepts the run method."""
    agent = DummyAgent()
    wrapped = wrap(agent, name="test-agent", session_id="test-session")
    
    with patch("agentwire.wrapper.emit_sync") as mock_emit:
        result = wrapped.run("test task")
        
        # Should return the real result
        assert result == "Completed: test task"
        
        # Should have emitted 2 messages: TASK and RESULT
        assert mock_emit.call_count == 2
        
        # Check TASK message
        task_msg = mock_emit.call_args_list[0][0][0]
        assert task_msg.type == MessageType.TASK
        assert task_msg.sender == "test-agent"
        assert task_msg.session_id == "test-session"
        assert "run" in task_msg.content
        
        # Check RESULT message
        result_msg = mock_emit.call_args_list[1][0][0]
        assert result_msg.type == MessageType.RESULT
        assert result_msg.sender == "test-agent"
        assert result_msg.session_id == "test-session"
        assert "Completed" in result_msg.content
        assert result_msg.parent_id == task_msg.id
        assert result_msg.latency_ms > 0


def test_proxy_intercepts_invoke_method():
    """Test that proxy intercepts the invoke method."""
    agent = DummyAgent()
    wrapped = wrap(agent, name="test-agent", session_id="test-session")
    
    with patch("agentwire.wrapper.emit_sync") as mock_emit:
        result = wrapped.invoke("test prompt")
        
        # Should return the real result
        assert result == {"result": "Response to: test prompt"}
        
        # Should have emitted 2 messages
        assert mock_emit.call_count == 2
        
        # Check that invoke was mentioned
        task_msg = mock_emit.call_args_list[0][0][0]
        assert "invoke" in task_msg.content


def test_proxy_does_not_intercept_other_methods():
    """Test that proxy doesn't intercept non-standard methods."""
    agent = DummyAgent()
    wrapped = wrap(agent, name="test-agent")
    
    with patch("agentwire.wrapper.emit_sync") as mock_emit:
        result = wrapped.other_method()
        
        # Should return the real result
        assert result == "other"
        
        # Should NOT have emitted any messages
        mock_emit.assert_not_called()


def test_proxy_handles_exceptions():
    """Test that proxy emits ERROR message on exception."""
    class FailingAgent:
        def run(self, task: str):
            raise ValueError("Something went wrong")
    
    agent = FailingAgent()
    wrapped = wrap(agent, name="failing-agent", session_id="test-session")
    
    with patch("agentwire.wrapper.emit_sync") as mock_emit:
        with pytest.raises(ValueError, match="Something went wrong"):
            wrapped.run("test task")
        
        # Should have emitted 2 messages: TASK and ERROR
        assert mock_emit.call_count == 2
        
        # Check TASK message
        task_msg = mock_emit.call_args_list[0][0][0]
        assert task_msg.type == MessageType.TASK
        
        # Check ERROR message
        error_msg = mock_emit.call_args_list[1][0][0]
        assert error_msg.type == MessageType.ERROR
        assert error_msg.sender == "failing-agent"
        assert "ValueError" in error_msg.content
        assert "Something went wrong" in error_msg.content
        assert error_msg.parent_id == task_msg.id
        assert error_msg.latency_ms >= 0
        assert error_msg.metadata["error_type"] == "ValueError"


def test_proxy_uses_session_context():
    """Test that proxy uses session context when no session_id provided."""
    agent = DummyAgent()
    wrapped = wrap(agent, name="test-agent")  # No session_id
    
    with patch("agentwire.wrapper.emit_sync") as mock_emit:
        with patch("agentwire.wrapper.get_current_session", return_value="context-session"):
            wrapped.run("test task")
            
            # Should use session from context
            task_msg = mock_emit.call_args_list[0][0][0]
            assert task_msg.session_id == "context-session"


def test_proxy_repr():
    """Test string representation of proxy."""
    agent = DummyAgent()
    wrapped = wrap(agent, name="test-agent")
    
    repr_str = repr(wrapped)
    assert "AgentProxy" in repr_str
    assert "test-agent" in repr_str
    assert "DummyAgent" in repr_str


def test_proxy_with_args_and_kwargs():
    """Test that proxy handles methods with args and kwargs."""
    class ComplexAgent:
        def run(self, task: str, priority: int = 1, **options):
            return f"Task: {task}, Priority: {priority}, Options: {options}"
    
    agent = ComplexAgent()
    wrapped = wrap(agent, name="complex-agent", session_id="test-session")
    
    with patch("agentwire.wrapper.emit_sync") as mock_emit:
        result = wrapped.run("test", priority=5, debug=True, verbose=False)
        
        # Should return the real result
        assert "test" in result
        assert "5" in result
        
        # Check TASK message includes args/kwargs info
        task_msg = mock_emit.call_args_list[0][0][0]
        assert "run" in task_msg.content


def test_proxy_truncates_long_results():
    """Test that proxy truncates long result content."""
    class VerboseAgent:
        def run(self, task: str) -> str:
            return "x" * 500  # Long result
    
    agent = VerboseAgent()
    wrapped = wrap(agent, name="verbose-agent", session_id="test-session")
    
    with patch("agentwire.wrapper.emit_sync") as mock_emit:
        wrapped.run("test")
        
        # Check RESULT message is truncated to 200 chars
        result_msg = mock_emit.call_args_list[1][0][0]
        assert len(result_msg.content) == 200
