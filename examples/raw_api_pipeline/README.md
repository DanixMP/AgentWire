# Raw API Pipeline Example

A pure Python data pipeline demonstrating AgentWire without any framework dependencies.

## Pipeline

```
Fetcher → Processor → Analyzer → Reporter
```

1. **Fetcher** - Retrieves data from source
2. **Processor** - Transforms and calculates statistics
3. **Analyzer** - Classifies and makes recommendations
4. **Reporter** - Generates final report

## Features Demonstrated

- ✅ Framework-agnostic usage
- ✅ Pure Python agents
- ✅ Linear pipeline pattern
- ✅ AgentWire SDK only (no integrations)
- ✅ Simple wrap() and session() usage

## Running the Example

### 1. Start AgentWire Server

```bash
# Terminal 1
agentwire start
```

### 2. Run the Example

```bash
# Terminal 2
python examples/raw_api_pipeline/main.py
```

### 3. View in Dashboard

Open http://localhost:8000

## Expected Output

```
📊 Raw API Pipeline Example
============================================================

✓ Configured AgentWire
✓ Created 4 agents: fetcher, processor, analyzer, reporter

📝 Source: production-database

1️⃣  Fetcher retrieving data...
   ✓ Fetched 5 records

2️⃣  Processor transforming data...
   ✓ Processed 4/5 active records
   Stats: sum=138, avg=34.50

3️⃣  Analyzer evaluating data...
   ✓ Classification: medium
   Confidence: 95.0%

4️⃣  Reporter generating final report...
   ✓ Report generated

DATA ANALYSIS REPORT
==================================================

Classification: MEDIUM
Confidence: 95.0%

Metrics:
  - Total Records: 5
  - Active Records: 4
  - Average Value: 34.50

Recommendation:
  Standard monitoring

==================================================

✅ Pipeline complete!
```

## Dashboard Views

### Feed View
- 4-step linear pipeline
- Each step shows input/output
- Clear data flow

### Graph View
- 4 nodes in a line
- 3 edges connecting them
- Simple topology

### Replay Mode
- Step through data transformation
- See how data flows through pipeline
- Watch statistics being calculated

## Customization

### Add More Stages

```python
validator = aw.wrap(DataValidator(), name="validator")
validated = validator.run(data)
```

### Add Error Handling

```python
class DataProcessor:
    def run(self, data: dict) -> dict:
        try:
            # Process data
            return result
        except Exception as e:
            # Emit error message
            aw.emit(aw.WireMessage(
                session_id=aw.get_current_session(),
                sender="processor",
                receiver="orchestrator",
                type=aw.MessageType.ERROR,
                content=str(e)
            ))
            raise
```

### Add Manual Messages

```python
# Emit custom message
aw.emit(aw.WireMessage(
    session_id=aw.get_current_session(),
    sender="processor",
    receiver="logger",
    type=aw.MessageType.SYSTEM,
    content="Processing started",
    metadata={"stage": "preprocessing"}
))
```

## Use Cases

This pattern is ideal for:
- Data pipelines
- ETL workflows
- Batch processing
- Report generation
- Any sequential processing

## Notes

- No framework dependencies
- Pure Python
- No API keys required
- Works offline
- Easy to understand and modify
