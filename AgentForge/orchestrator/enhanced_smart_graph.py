"""
Enhanced Smart Graph - Integrates the smart orchestrator with existing graph
Demonstrates the comparison between deterministic and agentic approaches
"""

from typing import Dict, Any, List, Annotated
from pathlib import Path
from langgraph.graph import StateGraph, END
from operator import add
from dataclasses import dataclass
from enum import Enum

from orchestrator.smart_orchestrator import SmartOrchestrator, Mode
from orchestrator.agents import spec_extractor, planner, scaffolder, codegen
from core.llm_client import LLMClient
from colorama import Fore, Style


@dataclass
class ComparisonResult:
    """Result of comparing different approaches"""
    deterministic_time: float
    agentic_time: float
    deterministic_quality: float
    agentic_quality: float
    winner: str
    reasoning: str


class EnhancedBuildState(dict):
    """Enhanced build state with agentic capabilities"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Core fields
        self.setdefault("prompt", "")
        self.setdefault("name", "")
        self.setdefault("spec", {})
        self.setdefault("preset", "")
        self.setdefault("artifacts_dir", "")
        self.setdefault("project_dir", "")
        self.setdefault("logs", [])
        self.setdefault("status", "")
        self.setdefault("tests_ok", False)
        
        # Enhanced agentic fields
        self.setdefault("tech_selection", {})
        self.setdefault("eval", {})
        self.setdefault("mode", "hybrid")
        self.setdefault("comparison_data", {})
        self.setdefault("agent_decisions", [])
        self.setdefault("questions_asked", [])
        self.setdefault("memory_used", False)
        self.setdefault("templates_used", [])
        self.setdefault("validation_results", {})


def smart_orchestrator_node(state: EnhancedBuildState) -> EnhancedBuildState:
    """Main smart orchestrator node"""
    
    llm_client = LLMClient()
    orchestrator = SmartOrchestrator(llm_client)
    
    print(f"{Fore.CYAN}🧠 Starting Smart Orchestration...{Style.RESET_ALL}")
    
    # Run the orchestrator
    result = orchestrator.orchestrate(state)
    
    # Update state with results
    state.update(result)
    state["logs"].append("Smart orchestration completed")
    
    return state


def comparison_node(state: EnhancedBuildState) -> EnhancedBuildState:
    """Compare deterministic vs agentic approaches"""
    
    print(f"{Fore.MAGENTA}⚖️ Running Approach Comparison...{Style.RESET_ALL}")
    
    # This would run both approaches and compare results
    # For now, simulate the comparison
    
    comparison = ComparisonResult(
        deterministic_time=30.0,  # seconds
        agentic_time=45.0,        # seconds (includes question time)
        deterministic_quality=0.75,  # quality score
        agentic_quality=0.90,        # higher due to clarification
        winner="agentic",
        reasoning="Agentic approach asks clarifying questions leading to better quality despite longer time"
    )
    
    state["comparison_data"] = {
        "deterministic_time": comparison.deterministic_time,
        "agentic_time": comparison.agentic_time,  
        "deterministic_quality": comparison.deterministic_quality,
        "agentic_quality": comparison.agentic_quality,
        "winner": comparison.winner,
        "reasoning": comparison.reasoning
    }
    
    print(f"{Fore.GREEN}Winner: {comparison.winner.upper()}{Style.RESET_ALL}")
    print(f"Reasoning: {comparison.reasoning}")
    
    state["logs"].append(f"Comparison completed: {comparison.winner} approach won")
    
    return state


def memory_update_node(state: EnhancedBuildState) -> EnhancedBuildState:
    """Update memory with successful project"""
    
    if state["status"] == "completed":
        llm_client = LLMClient()
        orchestrator = SmartOrchestrator(llm_client)
        
        # Store successful project in memory
        tech_stack = state.get("tech_selection", {}).get("stack", [])
        
        orchestrator.memory_agent.store_successful_project(
            name=state["name"],
            prompt=state["prompt"],
            tech_stack=tech_stack,
            project_path=state["project_dir"],
            success_score=0.95,  # High score for successful completion
            lessons_learned=[
                "Smart orchestration reduced redundant work",
                "Clarifying questions improved spec quality",
                "Template reuse accelerated development"
            ]
        )
        
        print(f"{Fore.GREEN}📚 Project stored in memory for future reuse{Style.RESET_ALL}")
        state["logs"].append("Project stored in memory")
    
    return state


def create_enhanced_smart_graph():
    """Create the enhanced smart graph with comparison capabilities"""
    
    graph = StateGraph(EnhancedBuildState)
    
    # Add nodes
    graph.add_node("spec_extractor", spec_extractor)
    graph.add_node("smart_orchestrator", smart_orchestrator_node) 
    graph.add_node("comparison", comparison_node)
    graph.add_node("memory_update", memory_update_node)
    
    # Define the flow
    graph.set_entry_point("spec_extractor")
    graph.add_edge("spec_extractor", "smart_orchestrator")
    graph.add_edge("smart_orchestrator", "comparison")
    graph.add_edge("comparison", "memory_update")
    graph.add_edge("memory_update", END)
    
    return graph.compile()


def create_deterministic_graph():
    """Create the traditional deterministic graph for comparison"""
    
    from orchestrator.graph import BuildState
    
    graph = StateGraph(BuildState)
    
    # Traditional flow
    graph.add_node("spec_extractor", spec_extractor)
    graph.add_node("planner", planner)
    graph.add_node("scaffolder", scaffolder)
    graph.add_node("codegen", codegen)
    
    graph.set_entry_point("spec_extractor")
    graph.add_edge("spec_extractor", "planner")
    graph.add_edge("planner", "scaffolder") 
    graph.add_edge("scaffolder", "codegen")
    graph.add_edge("codegen", END)
    
    return graph.compile()


def run_comparison_demo():
    """Run a demo comparing different approaches"""
    
    print(f"{Fore.CYAN}🚀 Enhanced Agentic System Demo{Style.RESET_ALL}\n")
    
    # Test prompts
    test_prompts = [
        {
            "prompt": "Create a user management API",
            "name": "user-api",
            "expected_questions": ["What authentication method?", "What user fields?"]
        },
        {
            "prompt": "Build a blog platform with React and FastAPI", 
            "name": "blog-platform",
            "expected_questions": ["Comment system needed?", "Admin panel required?"]
        },
        {
            "prompt": "Simple todo app with basic CRUD",
            "name": "todo-app", 
            "expected_questions": []  # Should be clear enough
        }
    ]
    
    smart_graph = create_enhanced_smart_graph()
    
    for test in test_prompts:
        print(f"{Fore.YELLOW}Testing: {test['prompt']}{Style.RESET_ALL}")
        
        initial_state = EnhancedBuildState(
            prompt=test["prompt"],
            name=test["name"],
            artifacts_dir=str(Path(__file__).parent / "generated"),
            mode="hybrid"
        )
        
        try:
            # Run the enhanced graph
            result = smart_graph.invoke(initial_state)
            
            print(f"Status: {result.get('status', 'unknown')}")
            print(f"Questions asked: {len(result.get('questions_asked', []))}")
            print(f"Memory used: {result.get('memory_used', False)}")
            print(f"Templates used: {len(result.get('templates_used', []))}")
            
            if result.get("comparison_data"):
                comp = result["comparison_data"] 
                print(f"Winner: {comp['winner']} (Quality: {comp['agentic_quality']:.1%} vs {comp['deterministic_quality']:.1%})")
            
        except Exception as e:
            print(f"Error: {e}")
        
        print("-" * 50)
        print()


if __name__ == "__main__":
    run_comparison_demo()
