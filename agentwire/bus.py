"""FastAPI message bus server."""

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from typing import List
import json
import logging

from .models import WireMessage, Session, MessageType
from .store import SQLiteStore, MessageStore
from .pricing import calculate_cost

logger = logging.getLogger(__name__)


# Global store instance
store: MessageStore = SQLiteStore()


class ConnectionManager:
    """Manages WebSocket connections and broadcasts messages."""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket, session_id: str | None = None):
        """
        Accept a new WebSocket connection and send recent messages.
        
        Args:
            websocket: The WebSocket connection
            session_id: Optional session ID to send messages for
        """
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")
        
        # Send last 50 messages for the active session
        if session_id:
            try:
                messages = await store.get_messages(session_id)
                recent_messages = messages[-50:] if len(messages) > 50 else messages
                
                for msg in recent_messages:
                    await websocket.send_json({
                        "event": "message",
                        "data": msg.model_dump(mode="json"),
                    })
            except Exception as e:
                logger.warning(f"Failed to send recent messages: {e}")
    
    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection."""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")
    
    async def broadcast(self, event: dict):
        """
        Broadcast an event to all connected clients.
        
        Args:
            event: Event dictionary with 'event' and 'data' keys
        """
        disconnected = []
        
        for connection in self.active_connections:
            try:
                await connection.send_json(event)
            except Exception as e:
                logger.warning(f"Failed to send to client: {e}")
                disconnected.append(connection)
        
        # Clean up disconnected clients
        for connection in disconnected:
            self.disconnect(connection)


# Global connection manager
manager = ConnectionManager()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize store on startup."""
    await store._init_db()
    yield


app = FastAPI(
    title="AgentWire",
    description="Real-time message bus and inspector for multi-agent LLM systems",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS middleware for dashboard development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/api/messages")
async def create_message(msg: WireMessage):
    """
    Ingest a new message, calculate cost if model is known, store it, and broadcast to WebSocket clients.
    """
    # Auto-calculate cost if model is provided
    if msg.model and msg.cost_usd == 0.0:
        msg.cost_usd = calculate_cost(msg.model, msg.tokens_in, msg.tokens_out)
    
    await store.save_message(msg)
    
    # Broadcast to all connected WebSocket clients
    await manager.broadcast({
        "event": "message",
        "data": msg.model_dump(mode="json"),
    })
    
    # Check if this is a session start/end event
    if msg.type == MessageType.SYSTEM:
        if msg.metadata.get("event") == "session_start":
            await manager.broadcast({
                "event": "session_start",
                "data": {
                    "session_id": msg.session_id,
                    "timestamp": msg.timestamp.isoformat(),
                    "name": msg.metadata.get("name"),
                },
            })
        elif msg.metadata.get("event") == "session_end":
            await manager.broadcast({
                "event": "session_end",
                "data": {
                    "session_id": msg.session_id,
                    "timestamp": msg.timestamp.isoformat(),
                    "name": msg.metadata.get("name"),
                },
            })
    
    return {"status": "ok", "id": msg.id}


@app.get("/api/sessions")
async def get_sessions() -> list[Session]:
    """
    Get all sessions with aggregated statistics.
    """
    return await store.get_sessions()


@app.get("/api/sessions/{session_id}")
async def get_session(session_id: str) -> Session:
    """
    Get a single session by ID.
    """
    session = await store.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@app.get("/api/sessions/{session_id}/messages")
async def get_session_messages(session_id: str) -> list[WireMessage]:
    """
    Get all messages for a session, ordered by timestamp.
    """
    return await store.get_messages(session_id)


@app.get("/api/sessions/{session_id}/graph")
async def get_session_graph(session_id: str) -> dict:
    """
    Get graph data (nodes and edges) for a session.
    
    Returns:
        {
            "nodes": [
                {
                    "id": "agent_name",
                    "message_count": 5,
                    "total_tokens": 1000,
                    "dominant_type": "TASK"
                }
            ],
            "edges": [
                {
                    "source": "agent1",
                    "target": "agent2",
                    "count": 3,
                    "dominant_type": "TASK",
                    "total_tokens": 500,
                    "avg_latency_ms": 1500
                }
            ]
        }
    """
    messages = await store.get_messages(session_id)
    
    if not messages:
        return {"nodes": [], "edges": []}
    
    # Build nodes (agents)
    node_stats = {}
    for msg in messages:
        # Track sender stats
        if msg.sender not in node_stats:
            node_stats[msg.sender] = {
                "message_count": 0,
                "total_tokens": 0,
                "types": {},
            }
        node_stats[msg.sender]["message_count"] += 1
        node_stats[msg.sender]["total_tokens"] += msg.tokens_in + msg.tokens_out
        node_stats[msg.sender]["types"][msg.type.value] = \
            node_stats[msg.sender]["types"].get(msg.type.value, 0) + 1
        
        # Track receiver as node (if not system/broadcast/unknown)
        if msg.receiver not in ("system", "broadcast", "unknown"):
            if msg.receiver not in node_stats:
                node_stats[msg.receiver] = {
                    "message_count": 0,
                    "total_tokens": 0,
                    "types": {},
                }
    
    # Build edges (message flows)
    edge_stats = {}
    for msg in messages:
        # Skip system/broadcast/unknown receivers
        if msg.receiver in ("system", "broadcast", "unknown"):
            continue
        
        edge_key = f"{msg.sender}→{msg.receiver}"
        if edge_key not in edge_stats:
            edge_stats[edge_key] = {
                "source": msg.sender,
                "target": msg.receiver,
                "count": 0,
                "types": {},
                "total_tokens": 0,
                "total_latency_ms": 0,
                "latency_count": 0,
            }
        
        edge_stats[edge_key]["count"] += 1
        edge_stats[edge_key]["types"][msg.type.value] = \
            edge_stats[edge_key]["types"].get(msg.type.value, 0) + 1
        edge_stats[edge_key]["total_tokens"] += msg.tokens_in + msg.tokens_out
        
        if msg.latency_ms > 0:
            edge_stats[edge_key]["total_latency_ms"] += msg.latency_ms
            edge_stats[edge_key]["latency_count"] += 1
    
    # Format nodes
    nodes = []
    for agent_id, stats in node_stats.items():
        # Find dominant message type
        dominant_type = max(stats["types"].items(), key=lambda x: x[1])[0] \
            if stats["types"] else "SYSTEM"
        
        nodes.append({
            "id": agent_id,
            "message_count": stats["message_count"],
            "total_tokens": stats["total_tokens"],
            "dominant_type": dominant_type,
        })
    
    # Format edges
    edges = []
    for edge_key, stats in edge_stats.items():
        # Find dominant message type
        dominant_type = max(stats["types"].items(), key=lambda x: x[1])[0] \
            if stats["types"] else "TASK"
        
        # Calculate average latency
        avg_latency_ms = int(stats["total_latency_ms"] / stats["latency_count"]) \
            if stats["latency_count"] > 0 else 0
        
        edges.append({
            "source": stats["source"],
            "target": stats["target"],
            "count": stats["count"],
            "dominant_type": dominant_type,
            "total_tokens": stats["total_tokens"],
            "avg_latency_ms": avg_latency_ms,
        })
    
    return {"nodes": nodes, "edges": edges}


@app.get("/api/stats")
async def get_stats() -> dict:
    """
    Get global statistics: total messages, sessions, tokens, cost.
    """
    return await store.get_stats()


@app.delete("/api/sessions/{session_id}")
async def delete_session(session_id: str):
    """
    Delete a session and all its messages.
    """
    await store.delete_session(session_id)
    return {"status": "ok"}


@app.delete("/api/messages")
async def clear_all():
    """
    Clear all sessions and messages.
    """
    await store.clear()
    return {"status": "ok"}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, session_id: str | None = None):
    """
    WebSocket endpoint for real-time message streaming.
    
    Query params:
        session_id: Optional session ID to receive messages for
    
    Events emitted:
        - message: New message arrived
        - session_start: Session started
        - session_end: Session ended
    """
    await manager.connect(websocket, session_id)
    
    try:
        # Keep connection alive and handle incoming messages (if any)
        while True:
            # Wait for any message from client (ping/pong, etc.)
            data = await websocket.receive_text()
            
            # Echo back for ping/pong
            if data == "ping":
                await websocket.send_text("pong")
    
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)


# Serve dashboard static files
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path

# Get the path to the static directory
static_dir = Path(__file__).parent / "static"

if static_dir.exists():
    # Mount static files
    app.mount("/assets", StaticFiles(directory=static_dir / "assets"), name="assets")
    
    # Serve index.html for root and all other routes (SPA routing)
    @app.get("/{full_path:path}")
    async def serve_dashboard(full_path: str):
        """Serve the dashboard for all non-API routes."""
        # If it's an API route, let FastAPI handle it
        if full_path.startswith("api/") or full_path.startswith("ws"):
            raise HTTPException(status_code=404, detail="Not Found")
        
        # Serve index.html for all other routes (SPA)
        index_file = static_dir / "index.html"
        if index_file.exists():
            return FileResponse(index_file)
        else:
            raise HTTPException(status_code=404, detail="Dashboard not built")
else:
    logger.warning("Dashboard static files not found. Run 'npm run build' in dashboard/")
