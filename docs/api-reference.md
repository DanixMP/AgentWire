# API Reference

Complete REST API and WebSocket reference for AgentWire.

## REST API

Base URL: `http://localhost:7433/api`

### POST /api/messages

Ingest a new message.

**Request Body:**

```json
{
  "session_id": "string",
  "sender": "string",
  "receiver": "string",
  "type": "TASK|RESULT|ERROR|TOOL_CALL|TOOL_RESULT|SYSTEM",
  "content": "string",
  "metadata": {},
  "tokens_in": 0,
  "tokens_out": 0,
  "model": "string",
  "latency_ms": 0,
  "tags": []
}
```

**Response:**

```json
{
  "status": "ok",
  "id": "message-uuid"
}
```

### GET /api/sessions

List all sessions.

**Response:**

```json
[
  {
    "id": "session-id",
    "name": "Session Name",
    "started_at": "2024-01-15T10:30:00Z",
    "ended_at": null,
    "message_count": 42,
    "total_tokens": 15000,
    "total_cost_usd": 0.045,
    "agents": ["agent1", "agent2"]
  }
]
```

### GET /api/sessions/{id}

Get a single session.

**Response:**

```json
{
  "id": "session-id",
  "name": "Session Name",
  "started_at": "2024-01-15T10:30:00Z",
  "ended_at": "2024-01-15T10:35:00Z",
  "message_count": 42,
  "total_tokens": 15000,
  "total_cost_usd": 0.045,
  "agents": ["agent1", "agent2"]
}
```

### GET /api/sessions/{id}/messages

Get all messages for a session.

**Response:**

```json
[
  {
    "id": "msg-uuid",
    "session_id": "session-id",
    "parent_id": null,
    "sender": "agent1",
    "receiver": "agent2",
    "type": "TASK",
    "content": "Message content",
    "metadata": {},
    "tokens_in": 100,
    "tokens_out": 200,
    "model": "claude-sonnet-4-6",
    "latency_ms": 1500,
    "cost_usd": 0.003,
    "timestamp": "2024-01-15T10:30:00Z",
    "tags": []
  }
]
```

### GET /api/sessions/{id}/graph

Get graph data for a session.

**Response:**

```json
{
  "nodes": [
    {
      "id": "agent1",
      "message_count": 10,
      "total_tokens": 5000,
      "dominant_type": "TASK"
    }
  ],
  "edges": [
    {
      "source": "agent1",
      "target": "agent2",
      "count": 5,
      "dominant_type": "TASK",
      "total_tokens": 2500,
      "avg_latency_ms": 1200
    }
  ]
}
```

### GET /api/stats

Get global statistics.

**Response:**

```json
{
  "total_messages": 1000,
  "total_sessions": 25,
  "total_tokens": 500000,
  "total_cost_usd": 1.5
}
```

### DELETE /api/sessions/{id}

Delete a session and its messages.

**Response:**

```json
{
  "status": "ok"
}
```

### DELETE /api/messages

Clear all sessions and messages.

**Response:**

```json
{
  "status": "ok"
}
```

## WebSocket API

URL: `ws://localhost:7433/ws`

Query Parameters:
- `session_id` (optional) - Filter messages by session

### Events Received

#### message

New message arrived.

```json
{
  "event": "message",
  "data": {
    "id": "msg-uuid",
    "session_id": "session-id",
    "sender": "agent1",
    "receiver": "agent2",
    "type": "TASK",
    "content": "Message content",
    ...
  }
}
```

#### session_start

Session started.

```json
{
  "event": "session_start",
  "data": {
    "session_id": "session-id",
    "timestamp": "2024-01-15T10:30:00Z",
    "name": "Session Name"
  }
}
```

#### session_end

Session ended.

```json
{
  "event": "session_end",
  "data": {
    "session_id": "session-id",
    "timestamp": "2024-01-15T10:35:00Z",
    "name": "Session Name"
  }
}
```

### Connection Behavior

- On connect: Receives last 50 messages for session (if session_id provided)
- Auto-reconnect: Exponential backoff (500ms → 8s)
- Ping/pong: Send "ping" to receive "pong"

## Message Types

| Type | Description |
|------|-------------|
| TASK | Agent assigns work to another agent |
| RESULT | Agent returns completed work |
| ERROR | Agent reports failure |
| TOOL_CALL | Agent calls an external tool |
| TOOL_RESULT | Tool returns result to agent |
| SYSTEM | Orchestration/control messages |

## Model Pricing

Supported models with automatic cost calculation:

| Model | Input (per token) | Output (per token) |
|-------|-------------------|-------------------|
| claude-opus-4-6 | $0.000015 | $0.000075 |
| claude-sonnet-4-6 | $0.000003 | $0.000015 |
| claude-haiku-4-5 | $0.0000008 | $0.000004 |
| gpt-4o | $0.0000025 | $0.00001 |
| gpt-4o-mini | $0.00000015 | $0.0000006 |
| gemini-1.5-pro | $0.00000125 | $0.000005 |

## Error Responses

All endpoints return standard error responses:

```json
{
  "detail": "Error message"
}
```

HTTP Status Codes:
- 200: Success
- 404: Not Found
- 422: Validation Error
- 500: Internal Server Error

## Rate Limits

No rate limits for local development.

For production deployments, implement rate limiting at the reverse proxy level.

## CORS

CORS is enabled for all origins in development mode.

For production, configure CORS in the FastAPI app.
