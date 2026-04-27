# AutoGen Coding Team Example

A 3-agent coding team demonstrating AgentWire integration with AutoGen patterns.

## Agents

1. **Orchestrator** - Manages workflow and assigns tasks
2. **Coder** - Writes code based on requirements
3. **Reviewer** - Reviews code and provides feedback

## Workflow

```
Orchestrator → Coder: "Write Fibonacci function"
Coder → Orchestrator: [code]
Orchestrator → Reviewer: "Review this code"
Reviewer → Orchestrator: {approved: true, score: 10}
Orchestrator: "Task complete!"
```

## Features Demonstrated

- ✅ Multi-agent collaboration
- ✅ Bidirectional communication
- ✅ Code review workflow
- ✅ AgentWire SDK integration
- ✅ Message flow visualization

## Running the Example

### 1. Start AgentWire Server

```bash
# Terminal 1
agentwire start
```

### 2. Run the Example

```bash
# Terminal 2
python examples/autogen_coding_team/main.py
```

### 3. View in Dashboard

Open http://localhost:8000

## Expected Output

```
👥 AutoGen Coding Team Example
============================================================

✓ Configured AgentWire
✓ Created 3 agents: orchestrator, coder, reviewer

📝 Task: Write a function to calculate Fibonacci numbers

1️⃣  Orchestrator assigning task to coder...
   ✓ Task assigned
   Requirements: 3 items

2️⃣  Coder writing code...
   ✓ Code written (XXX chars)
   Preview:
   def fibonacci(n: int) -> int:
       """
       Calculate the nth Fibonacci number.
   ...

3️⃣  Reviewer reviewing code...
   ✓ Review complete
   Approved: True
   Score: 10/10
   Suggestions: Looks good!

4️⃣  Orchestrator processing review...
   ✓ Task complete! Code approved.

✅ Code approved and ready for deployment!
```

## Dashboard Views

### Feed View
- 4-step workflow visible
- Orchestrator ↔ Coder ↔ Reviewer
- Each message shows content and metadata

### Graph View
- 3 nodes (orchestrator, coder, reviewer)
- Bidirectional edges showing collaboration
- Edge width shows message frequency

### Replay Mode
- Step through the workflow
- See code review process
- Watch decision making

## Customization

### Use Real AutoGen

```python
from autogen import AssistantAgent, UserProxyAgent
from agentwire.integrations.autogen import wire_autogen_agent

coder = AssistantAgent(
    name="coder",
    llm_config={"model": "gpt-4"}
)

wire_autogen_agent(coder, name="coder", session_id="run-1")
```

### Add More Agents

```python
tester = aw.wrap(TesterAgent(), name="tester")
test_results = tester.run(code)
```

### Implement Real Code Review

```python
class ReviewerAgent:
    def run(self, code: str) -> dict:
        # Use AST parsing, linting, etc.
        issues = analyze_code(code)
        return {
            "approved": len(issues) == 0,
            "issues": issues,
        }
```

## Notes

- This example uses mocked agents for demonstration
- No API keys required
- Works offline
- Replace with real AutoGen agents for production
