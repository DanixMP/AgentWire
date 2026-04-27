"""Session context manager for grouping agent runs."""

import threading
from contextlib import contextmanager
from typing import Optional
from datetime import datetime

from .models import WireMessage, MessageType
from .emitter import emit_sync, _config


# Thread-local storage for session context
_session_context = threading.local()


def get_current_session() -> str:
    """Get the current session ID from thread-local context."""
    return getattr(_session_context, "session_id", _config.default_session)


def _set_session(session_id: str) -> None:
    """Set the current session ID in thread-local context."""
    _session_context.session_id = session_id


def _get_previous_session() -> Optional[str]:
    """Get the previous session ID (for nested contexts)."""
    return getattr(_session_context, "previous_session_id", None)


def _set_previous_session(session_id: Optional[str]) -> None:
    """Store the previous session ID (for nested contexts)."""
    _session_context.previous_session_id = session_id


@contextmanager
def session(session_id: str, name: Optional[str] = None):
    """
    Context manager for grouping messages into a session.
    
    Sets the active session_id for all emit() calls within the block.
    Emits session_start and session_end SYSTEM messages to the bus.
    Uses threading.local so nested sessions and multi-threaded use work correctly.
    Restores the previous session_id on exit.
    
    Args:
        session_id: Unique identifier for this session
        name: Optional human-readable name for the session
    
    Example:
        with session("blog-post-run-42", name="Blog Post Generation"):
            facts = researcher.run("Find quantum computing breakthroughs")
            post = writer.run(facts)
    """
    # Save the previous session ID
    previous_session = get_current_session()
    _set_previous_session(previous_session)
    
    # Set the new session ID
    _set_session(session_id)
    
    # Emit session start
    start_msg = WireMessage(
        session_id=session_id,
        sender="system",
        receiver="broadcast",
        type=MessageType.SYSTEM,
        content=f"Session started: {name or session_id}",
        metadata={"event": "session_start", "name": name} if name else {"event": "session_start"},
    )
    emit_sync(start_msg)
    
    try:
        yield session_id
    finally:
        # Emit session end
        end_msg = WireMessage(
            session_id=session_id,
            sender="system",
            receiver="broadcast",
            type=MessageType.SYSTEM,
            content=f"Session ended: {name or session_id}",
            metadata={"event": "session_end", "name": name} if name else {"event": "session_end"},
        )
        emit_sync(end_msg)
        
        # Restore the previous session ID
        prev = _get_previous_session()
        if prev:
            _set_session(prev)
        _set_previous_session(None)
