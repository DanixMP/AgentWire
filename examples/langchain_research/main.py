"""
LangChain Research Pipeline Example

A 3-agent research pipeline demonstrating AgentWire integration:
- Planner: Creates research strategy
- Researcher: Executes research
- Summarizer: Summarizes findings

This example uses mocked LLM responses for demonstration.
"""

import time
from typing import Any, List, Optional
import agentwire as aw
from agentwire.integrations.langchain import AgentWireCallback


# Mock LLM for demonstration (replace with real LLM in production)
class MockLLM:
    """Mock LLM that returns predefined responses."""
    
    def __init__(self, name: str = "mock-llm"):
        self.name = name
    
    def __call__(self, prompt: str) -> str:
        """Generate mock response based on prompt."""
        time.sleep(0.2)  # Simulate API latency
        
        if "plan" in prompt.lower():
            return """Research Plan:
1. Search academic papers on quantum computing
2. Review recent breakthroughs (2023-2024)
3. Analyze practical applications
4. Identify key researchers and institutions"""
        
        elif "research" in prompt.lower():
            return """Research Findings:
- IBM achieved 127-qubit quantum processor
- Google demonstrated quantum advantage in optimization
- Error correction improvements: 40% reduction in error rates
- Applications: drug discovery, cryptography, optimization
- Key institutions: IBM, Google, MIT, Caltech"""
        
        elif "summarize" in prompt.lower():
            return """Summary:
Quantum computing made significant progress in 2023-2024. Major achievements include 
IBM's 127-qubit processor and Google's quantum advantage demonstration. Error correction 
improved by 40%, making practical applications more feasible. Primary use cases are drug 
discovery, cryptography, and optimization problems."""
        
        return "Mock response"
    
    def generate(self, prompts: List[str]) -> dict:
        """Generate responses for multiple prompts."""
        return {
            "generations": [[{"text": self(p)}] for p in prompts],
            "llm_output": {
                "token_usage": {
                    "prompt_tokens": sum(len(p.split()) for p in prompts) * 4,
                    "completion_tokens": 150,
                }
            }
        }


# Mock Agent classes
class PlannerAgent:
    """Agent that creates research plans."""
    
    def __init__(self, llm: MockLLM):
        self.llm = llm
    
    def run(self, topic: str) -> str:
        """Create a research plan."""
        prompt = f"Create a detailed research plan for: {topic}"
        return self.llm(prompt)


class ResearchAgent:
    """Agent that executes research."""
    
    def __init__(self, llm: MockLLM):
        self.llm = llm
    
    def run(self, plan: str) -> str:
        """Execute research based on plan."""
        prompt = f"Research the following plan:\n{plan}"
        return self.llm(prompt)


class SummarizerAgent:
    """Agent that summarizes findings."""
    
    def __init__(self, llm: MockLLM):
        self.llm = llm
    
    def run(self, findings: str) -> str:
        """Summarize research findings."""
        prompt = f"Summarize these research findings:\n{findings}"
        return self.llm(prompt)


def main():
    """Run the research pipeline."""
    print("🔬 LangChain Research Pipeline Example")
    print("=" * 60)
    print()
    
    # Configure AgentWire
    aw.configure(bus_url="http://localhost:8000")
    print("✓ Configured AgentWire")
    
    # Create mock LLM
    llm = MockLLM()
    
    # Create agents with AgentWire callbacks
    planner_callback = AgentWireCallback(agent_name="planner")
    researcher_callback = AgentWireCallback(agent_name="researcher")
    summarizer_callback = AgentWireCallback(agent_name="summarizer")
    
    planner = aw.wrap(PlannerAgent(llm), name="planner")
    researcher = aw.wrap(ResearchAgent(llm), name="researcher")
    summarizer = aw.wrap(SummarizerAgent(llm), name="summarizer")
    
    print("✓ Created 3 agents: planner, researcher, summarizer")
    print()
    
    # Run pipeline within a session
    topic = "Quantum Computing Breakthroughs 2023-2024"
    
    with aw.session("langchain-research-demo", name="LangChain Research Pipeline"):
        print(f"📝 Topic: {topic}")
        print()
        
        # Step 1: Planning
        print("1️⃣  Planner creating research strategy...")
        plan = planner.run(topic)
        print(f"   ✓ Plan created ({len(plan)} chars)")
        print(f"   Preview: {plan[:100]}...")
        print()
        
        # Step 2: Research
        print("2️⃣  Researcher executing plan...")
        findings = researcher.run(plan)
        print(f"   ✓ Research complete ({len(findings)} chars)")
        print(f"   Preview: {findings[:100]}...")
        print()
        
        # Step 3: Summarization
        print("3️⃣  Summarizer creating summary...")
        summary = summarizer.run(findings)
        print(f"   ✓ Summary complete ({len(summary)} chars)")
        print()
        
        print("📊 Final Summary:")
        print("-" * 60)
        print(summary)
        print("-" * 60)
    
    print()
    print("✅ Pipeline complete!")
    print()
    print("=" * 60)
    print("View in AgentWire Dashboard:")
    print("  1. Open http://localhost:8000")
    print("  2. See messages in Feed view")
    print("  3. Switch to Graph view to see agent topology")
    print("  4. Click 'Replay Session' to step through")
    print("=" * 60)


if __name__ == "__main__":
    main()
