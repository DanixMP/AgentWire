# AgentWire Dashboard

Real-time React dashboard for monitoring multi-agent LLM systems.

## Development

```bash
# Install dependencies
npm install

# Start dev server (with API proxy)
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

## Features

- **Real-time message feed** - See agent messages as they happen
- **WebSocket connection** - Auto-reconnect with exponential backoff
- **Stats tracking** - Messages, tokens, and cost
- **Agent filtering** - Filter messages by agent
- **Session management** - View messages by session
- **Auto-scroll** - Smart scrolling with "new messages" indicator

## Architecture

- **React 18** - UI framework
- **TypeScript** - Type safety
- **Vite** - Build tool and dev server
- **Tailwind CSS** - Styling
- **WebSocket** - Real-time communication

## API Proxy

The Vite dev server proxies API requests to the AgentWire backend:

- `/api/*` → `http://localhost:8000/api/*`
- `/ws` → `ws://localhost:8000/ws`

Make sure the AgentWire server is running:

```bash
uvicorn agentwire.bus:app --reload --port 8000
```

## Components

- **App.tsx** - Main app with state management
- **Sidebar.tsx** - Sessions and agents list
- **StatsBar.tsx** - Message count, tokens, cost
- **MessageFeed.tsx** - Scrolling message feed
- **useWebSocket.ts** - WebSocket hook with auto-reconnect

## Message Type Colors

- TASK → Teal (#5DCAA5)
- RESULT → Purple (#AFA9EC)
- ERROR → Red (#F09595)
- TOOL_CALL → Amber (#EF9F27)
- TOOL_RESULT → Amber Dim (#B87C14)
- SYSTEM → Gray (#888888)
