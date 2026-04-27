"""Core data models for AgentWire."""

from enum import Enum
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
import uuid


class MessageType(str, Enum):
    """Types of messages that can flow through the wire."""
    TASK = "TASK"  # agent assigns work to another agent
    RESULT = "RESULT"  # agent returns completed work
    ERROR = "ERROR"  # agent reports failure
    TOOL_CALL = "TOOL_CALL"  # agent calls an external tool
    TOOL_RESULT = "TOOL_RESULT"  # tool returns result to agent
    SYSTEM = "SYSTEM"  # orchestration/control messages


class WireMessage(BaseModel):
    """A single message flowing through the agent wire."""
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str  # groups a full run
    parent_id: Optional[str] = None  # reply threading
    
    sender: str  # agent name
    receiver: str  # agent name or "broadcast"
    type: MessageType
    
    content: str  # message body
    metadata: dict = Field(default_factory=dict)  # framework-specific extras
    
    tokens_in: int = 0  # prompt tokens consumed
    tokens_out: int = 0  # completion tokens generated
    model: Optional[str] = None  # e.g. "claude-sonnet-4-6"
    latency_ms: int = 0  # time to generate, milliseconds
    cost_usd: float = 0.0  # auto-computed if model is known
    
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    tags: list[str] = Field(default_factory=list)


class Session(BaseModel):
    """A session groups multiple messages from a single agent run."""
    
    id: str
    name: Optional[str] = None
    started_at: datetime
    ended_at: Optional[datetime] = None
    message_count: int = 0
    total_tokens: int = 0
    total_cost_usd: float = 0.0
    agents: list[str] = Field(default_factory=list)  # agent names seen in this session
