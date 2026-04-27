# LangChain Research Pipeline Example

A 3-agent research pipeline demonstrating AgentWire integration with LangChain.

## Agents

1. **Planner** - Creates research strategy
2. **Researcher** - Executes research based on plan
3. **Summarizer** - Summarizes findings

## Features Demonstrated

- ✅ AgentWire SDK integration (`wrap()`, `session()`)
- ✅ LangChain callback handler (optional)
- ✅ Multi-agent pipeline
- ✅ Message flow visualization
- ✅ Session grouping

## Running the Example

### 1. Start AgentWire Server

```bash
# Terminal 1
agentwire start
```

### 2. Run the Example

```bash
# Terminal 2
python examples/langchain_research/main.py
```

### 3. View in Dashboard

Open http://localhost:8000 to see:
- Real-time message feed
- Agent topology graph
- Session replay

## Expected Output

```
🔬 LangChain Research Pipeline Example
============================================================

✓ Configured AgentWire
✓ Created 3 agents: planner, researcher, summarizer

📝 Topic: Quantum Computing Breakthroughs 2023-2024

1️⃣  Planner creating research strategy...
   ✓ Plan created (XXX chars)
   Preview: Research Plan:...

2️⃣  Researcher executing plan...
   ✓ Research complete (XXX chars)
   Preview: Research Findings:...

3️⃣  Summarizer creating summary...
   ✓ Summary complete (XXX chars)

📊 Final Summary:
------------------------------------------------------------
Summary:
Quantum computing made significant progress in 2023-2024...
------------------------------------------------------------

✅ Pipeline complete!
```

## Dashboard Views

### Feed View
- See messages flowing between agents
- Planner → Researcher → Summarizer
- Each message shows tokens, latency, content

### Graph View
- 3 nodes (planner, researcher, summarizer)
- 2 edges (planner→researcher, researcher→summarizer)
- Node size = message count
- Edge width = message count

### Replay Mode
- Click "Replay Session" button
- Step through messages one by one
- See graph build progressively

## Customization

### Use Real LLM

Replace `MockLLM` with actual LangChain LLM:

```python
from langchain.llms import OpenAI

llm = OpenAI(temperature=0.7)
```

### Add LangChain Callbacks

```python
from agentwire.integrations.langchain import AgentWireCallback

agent = initialize_agent(
    tools=[...],
    llm=llm,
    callbacks=[AgentWireCallback(agent_name="researcher")]
)
```

### Add More Agents

```python
validator = aw.wrap(ValidatorAgent(llm), name="validator")
result = validator.run(summary)
```

## Notes

- This example uses mocked LLM responses for demonstration
- No API keys required
- Works offline
- Replace with real LLM for production use
