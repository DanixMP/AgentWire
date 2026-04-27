"""AgentWire - Real-time message bus and inspector for multi-agent LLM systems."""

__version__ = "0.1.0"

from .emitter import emit, configure
from .wrapper import wrap
from .session import session
from .models import WireMessage, MessageType

__all__ = ["emit", "configure", "wrap", "session", "WireMessage", "MessageType"]
