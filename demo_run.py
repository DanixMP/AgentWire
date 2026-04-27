"""
Quick Demo of AgentWire

This demonstrates a simple 3-agent pipeline with AgentWire.
"""

import time
import agentwire as aw


class PlannerAgent:
    """Plans the research strategy."""
    
    def run(self, topic: str) -> dict:
        """Create a research plan."""
        print(f"      [Planner thinking about: {topic}]")
        time.sleep(0.3)
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
        print(f"      [Researcher executing {len(plan['steps'])} steps]")
        time.sleep(0.5)
        findings = []
        for step in plan["steps"]:
            findings.append(f"✓ {step}")
        
        return "\n".join([
            f"Research on {plan['topic']}:",
            *findings,
            "\nKey insight: Quantum computing shows 40% improvement in 2024.",
        ])


class WriterAgent:
    """Writes the final article."""
    
    def run(self, research: str) -> str:
        """Write article based on research."""
        print(f"      [Writer composing article from {len(research)} chars of research]")
        time.sleep(0.3)
        return f"""
# Quantum Computing Breakthroughs 2024

Based on extensive research:

{research}

## Conclusion
The field is advancing rapidly with significant implications for cryptography
and drug discovery.
"""


def main():
    print("\n" + "="*70)
    print("🚀 AgentWire Demo - Multi-Agent Pipeline")
    print("="*70 + "\n")
    
    # Configure AgentWire to connect to local server
    aw.configure(bus_url="http://localhost:7433")
    print("✓ Configured AgentWire → http://localhost:7433")
    
    # Create and wrap agents
    planner = aw.wrap(PlannerAgent(), name="planner")
    researcher = aw.wrap(ResearchAgent(), name="researcher")
    writer = aw.wrap(WriterAgent(), name="writer")
    print("✓ Created 3 agents: planner, researcher, writer")
    print()
    
    # Run the pipeline within a session
    with aw.session("demo-quantum-2024", name="Quantum Computing Demo"):
        print("📝 Session: demo-quantum-2024")
        print("-" * 70)
        
        # Step 1: Planning
        print("\n1️⃣  PLANNER: Creating research strategy...")
        plan = planner.run("Quantum Computing Breakthroughs 2024")
        print(f"   ✓ Plan created with {len(plan['steps'])} steps")
        
        # Step 2: Research
        print("\n2️⃣  RESEARCHER: Executing research plan...")
        findings = researcher.run(plan)
        print(f"   ✓ Research complete ({len(findings)} chars)")
        
        # Step 3: Writing
        print("\n3️⃣  WRITER: Composing final article...")
        article = writer.run(findings)
        print(f"   ✓ Article written ({len(article)} chars)")
        
        print("\n" + "-" * 70)
        print("📊 FINAL ARTICLE PREVIEW:")
        print("-" * 70)
        print(article[:300] + "...")
        print("-" * 70)
    
    print("\n✅ Session completed: demo-quantum-2024")
    print("\n" + "="*70)
    print("🎯 NOW CHECK THE DASHBOARD:")
    print("="*70)
    print("  1. Open: http://localhost:7433")
    print("  2. See all 6 messages in the Feed view")
    print("  3. Switch to Graph view to see agent connections")
    print("  4. Check Stats bar for message count and tokens")
    print("  5. Click 'Replay' to step through the session")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
