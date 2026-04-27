# AgentWire — Design Document

> Feed this file to Claude Code at the start of every session:
> `claude --context Design-Agentwire.md` or reference inline with `@Design-Agentwire.md`
> This document is the single source of truth. Claude Code should not make architectural
> decisions not covered here — it should ask first.

---

## What this project is

A framework-agnostic, open-source message bus and real-time inspector for multi-agent LLM
systems. AgentWire sits between your agents, captures every inter-agent message, and surfaces
them in a live dashboard — feed, graph view, cost tracker, and session replay.

The problem it solves: multi-agent systems are opaque. When a 5-agent pipeline produces a
bad result, you have no way to see which agent said what to whom and why things went wrong.
AgentWire makes the invisible visible.

**The pitch in one line:** `pip install agentwire` → `agentwire.wrap(your_agent)` →
open localhost:7433 → see everything.

---

## What makes it different from existing tools

LangSmith, Langfuse, Phoenix, and AgentOps all exist. AgentWire is NOT another one of these.
The key differences:

- **Message bus as first-class abstraction.** Existing tools trace LLM calls (inputs/outputs
  to the model). AgentWire traces inter-agent messages (what agents say to each other). These
  are different levels of abstraction.
- **Framework-agnostic by design.** One unified view across LangChain, AutoGen, CrewAI, and
  raw API calls in the same session.
- **Session replay.** Step through a past run message-by-message with graph animation. No
  existing open-source tool does this.
- **Zero infrastructure to start.** `pip install agentwire && agentwire start` — SQLite,
  no Docker, no Postgres, no signup required for local dev.

---

## Repository structure

```
agentwire/
├── pyproject.toml               # Python package config, entry points
├── README.md
├── Design-Agentwire.md          # this file
├── agentwire/                   # Python package
│   ├── __init__.py              # public API: wrap(), emit(), session()
│   ├── models.py                # WireMessage, MessageType, Session Pydantic models
│   ├── bus.py                   # FastAPI app, all REST + WebSocket endpoints
│   ├── store.py                 # DB abstraction: SQLite (dev) + Postgres (prod)
│   ├── emitter.py               # async non-blocking message emitter (SDK side)
│   ├── wrapper.py               # agentwire.wrap() — agent instrumentation
│   ├── session.py               # context manager for session grouping
│   ├── cli.py                   # `agentwire start`, `agentwire docker up`, `agentwire clear`
│   ├── pricing.py               # model pricing table + cost calculation
│   └── integrations/
│       ├── langchain.py         # LangChain callback handler
│       ├── autogen.py           # AutoGen message hook
│       └── crewai.py            # CrewAI wrapper
├── dashboard/                   # React frontend
│   ├── package.json
│   ├── vite.config.ts
│   └── src/
│       ├── main.tsx
│       ├── App.tsx
│       ├── components/
│       │   ├── Sidebar.tsx      # session + agent list
│       │   ├── MessageFeed.tsx  # real-time feed
│       │   ├── GraphView.tsx    # D3 force graph
│       │   ├── ReplayBar.tsx    # session replay controls
│       │   └── StatsBar.tsx     # message count, tokens, cost
│       ├── hooks/
│       │   ├── useWebSocket.ts  # WebSocket connection + message stream
│       │   └── useSession.ts    # session state management
│       └── types.ts             # TypeScript types matching Python models
├── examples/
│   ├── langchain_research/      # 3-agent research pipeline
│   ├── autogen_coding_team/     # orchestrator + coder + reviewer
│   └── raw_api_pipeline/        # pure Anthropic API, no framework
├── tests/
│   ├── test_models.py
│   ├── test_bus.py
│   ├── test_store.py
│   ├── test_emitter.py
│   └── test_integrations.py
└── docs/
    ├── mkdocs.yml
    └── docs/
        ├── index.md
        ├── quickstart.md
        ├── api-reference.md
        └── integrations/
```

---

## Core data model (`agentwire/models.py`)

This is the contract. Every other component derives from it. Do not change field names without
updating all consumers.

```python
from enum import Enum
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
import uuid

class MessageType(str, Enum):
    TASK        = "TASK"         # agent assigns work to another agent
    RESULT      = "RESULT"       # agent returns completed work
    ERROR       = "ERROR"        # agent reports failure
    TOOL_CALL   = "TOOL_CALL"    # agent calls an external tool
    TOOL_RESULT = "TOOL_RESULT"  # tool returns result to agent
    SYSTEM      = "SYSTEM"       # orchestration/control messages

class WireMessage(BaseModel):
    id:          str      = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id:  str                          # groups a full run
    parent_id:   Optional[str] = None         # reply threading

    sender:      str                          # agent name
    receiver:    str                          # agent name or "broadcast"
    type:        MessageType

    content:     str                          # message body
    metadata:    dict = Field(default={})     # framework-specific extras

    tokens_in:   int = 0                      # prompt tokens consumed
    tokens_out:  int = 0                      # completion tokens generated
    model:       Optional[str] = None         # e.g. "claude-sonnet-4-6"
    latency_ms:  int = 0                      # time to generate, milliseconds
    cost_usd:    float = 0.0                  # auto-computed if model is known

    timestamp:   datetime = Field(default_factory=datetime.utcnow)
    tags:        list[str] = Field(default=[])

class Session(BaseModel):
    id:             str
    name:           Optional[str] = None
    started_at:     datetime
    ended_at:       Optional[datetime] = None
    message_count:  int = 0
    total_tokens:   int = 0
    total_cost_usd: float = 0.0
    agents:         list[str] = []            # agent names seen in this session
```

---

## Bus server (`agentwire/bus.py`)

FastAPI application. Serves both the REST API and the built React dashboard as static files.
The dashboard is built into `agentwire/static/` during `pip install` (via a build hook).

### REST endpoints

```
POST   /api/messages                   → ingest WireMessage, store, broadcast to WS clients
GET    /api/sessions                   → list Session[]
GET    /api/sessions/{id}              → get one Session
GET    /api/sessions/{id}/messages     → get WireMessage[] for a session (ordered by timestamp)
GET    /api/sessions/{id}/graph        → { nodes: AgentNode[], edges: MessageEdge[] }
GET    /api/agents                     → agent names seen + per-agent stats
GET    /api/stats                      → global stats (total messages, tokens, cost)
DELETE /api/sessions/{id}              → delete session and its messages
DELETE /api/messages                   → clear all data

GET    /                               → serve dashboard (React build)
GET    /{path}                         → catch-all → serve dashboard (SPA routing)
```

### Graph endpoint response shape

The `/api/sessions/{id}/graph` response feeds directly into D3. Format:

```python
{
  "nodes": [
    { "id": "orchestrator", "message_count": 4, "total_tokens": 2841 },
    { "id": "researcher",   "message_count": 5, "total_tokens": 8104 },
  ],
  "edges": [
    {
      "source": "orchestrator", "target": "researcher",
      "count": 3, "dominant_type": "TASK",
      "total_tokens": 4200, "avg_latency_ms": 2100
    },
  ]
}
```

### WebSocket `/ws`

Single broadcast channel. All connected dashboard clients receive every new event.
Event types emitted:

```python
# New message arrived
{ "event": "message", "data": WireMessage.model_dump() }

# Session started (first message with a new session_id)
{ "event": "session_start", "data": { "session_id": "...", "timestamp": "..." } }

# Session ended (explicit signal from SDK)
{ "event": "session_end", "data": { "session_id": "...", "timestamp": "..." } }
```

ConnectionManager (in bus.py) maintains `List[WebSocket]`. On connect: add to list, send
last 50 messages for the active session. On disconnect: remove from list. On new message:
broadcast to all connected clients.

---

## Storage (`agentwire/store.py`)

Abstract base class `MessageStore` with two implementations:
`SQLiteStore` (default, file-based) and `PostgresStore` (via asyncpg).

```python
class MessageStore(ABC):
    async def save_message(self, msg: WireMessage) -> None: ...
    async def get_messages(self, session_id: str) -> list[WireMessage]: ...
    async def get_sessions(self) -> list[Session]: ...
    async def get_session(self, session_id: str) -> Session | None: ...
    async def get_stats(self) -> dict: ...
    async def delete_session(self, session_id: str) -> None: ...
    async def clear(self) -> None: ...
```

SQLite schema:

```sql
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
);

CREATE INDEX IF NOT EXISTS idx_session   ON messages(session_id);
CREATE INDEX IF NOT EXISTS idx_timestamp ON messages(timestamp);
```

---

## Pricing (`agentwire/pricing.py`)

Auto-calculates `cost_usd` when a message with a known `model` is ingested.

```python
PRICING: dict[str, dict[str, float]] = {
    "claude-opus-4-6":    {"input": 0.000015,   "output": 0.000075},
    "claude-sonnet-4-6":  {"input": 0.000003,   "output": 0.000015},
    "claude-haiku-4-5":   {"input": 0.0000008,  "output": 0.000004},
    "gpt-4o":             {"input": 0.0000025,  "output": 0.00001},
    "gpt-4o-mini":        {"input": 0.00000015, "output": 0.0000006},
    "gemini-1.5-pro":     {"input": 0.00000125, "output": 0.000005},
}

def calculate_cost(model: str, tokens_in: int, tokens_out: int) -> float:
    if model not in PRICING:
        return 0.0
    p = PRICING[model]
    return round(tokens_in * p["input"] + tokens_out * p["output"], 6)
```

`calculate_cost()` is called automatically inside `POST /api/messages` before storing,
if `msg.model` is present and in the table.

---

## Python SDK (`agentwire/__init__.py` + supporting modules)

The public API surface. Keep it minimal and stable.

```python
# agentwire/__init__.py
from .emitter import emit, configure
from .wrapper import wrap
from .session import session
from .models  import WireMessage, MessageType

__all__ = ["emit", "configure", "wrap", "session", "WireMessage", "MessageType"]
```

### `configure()` — global config

```python
configure(
    bus_url="http://localhost:7433",  # where to POST messages
    default_session="my-run",         # fallback session_id if no context manager active
    enabled=True,                     # False = disable all emission silently
)
```

Reads from env vars first: `AGENTWIRE_URL`, `AGENTWIRE_SESSION`, `AGENTWIRE_ENABLED`.
Config is a module-level singleton. Thread-safe via a threading.Lock.

### `emit()` — fire and forget

```python
async def emit(msg: WireMessage) -> None:
    """Non-blocking HTTP POST to /api/messages. Never raises — logs warnings only."""
```

Uses `asyncio.create_task()` internally. If called from a sync context, falls back to a
background thread with its own event loop. The caller never waits for the HTTP request
to complete — zero performance impact on agent code.

### `wrap()` — instrument any agent

```python
def wrap(agent: Any, *, name: str, session_id: str | None = None) -> Any:
    """
    Returns a proxy object that behaves identically to `agent` but intercepts
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
    """
```

The proxy uses `__getattr__` to forward all attribute access to the wrapped agent.
Only the above method names are intercepted — everything else passes through untouched.

### `session()` — context manager

```python
@contextmanager
def session(session_id: str, name: str | None = None):
    """
    Sets the active session_id for all emit() calls within the block.
    Emits session_start and session_end SYSTEM messages to the bus.
    Uses threading.local so nested sessions and multi-threaded use work correctly.
    Restores the previous session_id on exit.
    """
```

Usage:
```python
import agentwire as aw

aw.configure(bus_url="http://localhost:7433")

researcher = aw.wrap(ResearchAgent(), name="researcher")
writer     = aw.wrap(WriterAgent(),   name="writer")

with aw.session("blog-post-run-42"):
    facts = researcher.run("Find recent breakthroughs in quantum computing")
    post  = writer.run(facts)
```

---

## Framework integrations (`agentwire/integrations/`)

### LangChain (`langchain.py`)

```python
from langchain.callbacks.base import BaseCallbackHandler

class AgentWireCallback(BaseCallbackHandler):
    """
    Hooks: on_llm_start, on_llm_end, on_tool_start, on_tool_end,
           on_agent_action, on_agent_finish, on_chain_error

    LangChain event → WireMessage type mapping:
      on_llm_start      → TASK   (sender=agent_name, receiver="llm")
      on_llm_end        → RESULT (sender="llm", receiver=agent_name)
      on_tool_start     → TOOL_CALL
      on_tool_end       → TOOL_RESULT
      on_agent_finish   → RESULT
      on_chain_error    → ERROR
    """
```

Usage:
```python
from agentwire.integrations.langchain import AgentWireCallback

agent = initialize_agent(
    tools, llm,
    callbacks=[AgentWireCallback(agent_name="researcher", session_id="run-1")]
)
```

### AutoGen (`autogen.py`)

```python
class AgentWireHook:
    """
    Registers as a process_message_before_send / process_message_before_receive hook.
    Emits a WireMessage for every outgoing and incoming message.
    """

# Usage:
hook = AgentWireHook(name="orchestrator", session_id="run-1")
agent.register_hook("process_message_before_send",    hook.on_send)
agent.register_hook("process_message_before_receive", hook.on_receive)
```

### CrewAI (`crewai.py`)

```python
def wire_crew(crew, session_id: str) -> None:
    """
    Patches all agents in a CrewAI crew to emit WireMessages.
    Wraps each agent's execute_task method.
    Call before crew.kickoff().
    """

# Usage:
wire_crew(my_crew, session_id="crew-run-7")
result = my_crew.kickoff()
```

---

## CLI (`agentwire/cli.py`)

Built with Typer. Registered as the `agentwire` command in pyproject.toml.

```
agentwire start              # start bus server on localhost:7433
  --port 7433                # custom port
  --db sqlite:///aw.db       # custom DB path or postgres:// URL
  --no-dashboard             # API-only mode, no static file serving

agentwire stop               # graceful shutdown via stored PID file

agentwire docker up          # write docker-compose.yml → docker compose up -d
agentwire docker down        # docker compose down

agentwire clear              # delete all sessions and messages
agentwire clear --session X  # delete one session by ID

agentwire status             # print: server URL, DB path, message count, session count
```

---

## Dashboard (`dashboard/src/`)

React 18 + Vite + TypeScript. Tailwind CSS for styling. D3 for the topology graph.
Served as static files embedded in the FastAPI server. Not a separate process.

### Component responsibilities

**`App.tsx`** — root component. Manages global state: active session ID, selected agent
filter, replay mode on/off, replay index, replay speed. Renders Sidebar + main area with
tab switcher (Feed | Graph).

**`Sidebar.tsx`** — fixed 220px left panel.
- Sessions list: click to switch active session. Shows message count per session.
- Agents list: click to filter feed to one agent.
- "Clear all" button at bottom.

**`StatsBar.tsx`** — three metric cards at top of main area:
total messages, total tokens, total cost (USD). Updates on every incoming WireMessage.

**`MessageFeed.tsx`** — scrolling chronological list of WireMessages, newest at bottom.
Each row: `sender → receiver` label, type badge (color-coded), timestamp, token count,
latency in ms, first 200 chars of content. Full content shown on click (expand in-place).
Auto-scrolls to bottom unless the user has scrolled up — in that case shows a
"↓ N new messages" pill that jumps to bottom on click.

Message type color system (apply consistently in feed AND graph):
```
TASK        → teal   #5DCAA5
RESULT      → purple #AFA9EC
ERROR       → red    #F09595
TOOL_CALL   → amber  #EF9F27
TOOL_RESULT → amber  #B87C14  (dimmer)
SYSTEM      → gray   #888888
```

**`GraphView.tsx`** — D3 force-directed graph. Tab-switched with MessageFeed.
- Nodes = agents. Circle radius proportional to message_count (min 20px, max 50px).
  Color: dominant MessageType sent from that agent (use color system above).
- Edges = message flows. Stroke width proportional to count (min 1px, max 6px).
  Color: dominant MessageType on that edge.
- Node label: agent name below circle.
- Edge tooltip on hover: message count + dominant type.
- Click node: calls onFilterAgent(agentName) prop → MessageFeed filters.
- Click edge: calls onFilterPair(sender, receiver) prop → MessageFeed filters.
- Live updates: use stable simulation ref. Call simulation.nodes() and
  simulation.force("link").links() to update in-place without restarting simulation.
- Replay mode: only renders nodes/edges that have appeared up to replayIndex.
  Current message's edge pulses via a CSS keyframe animation.

**`ReplayBar.tsx`** — fixed bar at bottom, only visible when replay mode active.
Controls: ◀ first, ‹ prev, ▶/⏸ play/pause, › next, ▶▶ last, speed selector (0.5× 1× 2× 5× 10×),
timeline `<input type="range">` scrubber.
Auto-play uses setInterval at 1000/speed ms per step. Clears on pause/unmount/end.

**`useWebSocket.ts`** — manages the `/ws` connection.
- Auto-reconnects with exponential backoff: 500ms → 1s → 2s → 4s → 8s (cap).
- On first connect: fetches last 50 messages for active session via REST.
- Exposes: `messages: WireMessage[]`, `isConnected: boolean`, `lastError: string | null`.

---

## Configuration file (`agentwire.toml`)

Optional, placed in project root. All fields have defaults.

```toml
[server]
host      = "0.0.0.0"
port      = 7433
db        = "sqlite:///agentwire.db"
log_level = "info"

[dashboard]
enabled = true

[retention]
max_messages_per_session = 10000
max_sessions             = 500

[pricing]
# Extend or override the built-in pricing table
"my-custom-model" = { input = 0.000002, output = 0.000008 }
```

---

## pyproject.toml — key sections

```toml
[project]
name            = "agentwire"
version         = "0.1.0"
description     = "Real-time message bus and inspector for multi-agent LLM systems"
readme          = "README.md"
requires-python = ">=3.10"
license         = { text = "MIT" }
dependencies = [
    "fastapi>=0.110",
    "uvicorn[standard]>=0.27",
    "pydantic>=2.0",
    "aiosqlite>=0.19",
    "httpx>=0.27",
    "typer>=0.12",
    "rich>=13",
    "tomli>=2.0",
]

[project.optional-dependencies]
postgres  = ["asyncpg>=0.29"]
langchain = ["langchain>=0.2"]
autogen   = ["pyautogen>=0.2"]
crewai    = ["crewai>=0.28"]
all       = ["agentwire[postgres,langchain,autogen,crewai]"]

[project.scripts]
agentwire = "agentwire.cli:app"

[build-system]
requires      = ["hatchling"]
build-backend = "hatchling.build"
# Build hook: runs `npm run build` in dashboard/ before packaging,
# copies dist/ output to agentwire/static/.
```

---

## Build phases for Claude Code

Use these prompts in order. Do not combine phases. Each ends with a verification step —
do not proceed until it passes.

---

### Phase 1 — Models + store + basic bus

```
Read Design-Agentwire.md sections:
"Core data model", "Storage", "Bus server" (REST only — no WebSocket yet).

Tasks:
1. Create pyproject.toml with all dependencies from the spec.
2. Implement agentwire/models.py — WireMessage, MessageType, Session exactly as specified.
3. Implement agentwire/store.py — MessageStore ABC + SQLiteStore using aiosqlite.
   Create the SQL schema on first run with CREATE TABLE IF NOT EXISTS.
4. Implement agentwire/bus.py — FastAPI app with these endpoints only:
   POST /api/messages, GET /api/sessions, GET /api/sessions/{id}/messages, GET /api/stats.
   No WebSocket yet. No static file serving yet.
5. Implement agentwire/pricing.py — PRICING table and calculate_cost().
   Call calculate_cost() automatically in POST /api/messages when msg.model is set.
6. Write tests/test_models.py and tests/test_bus.py using pytest + httpx AsyncClient.
   Test: create a WireMessage, POST it, GET it back, verify all fields round-trip.

Verification:
- pytest tests/ passes with no failures.
- uvicorn agentwire.bus:app --reload starts without errors.
- POST a test WireMessage with curl → GET /api/sessions returns it.
```

---

### Phase 2 — SDK: emit(), wrap(), session()

```
Read Design-Agentwire.md section: "Python SDK" — configure(), emit(), wrap(), session().

Tasks:
1. Implement agentwire/emitter.py:
   - Module-level config singleton (bus_url, default_session, enabled).
   - configure() reads env vars first, then kwargs.
   - emit() posts fire-and-forget via httpx. Never raises — logs warnings on failure.
     Sync-safe: if no event loop running, use a background thread with its own loop.
2. Implement agentwire/wrapper.py:
   - wrap() returns a __getattr__ proxy.
   - Intercepts: run, invoke, chat, generate, step, execute, __call__
   - Records latency, emits TASK before call and RESULT (or ERROR) after.
3. Implement agentwire/session.py:
   - Context manager using threading.local for session_id.
   - Emits session_start and session_end SYSTEM messages.
4. Implement agentwire/__init__.py — public API surface only.
5. Write tests/test_emitter.py:
   - Mock httpx.AsyncClient.post — verify emit() never raises even if server is down.
   - Verify session() sets/restores session_id on threading.local correctly.

Verification:
- pytest tests/ passes.
- Run a simple Python script wrapping a dummy class with agentwire.wrap().
  Messages appear in GET /api/sessions/{id}/messages.
```

---

### Phase 3 — WebSocket broadcaster

```
Read Design-Agentwire.md section: "WebSocket /ws".

Tasks:
1. Add ConnectionManager to bus.py:
   - Maintains List[WebSocket].
   - connect(): add socket, send last 50 messages as "message" events.
   - disconnect(): remove socket.
   - broadcast(event: dict): send JSON to all connected sockets.
2. Add GET /ws WebSocket endpoint.
3. After storing in POST /api/messages: call broadcast() with the new message.
4. Broadcast session_start / session_end events when SYSTEM messages arrive.
5. Add WebSocket tests using starlette TestClient.

Verification:
- wscat -c ws://localhost:7433/ws in one terminal.
- POST a message with curl in another.
- Message appears in wscat immediately.
```

---

### Phase 4 — React dashboard: feed + sidebar + stats

```
Read Design-Agentwire.md section: "Dashboard", all component responsibilities.

Tasks:
1. Scaffold dashboard/ with: npm create vite@latest dashboard -- --template react-ts
   Add: tailwindcss, d3, @types/d3
2. Implement dashboard/src/types.ts — TypeScript types matching all Python models exactly.
3. Implement useWebSocket.ts — auto-reconnect with exponential backoff.
   On first connect: fetch last 50 messages via GET /api/sessions/{id}/messages.
4. Implement StatsBar.tsx — message count, total tokens, total cost.
5. Implement Sidebar.tsx — sessions list + agents list, click to filter.
6. Implement MessageFeed.tsx — scrolling feed with color-coded message types.
   Auto-scroll to bottom unless user scrolled up. Show "↓ N new messages" pill.
7. Wire everything in App.tsx with tab switcher: "Feed" | "Graph" (Graph = empty div for now).
8. Configure FastAPI to serve built dashboard via StaticFiles.
   Vite dev server proxies /api/* to localhost:7433 for local development.

Verification:
- agentwire start → open localhost:7433 → dashboard loads, no console errors.
- Run any wrapped agent → messages appear live. Stats update. Sidebar shows agents.
```

---

### Phase 5 — Graph view (D3 force-directed)

```
Read Design-Agentwire.md section: "GraphView.tsx", "Graph endpoint response shape".

Tasks:
1. Implement GET /api/sessions/{id}/graph in bus.py.
   Compute nodes and edges from stored messages. Return exact shape from spec.
2. Implement GraphView.tsx using D3 force simulation:
   - useRef for SVG, useEffect to init D3.
   - Nodes: circles, radius proportional to message_count (min 20px, max 50px).
   - Edges: lines, strokeWidth proportional to count (min 1px, max 6px).
   - Node labels below circles. Edge tooltips on hover.
   - Click node → onFilterAgent(name). Click edge → onFilterPair(src, tgt).
   - Live updates: stable simulation ref, update nodes/links in-place.
3. Wire GraphView into App.tsx "Graph" tab.

Verification:
- Run a session with 3+ agents → switch to Graph tab.
- Nodes and edges render correctly. Clicking filters the feed. Live updates work.
```

---

### Phase 6 — Session replay

```
Read Design-Agentwire.md section: "ReplayBar.tsx".

Tasks:
1. Add replay state to App.tsx: isReplaying, replayIndex, replaySpeed.
2. Implement ReplayBar.tsx with all controls from the spec.
   Auto-play: setInterval at 1000/speed ms. Clears on pause/unmount/end.
   Timeline scrubber: <input type="range"> that sets replayIndex directly.
3. MessageFeed.tsx: when isReplaying, render only messages[0..replayIndex].
   Disable auto-scroll during replay.
4. GraphView.tsx: only render nodes/edges up to replayIndex.
   Current message's edge: CSS pulse animation (opacity 1→0.3→1, 0.8s infinite).
5. "Replay" button in Sidebar for completed sessions. "Exit replay" in ReplayBar.

Verification:
- Select a completed session → click Replay.
- Messages step through one by one. Graph animates progressively.
- Scrubber and speed control work. Exit replay returns to live feed.
```

---

### Phase 7 — CLI + framework integrations

```
Read Design-Agentwire.md sections: "CLI", "Framework integrations".

Tasks:
1. Implement agentwire/cli.py using Typer. All commands from the spec.
   start: runs uvicorn programmatically, writes PID to .agentwire.pid.
   stop: reads PID file, sends SIGTERM.
   docker up: generates docker-compose.yml → docker compose up -d.
2. Implement agentwire/integrations/langchain.py — AgentWireCallback.
   All hooks and type mappings from the spec.
3. Implement agentwire/integrations/autogen.py — AgentWireHook.
4. Implement agentwire/integrations/crewai.py — wire_crew().
5. Write tests/test_integrations.py — mock callbacks, verify correct WireMessages emitted.

Verification:
- agentwire start / stop / status / clear all work from CLI.
- Run examples/langchain_research with mocked LLM → dashboard shows 3 agents,
  correct message types, correct flow.
```

---

### Phase 8 — Examples + docs + PyPI prep

```
Read Design-Agentwire.md section: "Repository structure" (examples/ and docs/).

Tasks:
1. Write examples/langchain_research/main.py — 3-agent pipeline, mocked LLM, README.
2. Write examples/autogen_coding_team/main.py — orchestrator + coder + reviewer, mocked.
3. Write examples/raw_api_pipeline/main.py — raw Anthropic API calls, no framework, mocked.
4. Set up MkDocs in docs/ — index.md, quickstart.md, api-reference.md, integrations/.
5. Write README.md:
   - One-line description + what it is NOT (not another LangSmith)
   - Install command, 3-step quick start, features list, links.
6. Verify: pip install build && python -m build → twine check dist/* passes.
   Do NOT publish. Leave that to the human.

Verification:
- All three examples run with no errors.
- mkdocs serve starts, all pages render.
- twine check dist/* passes with no warnings.
```

---

## What you must provide — Claude Code cannot infer these

- **Your LLM API keys** — set as env vars when running real (non-mocked) examples.
- **PyPI credentials** — run `twine upload dist/*` yourself after Phase 8.
- **Demo GIF** — record after Phase 8 with `asciinema` or `terminalizer`.
  Show: agent run → live dashboard → graph view → replay mode.
- **Port conflicts** — if 7433 is in use, pass `--port` to `agentwire start`.

---

## Decisions already made — Claude Code must not revisit

- **FastAPI, not Flask or Django.** Async model required for WebSocket + aiosqlite.
- **SQLite default, Postgres optional.** Zero-config for dev. Postgres is `agentwire[postgres]`.
- **Dashboard served from FastAPI.** One process, one port. Not a separate service.
- **D3 directly, not a wrapper library.** Replay animation needs full control.
- **No authentication.** Local dev tool. Team mode uses a shared LAN URL.
- **Python 3.10+ minimum.** Required for `X | None` syntax and match statements.
- **Typer for CLI.** Auto help text, type validation, minimal boilerplate.
- **MIT license.** Maximum adoption for an open-source dev tool.

---

## Definition of done

- [ ] `pip install agentwire` installs cleanly from the built wheel.
- [ ] `agentwire start` boots server and dashboard at localhost:7433.
- [ ] `agentwire.wrap(any_agent)` emits messages visible in the dashboard live.
- [ ] LangChain, AutoGen, and CrewAI integrations each work with a one-line addition.
- [ ] Session replay steps through messages with progressive graph animation.
- [ ] D3 graph shows correct agent topology with weighted edges.
- [ ] All three examples run successfully with mocked LLMs.
- [ ] `pytest tests/` passes with >90% coverage on core modules.
- [ ] `mkdocs serve` starts without errors.
- [ ] `python -m build && twine check dist/*` passes cleanly.
- [ ] README is clear enough that a developer goes from zero to first dashboard in under 5 minutes.