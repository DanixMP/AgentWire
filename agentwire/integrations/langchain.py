"""LangChain integration for AgentWire."""

from typing import Any, Dict, List, Optional
from uuid import UUID

try:
    from langchain.callbacks.base import BaseCallbackHandler
    from langchain.schema import AgentAction, AgentFinish, LLMResult
except ImportError:
    raise ImportError(
        "LangChain is not installed. Install with: pip install agentwire[langchain]"
    )

from ..models import WireMessage, MessageType
from ..emitter import emit_sync
from ..session import get_current_session


class AgentWireCallback(BaseCallbackHandler):
    """
    LangChain callback handler that emits WireMessages to AgentWire.
    
    Usage:
        from agentwire.integrations.langchain import AgentWireCallback
        
        agent = initialize_agent(
            tools,
            llm,
            callbacks=[AgentWireCallback(agent_name="researcher", session_id="run-1")]
        )
    """
    
    def __init__(
        self,
        agent_name: str,
        session_id: Optional[str] = None,
    ):
        """
        Initialize the callback handler.
        
        Args:
            agent_name: Name of the agent (used as sender in messages)
            session_id: Optional session ID (uses thread-local context if not provided)
        """
        super().__init__()
        self.agent_name = agent_name
        self.session_id = session_id
        self._run_map: Dict[UUID, Dict[str, Any]] = {}
    
    def _get_session_id(self) -> str:
        """Get session ID from explicit value or thread-local context."""
        return self.session_id or get_current_session()
    
    def on_llm_start(
        self,
        serialized: Dict[str, Any],
        prompts: List[str],
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        **kwargs: Any,
    ) -> None:
        """Emit TASK message when LLM starts."""
        self._run_map[run_id] = {
            "type": "llm",
            "start_time": kwargs.get("start_time"),
        }
        
        msg = WireMessage(
            session_id=self._get_session_id(),
            sender=self.agent_name,
            receiver="llm",
            type=MessageType.TASK,
            content=prompts[0][:500] if prompts else "LLM call",
            metadata={
                "run_id": str(run_id),
                "model": serialized.get("name", "unknown"),
                "prompts_count": len(prompts),
            },
        )
        emit_sync(msg)
    
    def on_llm_end(
        self,
        response: LLMResult,
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        **kwargs: Any,
    ) -> None:
        """Emit RESULT message when LLM completes."""
        run_info = self._run_map.pop(run_id, {})
        
        # Extract token usage
        tokens_in = 0
        tokens_out = 0
        if response.llm_output:
            token_usage = response.llm_output.get("token_usage", {})
            tokens_in = token_usage.get("prompt_tokens", 0)
            tokens_out = token_usage.get("completion_tokens", 0)
        
        # Get first generation text
        content = ""
        if response.generations and response.generations[0]:
            content = response.generations[0][0].text[:500]
        
        msg = WireMessage(
            session_id=self._get_session_id(),
            sender="llm",
            receiver=self.agent_name,
            type=MessageType.RESULT,
            content=content,
            tokens_in=tokens_in,
            tokens_out=tokens_out,
            metadata={
                "run_id": str(run_id),
                "generations_count": len(response.generations),
            },
        )
        emit_sync(msg)
    
    def on_tool_start(
        self,
        serialized: Dict[str, Any],
        input_str: str,
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        **kwargs: Any,
    ) -> None:
        """Emit TOOL_CALL message when tool starts."""
        self._run_map[run_id] = {
            "type": "tool",
            "tool_name": serialized.get("name", "unknown"),
        }
        
        msg = WireMessage(
            session_id=self._get_session_id(),
            sender=self.agent_name,
            receiver=serialized.get("name", "tool"),
            type=MessageType.TOOL_CALL,
            content=input_str[:500],
            metadata={
                "run_id": str(run_id),
                "tool": serialized.get("name", "unknown"),
            },
        )
        emit_sync(msg)
    
    def on_tool_end(
        self,
        output: str,
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        **kwargs: Any,
    ) -> None:
        """Emit TOOL_RESULT message when tool completes."""
        run_info = self._run_map.pop(run_id, {})
        tool_name = run_info.get("tool_name", "tool")
        
        msg = WireMessage(
            session_id=self._get_session_id(),
            sender=tool_name,
            receiver=self.agent_name,
            type=MessageType.TOOL_RESULT,
            content=str(output)[:500],
            metadata={
                "run_id": str(run_id),
                "tool": tool_name,
            },
        )
        emit_sync(msg)
    
    def on_agent_action(
        self,
        action: AgentAction,
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        **kwargs: Any,
    ) -> None:
        """Called when agent takes an action."""
        # Already handled by on_tool_start
        pass
    
    def on_agent_finish(
        self,
        finish: AgentFinish,
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        **kwargs: Any,
    ) -> None:
        """Emit RESULT message when agent finishes."""
        msg = WireMessage(
            session_id=self._get_session_id(),
            sender=self.agent_name,
            receiver="user",
            type=MessageType.RESULT,
            content=str(finish.return_values.get("output", ""))[:500],
            metadata={
                "run_id": str(run_id),
                "finish_reason": finish.log,
            },
        )
        emit_sync(msg)
    
    def on_chain_error(
        self,
        error: Exception,
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        **kwargs: Any,
    ) -> None:
        """Emit ERROR message when chain fails."""
        msg = WireMessage(
            session_id=self._get_session_id(),
            sender=self.agent_name,
            receiver="user",
            type=MessageType.ERROR,
            content=f"{type(error).__name__}: {str(error)}"[:500],
            metadata={
                "run_id": str(run_id),
                "error_type": type(error).__name__,
            },
        )
        emit_sync(msg)
