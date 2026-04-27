"""CrewAI integration for AgentWire."""

from typing import Any, Optional
import time

from ..models import WireMessage, MessageType
from ..emitter import emit_sync
from ..session import get_current_session


def wire_crew(crew: Any, session_id: Optional[str] = None) -> None:
    """
    Wire a CrewAI crew to emit WireMessages.
    
    Patches all agents in the crew to emit messages when executing tasks.
    Call this before crew.kickoff().
    
    Args:
        crew: CrewAI Crew instance
        session_id: Optional session ID (uses thread-local context if not provided)
    
    Example:
        from agentwire.integrations.crewai import wire_crew
        
        my_crew = Crew(agents=[...], tasks=[...])
        wire_crew(my_crew, session_id="crew-run-7")
        result = my_crew.kickoff()
    """
    if not hasattr(crew, "agents"):
        raise ValueError("Invalid crew object: missing 'agents' attribute")
    
    def _get_session_id() -> str:
        return session_id or get_current_session()
    
    # Patch each agent's execute_task method
    for agent in crew.agents:
        agent_name = getattr(agent, "name", getattr(agent, "role", "unknown"))
        original_execute = getattr(agent, "execute_task", None)
        
        if not original_execute:
            continue
        
        def make_wrapper(agent_name: str, original_fn):
            """Create a wrapper that preserves the agent name."""
            def wrapped_execute(task: Any, *args, **kwargs):
                # Emit TASK message
                task_desc = str(getattr(task, "description", task))[:500]
                
                task_msg = WireMessage(
                    session_id=_get_session_id(),
                    sender="orchestrator",
                    receiver=agent_name,
                    type=MessageType.TASK,
                    content=task_desc,
                    metadata={
                        "agent": agent_name,
                        "task_type": type(task).__name__,
                    },
                )
                emit_sync(task_msg)
                
                # Execute original method
                start_time = time.time()
                try:
                    result = original_fn(task, *args, **kwargs)
                    latency_ms = int((time.time() - start_time) * 1000)
                    
                    # Emit RESULT message
                    result_msg = WireMessage(
                        session_id=_get_session_id(),
                        sender=agent_name,
                        receiver="orchestrator",
                        type=MessageType.RESULT,
                        content=str(result)[:500],
                        latency_ms=latency_ms,
                        metadata={
                            "agent": agent_name,
                            "success": True,
                        },
                    )
                    emit_sync(result_msg)
                    
                    return result
                    
                except Exception as e:
                    latency_ms = int((time.time() - start_time) * 1000)
                    
                    # Emit ERROR message
                    error_msg = WireMessage(
                        session_id=_get_session_id(),
                        sender=agent_name,
                        receiver="orchestrator",
                        type=MessageType.ERROR,
                        content=f"{type(e).__name__}: {str(e)}"[:500],
                        latency_ms=latency_ms,
                        metadata={
                            "agent": agent_name,
                            "error_type": type(e).__name__,
                        },
                    )
                    emit_sync(error_msg)
                    
                    raise
            
            return wrapped_execute
        
        # Replace the method
        setattr(agent, "execute_task", make_wrapper(agent_name, original_execute))


def wire_crewai_agent(agent: Any, name: Optional[str] = None, session_id: Optional[str] = None) -> None:
    """
    Wire a single CrewAI agent to emit WireMessages.
    
    Args:
        agent: CrewAI Agent instance
        name: Optional name (uses agent.name or agent.role if not provided)
        session_id: Optional session ID
    
    Example:
        from agentwire.integrations.crewai import wire_crewai_agent
        
        wire_crewai_agent(my_agent, name="researcher", session_id="run-1")
    """
    agent_name = name or getattr(agent, "name", getattr(agent, "role", "unknown"))
    
    def _get_session_id() -> str:
        return session_id or get_current_session()
    
    original_execute = getattr(agent, "execute_task", None)
    if not original_execute:
        raise ValueError(f"Agent {agent} does not have execute_task method")
    
    def wrapped_execute(task: Any, *args, **kwargs):
        # Emit TASK message
        task_desc = str(getattr(task, "description", task))[:500]
        
        task_msg = WireMessage(
            session_id=_get_session_id(),
            sender="orchestrator",
            receiver=agent_name,
            type=MessageType.TASK,
            content=task_desc,
            metadata={
                "agent": agent_name,
                "task_type": type(task).__name__,
            },
        )
        emit_sync(task_msg)
        
        # Execute original method
        start_time = time.time()
        try:
            result = original_execute(task, *args, **kwargs)
            latency_ms = int((time.time() - start_time) * 1000)
            
            # Emit RESULT message
            result_msg = WireMessage(
                session_id=_get_session_id(),
                sender=agent_name,
                receiver="orchestrator",
                type=MessageType.RESULT,
                content=str(result)[:500],
                latency_ms=latency_ms,
                metadata={
                    "agent": agent_name,
                    "success": True,
                },
            )
            emit_sync(result_msg)
            
            return result
            
        except Exception as e:
            latency_ms = int((time.time() - start_time) * 1000)
            
            # Emit ERROR message
            error_msg = WireMessage(
                session_id=_get_session_id(),
                sender=agent_name,
                receiver="orchestrator",
                type=MessageType.ERROR,
                content=f"{type(e).__name__}: {str(e)}"[:500],
                latency_ms=latency_ms,
                metadata={
                    "agent": agent_name,
                    "error_type": type(e).__name__,
                },
            )
            emit_sync(error_msg)
            
            raise
    
    setattr(agent, "execute_task", wrapped_execute)
