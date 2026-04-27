"""Async non-blocking message emitter (SDK side)."""

import os
import asyncio
import threading
import logging
from typing import Optional
import httpx

from .models import WireMessage

logger = logging.getLogger(__name__)


class Config:
    """Global configuration singleton."""
    
    def __init__(self):
        self.bus_url: str = "http://localhost:7433"
        self.default_session: str = "default"
        self.enabled: bool = True
        self._lock = threading.Lock()
    
    def update(
        self,
        bus_url: Optional[str] = None,
        default_session: Optional[str] = None,
        enabled: Optional[bool] = None,
    ):
        """Thread-safe config update."""
        with self._lock:
            if bus_url is not None:
                self.bus_url = bus_url
            if default_session is not None:
                self.default_session = default_session
            if enabled is not None:
                self.enabled = enabled


# Global config instance
_config = Config()


def configure(
    bus_url: Optional[str] = None,
    default_session: Optional[str] = None,
    enabled: Optional[bool] = None,
):
    """
    Configure AgentWire SDK globally.
    
    Reads from environment variables first, then kwargs:
    - AGENTWIRE_URL
    - AGENTWIRE_SESSION
    - AGENTWIRE_ENABLED
    
    Args:
        bus_url: URL of the AgentWire bus server
        default_session: Default session ID if no context manager active
        enabled: Whether to enable message emission (False = silent disable)
    """
    # Read from env vars first
    env_url = os.getenv("AGENTWIRE_URL")
    env_session = os.getenv("AGENTWIRE_SESSION")
    env_enabled = os.getenv("AGENTWIRE_ENABLED")
    
    final_url = bus_url or env_url
    final_session = default_session or env_session
    final_enabled = enabled if enabled is not None else (
        env_enabled.lower() in ("true", "1", "yes") if env_enabled else None
    )
    
    _config.update(
        bus_url=final_url,
        default_session=final_session,
        enabled=final_enabled,
    )


async def _emit_async(msg: WireMessage) -> None:
    """
    Internal async emit implementation.
    Never raises — logs warnings on failure.
    """
    if not _config.enabled:
        return
    
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(
                f"{_config.bus_url}/api/messages",
                json=msg.model_dump(mode="json"),
            )
            response.raise_for_status()
    except httpx.HTTPError as e:
        logger.warning(f"Failed to emit message to AgentWire: {e}")
    except Exception as e:
        logger.warning(f"Unexpected error emitting message: {e}")


def _emit_sync(msg: WireMessage) -> None:
    """
    Sync wrapper that runs emit in a background thread with its own event loop.
    Used when emit() is called from a sync context.
    """
    def run_in_thread():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(_emit_async(msg))
        finally:
            loop.close()
    
    thread = threading.Thread(target=run_in_thread, daemon=True)
    thread.start()


async def emit(msg: WireMessage) -> None:
    """
    Fire-and-forget message emission to the AgentWire bus.
    
    This function is non-blocking and never raises exceptions.
    If called from an async context, it creates a background task.
    If called from a sync context, it uses a background thread.
    
    Args:
        msg: WireMessage to emit
    """
    if not _config.enabled:
        return
    
    try:
        # Try to get the current event loop
        loop = asyncio.get_running_loop()
        # We're in an async context — create a background task
        loop.create_task(_emit_async(msg))
    except RuntimeError:
        # No event loop running — we're in a sync context
        _emit_sync(msg)


def emit_sync(msg: WireMessage) -> None:
    """
    Synchronous version of emit for use in pure sync code.
    Uses a background thread with its own event loop.
    
    Args:
        msg: WireMessage to emit
    """
    _emit_sync(msg)
