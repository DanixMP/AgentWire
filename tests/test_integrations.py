"""Tests for framework integrations."""

import pytest
from unittest.mock import MagicMock, patch
from uuid import uuid4

from agentwire.models import MessageType


def test_langchain_callback_import():
    """Test that LangChain callback can be imported."""
    try:
        from agentwire.integrations.langchain import AgentWireCallback
        assert AgentWireCallback is not None
    except ImportError:
        pytest.skip("LangChain not installed")


def test_langchain_callback_initialization():
    """Test LangChain callback initialization."""
    try:
        from agentwire.integrations.langchain import AgentWireCallback
        
        callback = AgentWireCallback(agent_name="test-agent", session_id="test-session")
        assert callback.agent_name == "test-agent"
        assert callback.session_id == "test-session"
    except ImportError:
        pytest.skip("LangChain not installed")


def test_langchain_callback_llm_start():
    """Test LangChain callback on_llm_start."""
    try:
        from agentwire.integrations.langchain import AgentWireCallback
        
        callback = AgentWireCallback(agent_name="test-agent", session_id="test-session")
        
        with patch("agentwire.integrations.langchain.emit_sync") as mock_emit:
            run_id = uuid4()
            callback.on_llm_start(
                serialized={"name": "gpt-4"},
                prompts=["Test prompt"],
                run_id=run_id,
            )
            
            # Verify emit was called
            mock_emit.assert_called_once()
            msg = mock_emit.call_args[0][0]
            
            assert msg.sender == "test-agent"
            assert msg.receiver == "llm"
            assert msg.type == MessageType.TASK
            assert "Test prompt" in msg.content
    except ImportError:
        pytest.skip("LangChain not installed")


def test_autogen_hook_initialization():
    """Test AutoGen hook initialization."""
    from agentwire.integrations.autogen import AgentWireHook
    
    hook = AgentWireHook(name="test-agent", session_id="test-session")
    assert hook.name == "test-agent"
    assert hook.session_id == "test-session"


def test_autogen_hook_on_send():
    """Test AutoGen hook on_send."""
    from agentwire.integrations.autogen import AgentWireHook
    
    hook = AgentWireHook(name="test-agent", session_id="test-session")
    
    with patch("agentwire.integrations.autogen.emit_sync") as mock_emit:
        message = {
            "content": "Test message",
            "recipient": "other-agent",
            "role": "user",
        }
        
        result = hook.on_send(message)
        
        # Verify message passed through
        assert result == message
        
        # Verify emit was called
        mock_emit.assert_called_once()
        msg = mock_emit.call_args[0][0]
        
        assert msg.sender == "test-agent"
        assert msg.receiver == "other-agent"
        assert msg.type == MessageType.TASK
        assert "Test message" in msg.content


def test_autogen_hook_on_receive():
    """Test AutoGen hook on_receive."""
    from agentwire.integrations.autogen import AgentWireHook
    
    hook = AgentWireHook(name="test-agent", session_id="test-session")
    
    with patch("agentwire.integrations.autogen.emit_sync") as mock_emit:
        message = {
            "content": "Response message",
            "sender": "other-agent",
            "role": "assistant",
        }
        
        result = hook.on_receive(message)
        
        # Verify message passed through
        assert result == message
        
        # Verify emit was called
        mock_emit.assert_called_once()
        msg = mock_emit.call_args[0][0]
        
        assert msg.sender == "other-agent"
        assert msg.receiver == "test-agent"
        assert msg.type == MessageType.RESULT


def test_crewai_wire_crew():
    """Test CrewAI wire_crew function."""
    from agentwire.integrations.crewai import wire_crew
    
    # Create mock crew
    mock_agent = MagicMock()
    mock_agent.name = "test-agent"
    mock_agent.execute_task = MagicMock(return_value="Task result")
    
    mock_crew = MagicMock()
    mock_crew.agents = [mock_agent]
    
    # Wire the crew
    wire_crew(mock_crew, session_id="test-session")
    
    # Verify agent's execute_task was replaced
    assert mock_agent.execute_task != MagicMock
    
    # Execute task and verify messages emitted
    with patch("agentwire.integrations.crewai.emit_sync") as mock_emit:
        mock_task = MagicMock()
        mock_task.description = "Test task"
        
        result = mock_agent.execute_task(mock_task)
        
        assert result == "Task result"
        
        # Should emit TASK and RESULT messages
        assert mock_emit.call_count == 2
        
        # Check TASK message
        task_msg = mock_emit.call_args_list[0][0][0]
        assert task_msg.type == MessageType.TASK
        assert task_msg.sender == "orchestrator"
        assert task_msg.receiver == "test-agent"
        
        # Check RESULT message
        result_msg = mock_emit.call_args_list[1][0][0]
        assert result_msg.type == MessageType.RESULT
        assert result_msg.sender == "test-agent"
        assert result_msg.receiver == "orchestrator"


def test_crewai_wire_crew_error_handling():
    """Test CrewAI wire_crew error handling."""
    from agentwire.integrations.crewai import wire_crew
    
    # Create mock agent that raises error
    def failing_execute(task):
        raise ValueError("Task failed")
    
    mock_agent = MagicMock()
    mock_agent.name = "failing-agent"
    mock_agent.execute_task = failing_execute
    
    mock_crew = MagicMock()
    mock_crew.agents = [mock_agent]
    
    # Wire the crew
    wire_crew(mock_crew, session_id="test-session")
    
    # Execute task and verify ERROR message emitted
    with patch("agentwire.integrations.crewai.emit_sync") as mock_emit:
        mock_task = MagicMock()
        mock_task.description = "Test task"
        
        with pytest.raises(ValueError, match="Task failed"):
            mock_agent.execute_task(mock_task)
        
        # Should emit TASK and ERROR messages
        assert mock_emit.call_count == 2
        
        # Check ERROR message
        error_msg = mock_emit.call_args_list[1][0][0]
        assert error_msg.type == MessageType.ERROR
        assert "ValueError" in error_msg.content
        assert "Task failed" in error_msg.content
