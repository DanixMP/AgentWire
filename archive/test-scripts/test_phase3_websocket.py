"""
Phase 3 WebSocket Demo

This script demonstrates real-time message broadcasting via WebSocket.

To run:
1. Terminal 1: uvicorn agentwire.bus:app --reload --port 8000
2. Terminal 2: python test_phase3.py

You should see messages being sent and received in real-time.
"""

import asyncio
import httpx
import websockets
import json
from datetime import datetime


async def websocket_listener(session_id: str):
    """Listen to WebSocket and print received events."""
    uri = f"ws://localhost:8000/ws?session_id={session_id}"
    
    print(f"📡 Connecting to WebSocket: {uri}")
    
    try:
        async with websockets.connect(uri) as websocket:
            print("✓ WebSocket connected\n")
            
            # Listen for messages
            async for message in websocket:
                data = json.loads(message)
                event = data.get("event")
                
                if event == "message":
                    msg = data["data"]
                    timestamp = datetime.fromisoformat(msg["timestamp"]).strftime("%H:%M:%S")
                    print(f"[{timestamp}] {msg['sender']} → {msg['receiver']}: {msg['type']}")
                    print(f"           {msg['content'][:80]}")
                
                elif event == "session_start":
                    session_data = data["data"]
                    print(f"\n🟢 Session started: {session_data['session_id']}")
                    if session_data.get("name"):
                        print(f"   Name: {session_data['name']}")
                
                elif event == "session_end":
                    session_data = data["data"]
                    print(f"\n🔴 Session ended: {session_data['session_id']}\n")
    
    except websockets.exceptions.WebSocketException as e:
        print(f"❌ WebSocket error: {e}")
        print("\nMake sure the server is running:")
        print("  uvicorn agentwire.bus:app --reload --port 8000")


async def send_messages(session_id: str):
    """Send test messages via REST API."""
    base_url = "http://localhost:8000"
    
    print("📤 Sending messages via REST API...\n")
    
    async with httpx.AsyncClient() as client:
        # Wait a bit for WebSocket to connect
        await asyncio.sleep(1)
        
        # Session start
        await client.post(f"{base_url}/api/messages", json={
            "session_id": session_id,
            "sender": "system",
            "receiver": "broadcast",
            "type": "SYSTEM",
            "content": f"Session started: {session_id}",
            "metadata": {"event": "session_start", "name": "Phase 3 Demo"},
        })
        
        await asyncio.sleep(0.5)
        
        # Task message
        await client.post(f"{base_url}/api/messages", json={
            "session_id": session_id,
            "sender": "orchestrator",
            "receiver": "researcher",
            "type": "TASK",
            "content": "Research quantum computing breakthroughs in 2024",
        })
        
        await asyncio.sleep(0.5)
        
        # Result message
        await client.post(f"{base_url}/api/messages", json={
            "session_id": session_id,
            "sender": "researcher",
            "receiver": "orchestrator",
            "type": "RESULT",
            "content": "Found 15 major breakthroughs including improved error correction...",
            "tokens_in": 500,
            "tokens_out": 1500,
            "model": "claude-sonnet-4-6",
            "latency_ms": 2500,
        })
        
        await asyncio.sleep(0.5)
        
        # Tool call
        await client.post(f"{base_url}/api/messages", json={
            "session_id": session_id,
            "sender": "researcher",
            "receiver": "web_search",
            "type": "TOOL_CALL",
            "content": "search('quantum computing 2024')",
        })
        
        await asyncio.sleep(0.5)
        
        # Tool result
        await client.post(f"{base_url}/api/messages", json={
            "session_id": session_id,
            "sender": "web_search",
            "receiver": "researcher",
            "type": "TOOL_RESULT",
            "content": "Found 42 results from arxiv.org, nature.com, and other sources",
        })
        
        await asyncio.sleep(0.5)
        
        # Error message
        await client.post(f"{base_url}/api/messages", json={
            "session_id": session_id,
            "sender": "writer",
            "receiver": "orchestrator",
            "type": "ERROR",
            "content": "RateLimitError: API quota exceeded",
        })
        
        await asyncio.sleep(0.5)
        
        # Session end
        await client.post(f"{base_url}/api/messages", json={
            "session_id": session_id,
            "sender": "system",
            "receiver": "broadcast",
            "type": "SYSTEM",
            "content": f"Session ended: {session_id}",
            "metadata": {"event": "session_end", "name": "Phase 3 Demo"},
        })
        
        print("\n✓ All messages sent")
        
        # Wait a bit for WebSocket to receive all messages
        await asyncio.sleep(2)


async def main():
    print("🚀 Phase 3 WebSocket Demo\n")
    print("="*60)
    
    session_id = f"phase3-demo-{datetime.now().strftime('%H%M%S')}"
    
    # Run WebSocket listener and message sender concurrently
    try:
        await asyncio.gather(
            websocket_listener(session_id),
            send_messages(session_id),
        )
    except KeyboardInterrupt:
        print("\n\n👋 Demo stopped")
    
    print("="*60)
    print("\n✅ Phase 3 WebSocket Demo Complete!")
    print("\nWhat was demonstrated:")
    print("  • WebSocket connection and real-time message streaming")
    print("  • Session start/end event broadcasting")
    print("  • Multiple message types (TASK, RESULT, ERROR, TOOL_CALL, etc.)")
    print("  • Automatic cost calculation for messages with model info")
    print("  • Concurrent REST API posting and WebSocket receiving")


if __name__ == "__main__":
    asyncio.run(main())
