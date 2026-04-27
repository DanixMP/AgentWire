# Quick Start

Get AgentWire running in 5 minutes.

## Installation

```bash
pip install agentwire
```

## Start the Server

```bash
agentwire start
```

This starts:
- REST API at http://localhost:7433/api
- WebSocket at ws://localhost:7433/ws
- Dashboard at http://localhost:7433

## Wrap Your Agents

```python
import agentwire as aw

# Configure
aw.configure(bus_url="http://localhost:7433")

# Wrap agents
researcher = aw.wrap(ResearchAgent(), name="researcher")
writer = aw.wrap(WriterAgent(), name="writer")

# Run with session
with aw.session("my-run"):
    facts = researcher.run("Find quantum computing breakthroughs")
    post = writer.run(facts)
```

## View in Dashboard

Open http://localhost:7433 to see:

- **Feed View** - Real-time message stream
- **Graph View** - Agent topology
- **Stats** - Messages, tokens, cost
- **Replay** - Step through session

## Next Steps

- [Configuration](configuration.md) - Customize settings
- [SDK Reference](sdk/overview.md) - Learn the API
- [Examples](examples/langchain.md) - See working examples
- [Integrations](integrations/langchain.md) - Use with frameworks

## Common Patterns

### Multiple Agents

```python
planner = aw.wrap(PlannerAgent(), name="planner")
researcher = aw.wrap(ResearchAgent(), name="researcher")
writer = aw.wrap(WriterAgent(), name="writer")

with aw.session("blog-post"):
    plan = planner.run("Create blog post about AI")
    facts = researcher.run(plan)
    post = writer.run(facts)
```

### Error Handling

```python
try:
    result = agent.run("task")
except Exception as e:
    # Error automatically emitted to AgentWire
    print(f"Agent failed: {e}")
```

### Manual Messages

```python
aw.emit(aw.WireMessage(
    session_id=aw.get_current_session(),
    sender="my-agent",
    receiver="other-agent",
    type=aw.MessageType.TASK,
    content="Custom message"
))
```

## Troubleshooting

### Server won't start

```bash
# Check if port is in use
agentwire status

# Use different port
agentwire start --port 8000
```

### Messages not appearing

```python
# Check configuration
aw.configure(bus_url="http://localhost:7433", enabled=True)

# Verify server is running
# Visit http://localhost:7433
```

### Dashboard not loading

```bash
# Restart server
agentwire stop
agentwire start
```

## Environment Variables

```bash
export AGENTWIRE_URL="http://localhost:7433"
export AGENTWIRE_SESSION="my-default-session"
export AGENTWIRE_ENABLED="true"
```

Then in code:

```python
aw.configure()  # Uses env vars
```
