"""
Simple multi-agent pipeline example.

This example demonstrates:
- Wrapping agents with agentwire.wrap()
- Using session context manager
- Automatic message emission
- Real-time visibility in the dashboard

To run:
1. Start the AgentWire server: uvicorn agentwire.bus:app --reload
2. Open http://localhost:8000/api/stats to verify server is running
3. Run this script: python examples/simple_pipeline.py
4. Check the dashboard (when implemented) or query the API
"""

import time
import agentwire as aw


class PlannerAgent:
    """Plans the research strategy."""
    
    def run(self, topic: str) -> dict:
        """Create a research plan."""
        time.sleep(0.2)
        return {
            "topic": topic,
            "steps": [
                "Search academic papers",
                "Review recent news",
                "Analyze trends",
            ],
            "estimated_time": "30 minutes",
        }


class ResearchAgent:
    """Executes the research plan."""
    
    def run(self, plan: dict) -> str:
        """Execute research based on plan."""
        time.sleep(0.5)
        findings = []
        for step in plan["steps"]:
            findings.append(f"Completed: {step}")
        
        return "\n".join([
            f"Research on {plan['topic']}:",
            *findings,
            "\nKey insight: Quantum computing shows 40% improvement in 2024.",
        ])


class WriterAgent:
    """Writes the final article."""
    
    def run(self, research: str) -> str:
        """Write article based on research."""
        time.sleep(0.3)
        return f"""
# Article: Quantum Computing Breakthroughs

Based on extensive research:

{research}

## Conclusion
The field is advancing rapidly with significant implications for cryptography
and drug discovery.
"""


def main():
    print("🚀 Starting Simple Multi-Agent Pipeline\n")
    
    # Configure AgentWire to connect to local server
    aw.configure(bus_url="http://localhost:8000")
    print("✓ Configured to connect to http://localhost:8000")
    
    # Create and wrap agents
    planner = aw.wrap(PlannerAgent(), name="planner")
    researcher = aw.wrap(ResearchAgent(), name="researcher")
    writer = aw.wrap(WriterAgent(), name="writer")
    print("✓ Created 3 agents: planner, researcher, writer\n")
    
    # Run the pipeline within a session
    with aw.session("quantum-article-2024", name="Quantum Computing Article"):
        print("📝 Session started: quantum-article-2024\n")
        
        # Step 1: Planning
        print("1️⃣  Planner creating research strategy...")
        plan = planner.run("Quantum Computing Breakthroughs 2024")
        print(f"   ✓ Plan created with {len(plan['steps'])} steps\n")
        
        # Step 2: Research
        print("2️⃣  Researcher executing plan...")
        findings = researcher.run(plan)
        print(f"   ✓ Research complete ({len(findings)} chars)\n")
        
        # Step 3: Writing
        print("3️⃣  Writer composing article...")
        article = writer.run(findings)
        print(f"   ✓ Article written ({len(article)} chars)\n")
        
        print("📊 Final article preview:")
        print(article[:200] + "...\n")
    
    print("✅ Session ended: quantum-article-2024")
    print("\n" + "="*60)
    print("Check the AgentWire dashboard to see:")
    print("  • Message flow between agents")
    print("  • Timing and latency for each step")
    print("  • Session replay")
    print("="*60)


if __name__ == "__main__":
    main()
