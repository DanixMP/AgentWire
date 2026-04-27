"""Agent wrapper for automatic message emission."""

import time
import traceback
from typing import Any, Optional
from datetime import datetime

from .models import WireMessage, MessageType
from .emitter import emit_sync
from .session import get_current_session


class AgentProxy:
    """
    Proxy object that wraps an agent and intercepts method calls.
    
    Automatically emits TASK and RESULT (or ERROR) messages for intercepted methods.
    All other attributes and methods pass through to the wrapped agent unchanged.
    """
    
    # Methods to intercept (tried in order)
    INTERCEPTED_METHODS = [
        "run",
        "invoke",
        "chat",
        "generate",
        "step",
        "execute",
        "__call__",
    ]
    
    def __init__(self, agent: Any, name: str, session_id: Optional[str] = None):
        """
        Create a proxy for an agent.
        
        Args:
            agent: The agent object to wrap
            name: Name of this agent (used as sender in messages)
            session_id: Optional session ID (overrides thread-local context)
        """
        # Store in __dict__ to avoid triggering __getattr__
        object.__setattr__(self, "_agent", agent)
        object.__setattr__(self, "_name", name)
        object.__setattr__(self, "_session_id", session_id)
    
    def __getattr__(self, attr: str) -> Any:
        """
        Forward attribute access to the wrapped agent.
        Intercept known method names to add message emission.
        """
        # Get the attribute from the wrapped agent
        value = getattr(self._agent, attr)
        
        # If it's one of our intercepted methods and it's callable, wrap it
        if attr in self.INTERCEPTED_METHODS and callable(value):
            return self._wrap_method(value, attr)
        
        # Otherwise return as-is
        return value
    
    def __setattr__(self, attr: str, value: Any) -> None:
        """Forward attribute setting to the wrapped agent."""
        setattr(self._agent, attr, value)
    
    def _wrap_method(self, method: callable, method_name: str) -> callable:
        """
        Wrap a method to emit TASK and RESULT/ERROR messages.
        
        Args:
            method: The original method to wrap
            method_name: Name of the method (for logging)
        
        Returns:
            Wrapped method that emits messages
        """
        def wrapped(*args, **kwargs):
            session_id = self._session_id or get_current_session()
            
            # Build task description from args/kwargs
            task_parts = []
            if args:
                task_parts.append(f"args={args[:2]}")  # First 2 args only
            if kwargs:
                task_parts.append(f"kwargs={list(kwargs.keys())[:3]}")  # First 3 keys
            task_desc = f"{method_name}({', '.join(task_parts)})"
            
            # Emit TASK message
            task_msg = WireMessage(
                session_id=session_id,
                sender=self._name,
                receiver="unknown",  # We don't know the receiver yet
                type=MessageType.TASK,
                content=task_desc,
                metadata={
                    "method": method_name,
                    "agent": self._name,
                },
            )
            emit_sync(task_msg)
            
            # Record start time
            start_time = time.time()
            
            try:
                # Call the real method
                result = method(*args, **kwargs)
                
                # Calculate latency
                latency_ms = int((time.time() - start_time) * 1000)
                
                # Emit RESULT message
                result_summary = str(result)[:200]  # First 200 chars
                result_msg = WireMessage(
                    session_id=session_id,
                    sender=self._name,
                    receiver="unknown",
                    type=MessageType.RESULT,
                    content=result_summary,
                    parent_id=task_msg.id,
                    latency_ms=latency_ms,
                    metadata={
                        "method": method_name,
                        "agent": self._name,
                        "success": True,
                    },
                )
                emit_sync(result_msg)
                
                # Return the real result unchanged
                return result
                
            except Exception as e:
                # Calculate latency
                latency_ms = int((time.time() - start_time) * 1000)
                
                # Emit ERROR message
                error_msg = WireMessage(
                    session_id=session_id,
                    sender=self._name,
                    receiver="unknown",
                    type=MessageType.ERROR,
                    content=f"{type(e).__name__}: {str(e)}",
                    parent_id=task_msg.id,
                    latency_ms=latency_ms,
                    metadata={
                        "method": method_name,
                        "agent": self._name,
                        "error_type": type(e).__name__,
                        "traceback": traceback.format_exc()[:500],  # First 500 chars
                    },
                )
                emit_sync(error_msg)
                
                # Re-raise the exception
                raise
        
        return wrapped
    
    def __repr__(self) -> str:
        """String representation showing this is a wrapped agent."""
        return f"AgentProxy({self._name}, wrapping {self._agent.__class__.__name__})"


def wrap(agent: Any, *, name: str, session_id: Optional[str] = None) -> Any:
    """
    Wrap an agent to automatically emit WireMessages.
    
    Returns a proxy object that behaves identically to the agent but intercepts
    calls to known method names and emits WireMessages automatically.
    
    Intercepted method names (tried in order):
      run, invoke, chat, generate, step, execute, __call__
    
    Interception flow:
      1. Record timestamp_start
      2. Emit TASK WireMessage (sender=name, receiver="unknown")
      3. Call the real method
      4. Record latency_ms
      5. Emit RESULT WireMessage with the return value summary
         (or ERROR WireMessage if an exception was raised)
      6. Return the real return value unchanged
    
    Args:
        agent: The agent object to wrap (any object with callable methods)
        name: Name of this agent (used as sender in messages)
        session_id: Optional session ID (overrides thread-local context)
    
    Returns:
        AgentProxy that wraps the agent
    
    Example:
        researcher = wrap(ResearchAgent(), name="researcher")
        result = researcher.run("Find quantum computing breakthroughs")
    """
    return AgentProxy(agent, name, session_id)
