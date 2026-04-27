# AgentWire

**Real-time message bus and inspector for multi-agent LLM systems**

AgentWire makes multi-agent systems visible. It sits between your agents, captures every inter-agent message, and surfaces them in a live dashboard with feed, graph view, cost tracker, and session replay.

## The Problem

When a 5-agent pipeline produces a bad result, you have no way to see which agent said what to whom and why things went wrong. Multi-agent systems are opaque black boxes.

## The Solution

```python
pip install agentwire
agentwire start

# In your code
import agentwire as aw

aw.configure(bus_url="http://localhost:7433")

researcher = aw.wrap(ResearchAgent(), name="researcher")
writer = aw.wrap(WriterAgent(), name="writer")

with aw.session("blog-post-run-42"):
    facts = researcher.run("Find quantum computing breakthroughs")
    post = writer.run(facts)
```

Open http://localhost:7433 → see everything in real-time.

## Key Features

### 🔄 Real-Time Message Feed
See messages flowing between agents as they happen. Every TASK, RESULT, ERROR, and TOOL_CALL is captured and displayed.

### 🕸️ Interactive Graph View
Visualize agent topology with D3 force-directed graphs. Node size = message count, edge width = message frequency.

### ⏮️ Session Replay
Step through past runs message-by-message. Progressive graph rendering shows how the system evolved.

### 💰 Cost Tracking
Automatic token counting and USD cost calculation for all major LLM providers.

### 🔌 Framework-Agnostic
Works with LangChain, AutoGen, CrewAI, and raw API calls. One unified view across all frameworks.

### 🚀 Zero Infrastructure
SQLite by default. No Docker, no Postgres, no signup required for local dev.

## What Makes It Different

Unlike LangSmith, Langfuse, Phoenix, and AgentOps:

- **Message bus abstraction** - Traces inter-agent messages, not just LLM calls
- **Framework-agnostic** - One view across LangChain, AutoGen, CrewAI, raw APIs
- **Session replay** - Step through past runs with graph animation
- **Zero setup** - `pip install && agentwire start` with SQLite

## Quick Links

- [Quick Start](quickstart.md) - Get started in 5 minutes
- [SDK Reference](sdk/overview.md) - Complete API documentation
- [Examples](examples/langchain.md) - Working examples
- [Dashboard Guide](dashboard/overview.md) - Using the web interface

## Architecture

```
Agent Code (SDK)
    ↓ emit()
REST API (POST /api/messages)
    ↓ store + broadcast()
    ├─→ SQLite Database
    └─→ WebSocket Clients
         └─→ React Dashboard
```

## Status

✅ Core functionality complete
✅ Production-ready SDK
✅ Full-featured dashboard
✅ Framework integrations
✅ CLI tool

## License

MIT - See LICENSE file for details
