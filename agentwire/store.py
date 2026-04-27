"""Database abstraction layer for message storage."""

from abc import ABC, abstractmethod
from typing import Optional
import aiosqlite
import json
from datetime import datetime

from .models import WireMessage, Session, MessageType


class MessageStore(ABC):
    """Abstract base class for message storage backends."""
    
    @abstractmethod
    async def save_message(self, msg: WireMessage) -> None:
        """Save a message to the store."""
        pass
    
    @abstractmethod
    async def get_messages(self, session_id: str) -> list[WireMessage]:
        """Get all messages for a session, ordered by timestamp."""
        pass
    
    @abstractmethod
    async def get_sessions(self) -> list[Session]:
        """Get all sessions, ordered by started_at descending."""
        pass
    
    @abstractmethod
    async def get_session(self, session_id: str) -> Optional[Session]:
        """Get a single session by ID."""
        pass
    
    @abstractmethod
    async def get_stats(self) -> dict:
        """Get global statistics."""
        pass
    
    @abstractmethod
    async def delete_session(self, session_id: str) -> None:
        """Delete a session and all its messages."""
        pass
    
    @abstractmethod
    async def clear(self) -> None:
        """Delete all sessions and messages."""
        pass


class SQLiteStore(MessageStore):
    """SQLite-based message store for local development."""
    
    def __init__(self, db_path: str = "agentwire.db"):
        self.db_path = db_path
    
    async def _init_db(self):
        """Initialize database schema."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id          TEXT PRIMARY KEY,
                    session_id  TEXT NOT NULL,
                    parent_id   TEXT,
                    sender      TEXT NOT NULL,
                    receiver    TEXT NOT NULL,
                    type        TEXT NOT NULL,
                    content     TEXT NOT NULL,
                    metadata    TEXT DEFAULT '{}',
                    tokens_in   INTEGER DEFAULT 0,
                    tokens_out  INTEGER DEFAULT 0,
                    model       TEXT,
                    latency_ms  INTEGER DEFAULT 0,
                    cost_usd    REAL DEFAULT 0.0,
                    timestamp   TEXT NOT NULL,
                    tags        TEXT DEFAULT '[]'
                )
            """)
            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_session ON messages(session_id)
            """)
            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_timestamp ON messages(timestamp)
            """)
            await db.commit()
    
    async def save_message(self, msg: WireMessage) -> None:
        """Save a message to SQLite."""
        # Ensure DB is initialized
        await self._init_db()
        
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO messages (
                    id, session_id, parent_id, sender, receiver, type,
                    content, metadata, tokens_in, tokens_out, model,
                    latency_ms, cost_usd, timestamp, tags
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                msg.id,
                msg.session_id,
                msg.parent_id,
                msg.sender,
                msg.receiver,
                msg.type.value,
                msg.content,
                json.dumps(msg.metadata),
                msg.tokens_in,
                msg.tokens_out,
                msg.model,
                msg.latency_ms,
                msg.cost_usd,
                msg.timestamp.isoformat(),
                json.dumps(msg.tags),
            ))
            await db.commit()
    
    async def get_messages(self, session_id: str) -> list[WireMessage]:
        """Get all messages for a session."""
        await self._init_db()
        
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM messages WHERE session_id = ? ORDER BY timestamp ASC",
                (session_id,)
            ) as cursor:
                rows = await cursor.fetchall()
                return [self._row_to_message(row) for row in rows]
    
    async def get_sessions(self) -> list[Session]:
        """Get all sessions with aggregated stats."""
        await self._init_db()
        
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("""
                SELECT 
                    session_id,
                    MIN(timestamp) as started_at,
                    MAX(timestamp) as ended_at,
                    COUNT(*) as message_count,
                    SUM(tokens_in + tokens_out) as total_tokens,
                    SUM(cost_usd) as total_cost_usd,
                    GROUP_CONCAT(DISTINCT sender) as agents
                FROM messages
                GROUP BY session_id
                ORDER BY started_at DESC
            """) as cursor:
                rows = await cursor.fetchall()
                sessions = []
                for row in rows:
                    agents = row["agents"].split(",") if row["agents"] else []
                    sessions.append(Session(
                        id=row["session_id"],
                        started_at=datetime.fromisoformat(row["started_at"]),
                        ended_at=datetime.fromisoformat(row["ended_at"]) if row["ended_at"] else None,
                        message_count=row["message_count"],
                        total_tokens=row["total_tokens"] or 0,
                        total_cost_usd=row["total_cost_usd"] or 0.0,
                        agents=agents,
                    ))
                return sessions
    
    async def get_session(self, session_id: str) -> Optional[Session]:
        """Get a single session by ID."""
        sessions = await self.get_sessions()
        for session in sessions:
            if session.id == session_id:
                return session
        return None
    
    async def get_stats(self) -> dict:
        """Get global statistics."""
        await self._init_db()
        
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("""
                SELECT 
                    COUNT(*) as total_messages,
                    COUNT(DISTINCT session_id) as total_sessions,
                    SUM(tokens_in + tokens_out) as total_tokens,
                    SUM(cost_usd) as total_cost_usd
                FROM messages
            """) as cursor:
                row = await cursor.fetchone()
                return {
                    "total_messages": row["total_messages"] or 0,
                    "total_sessions": row["total_sessions"] or 0,
                    "total_tokens": row["total_tokens"] or 0,
                    "total_cost_usd": row["total_cost_usd"] or 0.0,
                }
    
    async def delete_session(self, session_id: str) -> None:
        """Delete a session and all its messages."""
        await self._init_db()
        
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))
            await db.commit()
    
    async def clear(self) -> None:
        """Delete all sessions and messages."""
        await self._init_db()
        
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("DELETE FROM messages")
            await db.commit()
    
    def _row_to_message(self, row: aiosqlite.Row) -> WireMessage:
        """Convert a database row to a WireMessage."""
        return WireMessage(
            id=row["id"],
            session_id=row["session_id"],
            parent_id=row["parent_id"],
            sender=row["sender"],
            receiver=row["receiver"],
            type=MessageType(row["type"]),
            content=row["content"],
            metadata=json.loads(row["metadata"]),
            tokens_in=row["tokens_in"],
            tokens_out=row["tokens_out"],
            model=row["model"],
            latency_ms=row["latency_ms"],
            cost_usd=row["cost_usd"],
            timestamp=datetime.fromisoformat(row["timestamp"]),
            tags=json.loads(row["tags"]),
        )
