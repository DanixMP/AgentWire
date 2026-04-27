"""Quick verification script for Phase 1 completion."""

import asyncio
from agentwire.models import WireMessage, MessageType
from agentwire.store import SQLiteStore
from agentwire.pricing import calculate_cost


async def main():
    print("🧪 Testing Phase 1 Components\n")
    
    # Test 1: Pricing calculation
    print("1. Testing pricing calculation...")
    cost = calculate_cost("claude-sonnet-4-6", 1000, 2000)
    expected = 1000 * 0.000003 + 2000 * 0.000015
    assert cost == expected, f"Expected {expected}, got {cost}"
    print(f"   ✓ Cost calculation: {cost} USD")
    
    # Test 2: Create a message
    print("\n2. Testing WireMessage creation...")
    msg = WireMessage(
        session_id="test-session",
        sender="agent1",
        receiver="agent2",
        type=MessageType.TASK,
        content="Test message",
        tokens_in=100,
        tokens_out=200,
        model="claude-sonnet-4-6",
    )
    print(f"   ✓ Message created: {msg.id}")
    
    # Test 3: Store and retrieve
    print("\n3. Testing SQLite storage...")
    store = SQLiteStore("test_phase1.db")
    await store.save_message(msg)
    print(f"   ✓ Message saved to database")
    
    messages = await store.get_messages("test-session")
    assert len(messages) == 1
    assert messages[0].id == msg.id
    print(f"   ✓ Message retrieved: {messages[0].sender} → {messages[0].receiver}")
    
    # Test 4: Session aggregation
    print("\n4. Testing session aggregation...")
    sessions = await store.get_sessions()
    assert len(sessions) == 1
    assert sessions[0].id == "test-session"
    assert sessions[0].message_count == 1
    print(f"   ✓ Session found: {sessions[0].id} ({sessions[0].message_count} messages)")
    
    # Test 5: Stats
    print("\n5. Testing global stats...")
    stats = await store.get_stats()
    print(f"   ✓ Total messages: {stats['total_messages']}")
    print(f"   ✓ Total sessions: {stats['total_sessions']}")
    print(f"   ✓ Total tokens: {stats['total_tokens']}")
    print(f"   ✓ Total cost: ${stats['total_cost_usd']}")
    
    # Cleanup
    await store.clear()
    print("\n✅ Phase 1 verification complete!")
    print("\nNext steps:")
    print("  • Run: uvicorn agentwire.bus:app --reload")
    print("  • Test: curl http://localhost:8000/api/stats")
    print("  • Ready for Phase 2: SDK implementation")


if __name__ == "__main__":
    asyncio.run(main())
