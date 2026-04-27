"""End-to-end test for Phase 2 SDK functionality."""

import time
import agentwire as aw


class ResearchAgent:
    """Dummy research agent for testing."""
    
    def run(self, query: str) -> str:
        """Simulate research."""
        time.sleep(0.1)
        return f"Research findings for: {query}"


class WriterAgent:
    """Dummy writer agent for testing."""
    
    def run(self, facts: str) -> str:
        """Simulate writing."""
        time.sleep(0.1)
        return f"Article based on: {facts[:50]}..."


def main():
    print("🧪 Testing Phase 2 SDK\n")
    
    # Configure AgentWire
    print("1. Configuring AgentWire...")
    aw.configure(
        bus_url="http://localhost:7433",
        default_session="test-default",
    )
    print("   ✓ Configured")
    
    # Create and wrap agents
    print("\n2. Creating and wrapping agents...")
    researcher = aw.wrap(ResearchAgent(), name="researcher")
    writer = aw.wrap(WriterAgent(), name="writer")
    print("   ✓ Agents wrapped")
    
    # Test without session context (uses default)
    print("\n3. Testing without session context...")
    result = researcher.run("quantum computing")
    print(f"   ✓ Researcher result: {result[:50]}...")
    
    # Test with session context
    print("\n4. Testing with session context...")
    with aw.session("blog-post-run", name="Blog Post Generation") as session_id:
        print(f"   ✓ Session started: {session_id}")
        
        # Run research
        facts = researcher.run("AI breakthroughs 2024")
        print(f"   ✓ Research complete: {facts[:50]}...")
        
        # Run writing
        article = writer.run(facts)
        print(f"   ✓ Article complete: {article[:50]}...")
    
    print("   ✓ Session ended")
    
    # Test nested sessions
    print("\n5. Testing nested sessions...")
    with aw.session("outer-session"):
        print("   ✓ Outer session started")
        researcher.run("outer task")
        
        with aw.session("inner-session"):
            print("   ✓ Inner session started")
            researcher.run("inner task")
        
        print("   ✓ Inner session ended")
        researcher.run("back to outer")
    
    print("   ✓ Outer session ended")
    
    # Test error handling
    print("\n6. Testing error handling...")
    
    class FailingAgent:
        def run(self, task: str):
            raise ValueError("Intentional error for testing")
    
    failing = aw.wrap(FailingAgent(), name="failing-agent")
    
    try:
        failing.run("this will fail")
    except ValueError as e:
        print(f"   ✓ Error caught: {e}")
    
    print("\n✅ Phase 2 SDK verification complete!")
    print("\nWhat was tested:")
    print("  • configure() with custom settings")
    print("  • wrap() to create agent proxies")
    print("  • session() context manager")
    print("  • Nested sessions")
    print("  • Error handling and ERROR message emission")
    print("  • Message emission (fire-and-forget)")
    print("\nNote: Messages were emitted but not verified against the bus.")
    print("      Start the bus server to see messages in real-time:")
    print("      uvicorn agentwire.bus:app --reload")


if __name__ == "__main__":
    main()
