"""AutoGen integration for AgentWire."""

from typing import Any, Dict, Optional

from ..models import WireMessage, MessageType
from ..emitter import emit_sync
from ..session import get_current_session


class AgentWireHook:
    """
    AutoGen hook that emits WireMessages to AgentWire.
    
    Usage:
        from agentwire.integrations.autogen import AgentWireHook
        
        hook = AgentWireHook(name="orchestrator", session_id="run-1")
        agent.register_hook("process_message_before_send", hook.on_send)
        agent.register_hook("process_message_before_receive", hook.on_receive)
    """
    
    def __init__(
        self,
        name: str,
        session_id: Optional[str] = None,
    ):
        """
        Initialize the hook.
        
        Args:
            name: Name of the agent
            session_id: Optional session ID (uses thread-local context if not provided)
        """
        self.name = name
        self.session_id = session_id
    
    def _get_session_id(self) -> str:
        """Get session ID from explicit value or thread-local context."""
        return self.session_id or get_current_session()
    
    def on_send(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """
        Hook called before sending a message.
        
        Args:
            message: AutoGen message dict
        
        Returns:
            Unmodified message (pass-through)
        """
        # Determine message type
        msg_type = MessageType.TASK
        content = message.get("content", "")
        
        if "error" in content.lower() or message.get("role") == "error":
            msg_type = MessageType.ERROR
        elif "result" in content.lower() or message.get("role") == "assistant":
            msg_type = MessageType.RESULT
        
        # Emit message
        wire_msg = WireMessage(
            session_id=self._get_session_id(),
            sender=self.name,
            receiver=message.get("recipient", "unknown"),
            type=msg_type,
            content=str(content)[:500],
            metadata={
                "role": message.get("role"),
                "name": message.get("name"),
            },
        )
        emit_sync(wire_msg)
        
        return message  # Pass through unmodified
    
    def on_receive(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """
        Hook called before receiving a message.
        
        Args:
            message: AutoGen message dict
        
        Returns:
            Unmodified message (pass-through)
        """
        # Determine message type
        msg_type = MessageType.RESULT
        content = message.get("content", "")
        
        if "error" in content.lower():
            msg_type = MessageType.ERROR
        elif "tool" in str(message.get("role", "")).lower():
            msg_type = MessageType.TOOL_RESULT
        
        # Emit message
        wire_msg = WireMessage(
            session_id=self._get_session_id(),
            sender=message.get("sender", "unknown"),
            receiver=self.name,
            type=msg_type,
            content=str(content)[:500],
            metadata={
                "role": message.get("role"),
                "name": message.get("name"),
            },
        )
        emit_sync(wire_msg)
        
        return message  # Pass through unmodified


def wire_autogen_agent(agent: Any, name: str, session_id: Optional[str] = None) -> None:
    """
    Convenience function to wire an AutoGen agent.
    
    Args:
        agent: AutoGen agent instance
        name: Name for the agent
        session_id: Optional session ID
    
    Example:
        from agentwire.integrations.autogen import wire_autogen_agent
        
        wire_autogen_agent(my_agent, name="researcher", session_id="run-1")
    """
    hook = AgentWireHook(name=name, session_id=session_id)
    
    # Register hooks if agent supports them
    if hasattr(agent, "register_hook"):
        agent.register_hook("process_message_before_send", hook.on_send)
        agent.register_hook("process_message_before_receive", hook.on_receive)
    else:
        raise ValueError(
            f"Agent {agent} does not support hooks. "
            "Make sure you're using a compatible AutoGen version."
        )
