"""
AutoGen Coding Team Example

A 3-agent coding team demonstrating AgentWire integration:
- Orchestrator: Manages the workflow
- Coder: Writes code
- Reviewer: Reviews and suggests improvements

This example uses mocked agents for demonstration.
"""

import time
import agentwire as aw
from agentwire.integrations.autogen import AgentWireHook


class OrchestratorAgent:
    """Orchestrator that manages the workflow."""
    
    def __init__(self, name: str = "orchestrator"):
        self.name = name
    
    def run(self, task: str) -> dict:
        """Assign task to coder."""
        time.sleep(0.1)
        return {
            "action": "assign_to_coder",
            "task": task,
            "requirements": [
                "Write clean, documented code",
                "Include error handling",
                "Add type hints",
            ]
        }
    
    def process_review(self, review: dict) -> str:
        """Process review and decide next action."""
        time.sleep(0.1)
        if review.get("approved"):
            return "Task complete! Code approved."
        else:
            return f"Revisions needed: {review.get('suggestions')}"


class CoderAgent:
    """Coder that writes code."""
    
    def __init__(self, name: str = "coder"):
        self.name = name
    
    def run(self, assignment: dict) -> str:
        """Write code based on assignment."""
        time.sleep(0.3)
        
        code = '''def fibonacci(n: int) -> int:
    """
    Calculate the nth Fibonacci number.
    
    Args:
        n: Position in Fibonacci sequence (0-indexed)
    
    Returns:
        The nth Fibonacci number
    
    Raises:
        ValueError: If n is negative
    """
    if n < 0:
        raise ValueError("n must be non-negative")
    
    if n <= 1:
        return n
    
    a, b = 0, 1
    for _ in range(2, n + 1):
        a, b = b, a + b
    
    return b
'''
        return code


class ReviewerAgent:
    """Reviewer that reviews code."""
    
    def __init__(self, name: str = "reviewer"):
        self.name = name
    
    def run(self, code: str) -> dict:
        """Review code and provide feedback."""
        time.sleep(0.2)
        
        # Simple mock review
        has_docstring = '"""' in code
        has_type_hints = ': int' in code
        has_error_handling = 'raise' in code
        
        approved = has_docstring and has_type_hints and has_error_handling
        
        suggestions = []
        if not has_docstring:
            suggestions.append("Add docstring")
        if not has_type_hints:
            suggestions.append("Add type hints")
        if not has_error_handling:
            suggestions.append("Add error handling")
        
        return {
            "approved": approved,
            "suggestions": suggestions if suggestions else ["Looks good!"],
            "score": 10 if approved else 7,
        }


def main():
    """Run the coding team workflow."""
    print("👥 AutoGen Coding Team Example")
    print("=" * 60)
    print()
    
    # Configure AgentWire
    aw.configure(bus_url="http://localhost:8000")
    print("✓ Configured AgentWire")
    
    # Create agents with AgentWire wrapping
    orchestrator = aw.wrap(OrchestratorAgent(), name="orchestrator")
    coder = aw.wrap(CoderAgent(), name="coder")
    reviewer = aw.wrap(ReviewerAgent(), name="reviewer")
    
    print("✓ Created 3 agents: orchestrator, coder, reviewer")
    print()
    
    # Run workflow within a session
    task = "Write a function to calculate Fibonacci numbers"
    
    with aw.session("autogen-coding-demo", name="AutoGen Coding Team"):
        print(f"📝 Task: {task}")
        print()
        
        # Step 1: Orchestrator assigns task
        print("1️⃣  Orchestrator assigning task to coder...")
        assignment = orchestrator.run(task)
        print(f"   ✓ Task assigned")
        print(f"   Requirements: {len(assignment['requirements'])} items")
        print()
        
        # Step 2: Coder writes code
        print("2️⃣  Coder writing code...")
        code = coder.run(assignment)
        print(f"   ✓ Code written ({len(code)} chars)")
        print(f"   Preview:")
        print("   " + "\n   ".join(code.split("\n")[:5]))
        print("   ...")
        print()
        
        # Step 3: Reviewer reviews code
        print("3️⃣  Reviewer reviewing code...")
        review = reviewer.run(code)
        print(f"   ✓ Review complete")
        print(f"   Approved: {review['approved']}")
        print(f"   Score: {review['score']}/10")
        print(f"   Suggestions: {', '.join(review['suggestions'])}")
        print()
        
        # Step 4: Orchestrator processes review
        print("4️⃣  Orchestrator processing review...")
        result = orchestrator.process_review(review)
        print(f"   ✓ {result}")
        print()
        
        if review['approved']:
            print("✅ Code approved and ready for deployment!")
        else:
            print("⚠️  Revisions needed")
    
    print()
    print("=" * 60)
    print("View in AgentWire Dashboard:")
    print("  1. Open http://localhost:8000")
    print("  2. See 4-step workflow in Feed view")
    print("  3. Switch to Graph view:")
    print("     - orchestrator ↔ coder")
    print("     - orchestrator ↔ reviewer")
    print("  4. Use Replay to step through workflow")
    print("=" * 60)


if __name__ == "__main__":
    main()
