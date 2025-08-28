"""
Enhanced Agentic System Demo
Shows the intelligent decision-making capabilities
"""

import os
import sys
from pathlib import Path
from colorama import Fore, Style, init

# Initialize colorama
init()

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from orchestrator.smart_orchestrator import SmartOrchestrator, Mode
    from orchestrator.memory_agent import MemoryAgent
    from core.llm_client import LLMClient
except ImportError as e:
    print(f"{Fore.RED}Import error: {e}{Style.RESET_ALL}")
    print("Please ensure you're running from the AgentForge directory")
    sys.exit(1)


def demo_memory_intelligence():
    """Demo: Memory agent avoiding redundant work"""
    
    print(f"{Fore.CYAN}🧠 Demo 1: Memory-Based Intelligence{Style.RESET_ALL}")
    print("Scenario: Building similar projects should reuse successful patterns")
    print()
    
    llm_client = LLMClient()
    memory_agent = MemoryAgent(llm_client)
    
    # Simulate storing a successful project
    print("📚 Storing successful project...")
    memory_agent.store_successful_project(
        name="user-management-api",
        prompt="Create a REST API for user management with authentication",
        tech_stack=["fastapi", "postgresql", "jwt"],
        project_path="/projects/user-api",
        success_score=0.95,
        lessons_learned=["JWT auth works well", "Async endpoints are fast", "Postgres handles concurrency"]
    )
    
    # Now test similar request
    print("🔍 Testing similar request...")
    similar_prompt = "Build a user management REST API with login"
    result = memory_agent.find_similar_projects(similar_prompt, ["fastapi", "auth"])
    
    print(f"Similarity confidence: {result.get('confidence', 0):.1%}")
    if result.get('confidence', 0) > 0.5:
        print(f"{Fore.GREEN}✅ Found similar project: {result.get('project_name')}{Style.RESET_ALL}")
        print(f"Recommended tech: {result.get('tech_stack')}")
        print("🚀 Can skip tech selection and use proven pattern!")
    else:
        print(f"{Fore.YELLOW}⚠️ No strong match found, need full analysis{Style.RESET_ALL}")
    
    print()


def demo_smart_questioning():
    """Demo: Asking clarifying questions when specs are unclear"""
    
    print(f"{Fore.CYAN}🤔 Demo 2: Smart Question Asking{Style.RESET_ALL}")
    print("Scenario: Unclear specs should trigger targeted questions")
    print()
    
    llm_client = LLMClient()
    orchestrator = SmartOrchestrator(llm_client)
    
    # Test with vague spec
    vague_spec = {
        "purpose": "Some kind of web app"
    }
    
    print("📝 Analyzing vague specification...")
    completeness = orchestrator._evaluate_spec_completeness(vague_spec)
    
    print(f"Completeness score: {completeness['score']:.1%}")
    print(f"Missing areas: {completeness['missing_areas']}")
    
    if completeness['score'] < 0.7:
        print(f"{Fore.YELLOW}❓ Generating clarifying questions...{Style.RESET_ALL}")
        questions = orchestrator.spec_refiner.generate_questions(vague_spec, completeness['missing_areas'])
        
        for i, question in enumerate(questions, 1):
            print(f"  Q{i}: {question}")
        
        print(f"{Fore.GREEN}✅ Questions will improve spec quality before coding{Style.RESET_ALL}")
    
    print()


def demo_tech_validation():
    """Demo: Validating tech choices against requirements"""
    
    print(f"{Fore.CYAN}🔧 Demo 3: Smart Tech Validation{Style.RESET_ALL}")
    print("Scenario: Tech choices should match project needs")
    print()
    
    llm_client = LLMClient()
    orchestrator = SmartOrchestrator(llm_client)
    
    # Test over-engineering
    test_cases = [
        {
            "name": "Over-engineered simple app",
            "tech_selection": {
                "stack": ["react", "django", "postgresql", "redis"],
                "confidence": 0.8,
                "reasoning": "Full-featured modern stack"
            },
            "spec": {"purpose": "Simple todo list"},
            "prompt": "create a simple todo list prototype"
        },
        {
            "name": "Under-engineered production app",
            "tech_selection": {
                "stack": ["flask", "sqlite"],
                "confidence": 0.6, 
                "reasoning": "Lightweight and simple"
            },
            "spec": {"purpose": "Production e-commerce platform"},
            "prompt": "build production-ready e-commerce platform for 10000+ users"
        }
    ]
    
    for test_case in test_cases:
        print(f"🧪 Testing: {test_case['name']}")
        
        validation = orchestrator.tech_validator.validate_selection(
            test_case["tech_selection"],
            test_case["spec"],
            test_case["prompt"]
        )
        
        if validation.valid:
            print(f"{Fore.GREEN}✅ Tech selection validated{Style.RESET_ALL}")
        else:
            print(f"{Fore.RED}❌ Issues found: {validation.issues[0] if validation.issues else 'Unknown'}{Style.RESET_ALL}")
            if validation.suggested_alternative:
                print(f"💡 Suggested alternative: {validation.suggested_alternative.get('stack')}")
        
        print()


def demo_hybrid_approach():
    """Demo: Choosing between templates, agents, and hybrid"""
    
    print(f"{Fore.CYAN}⚖️ Demo 4: Hybrid Approach Decision{Style.RESET_ALL}")
    print("Scenario: System chooses best approach based on template coverage")
    print()
    
    llm_client = LLMClient()
    orchestrator = SmartOrchestrator(llm_client)
    
    test_scenarios = [
        {
            "name": "High template coverage",
            "tech_stack": ["fastapi", "sqlite"],  # Assume we have templates
            "expected": "use_templates"
        },
        {
            "name": "No template coverage", 
            "tech_stack": ["unknown_framework", "exotic_db"],
            "expected": "agent_generate"
        },
        {
            "name": "Partial coverage",
            "tech_stack": ["fastapi", "exotic_db"],  # Mixed
            "expected": "hybrid_generate"
        }
    ]
    
    for scenario in test_scenarios:
        print(f"🎯 Scenario: {scenario['name']}")
        
        # Mock state
        state = {
            "tech_selection": {"stack": scenario["tech_stack"]},
            "spec": {"purpose": "Test application"}
        }
        
        decision = orchestrator._decide_codegen_strategy(state)
        
        print(f"Decision: {decision.action}")
        print(f"Confidence: {decision.confidence:.2f}")
        print(f"Reasoning: {decision.reasoning}")
        
        if decision.action == scenario["expected"]:
            print(f"{Fore.GREEN}✅ Expected decision made{Style.RESET_ALL}")
        else:
            print(f"{Fore.YELLOW}⚠️ Unexpected decision (expected {scenario['expected']}){Style.RESET_ALL}")
        
        print()


def demo_comparison_summary():
    """Show comparison between approaches"""
    
    print(f"{Fore.CYAN}📊 Enhanced vs Traditional Comparison{Style.RESET_ALL}")
    print()
    
    comparison_data = {
        "Traditional (Deterministic)": {
            "pros": [
                "Fast and predictable",
                "Simple to understand", 
                "Consistent results"
            ],
            "cons": [
                "No intelligence or adaptation",
                "May miss optimal solutions",
                "Redundant work"
            ],
            "use_cases": ["Simple, well-defined projects", "Rapid prototyping"]
        },
        "Enhanced (Agentic)": {
            "pros": [
                "Intelligent decision making",
                "Asks clarifying questions",
                "Avoids redundant work",
                "Learns from history"
            ],
            "cons": [
                "Slower due to analysis",
                "More complex system",
                "Requires user interaction"
            ],
            "use_cases": ["Complex projects", "Unclear requirements", "Learning from patterns"]
        }
    }
    
    for approach, details in comparison_data.items():
        print(f"{Fore.YELLOW}{approach}:{Style.RESET_ALL}")
        print(f"  {Fore.GREEN}Pros:{Style.RESET_ALL}")
        for pro in details["pros"]:
            print(f"    ✅ {pro}")
        print(f"  {Fore.RED}Cons:{Style.RESET_ALL}")
        for con in details["cons"]:
            print(f"    ❌ {con}")
        print(f"  {Fore.CYAN}Best for:{Style.RESET_ALL}")
        for use_case in details["use_cases"]:
            print(f"    🎯 {use_case}")
        print()
    
    print(f"{Fore.MAGENTA}💡 Key Insight: Use hybrid approach - templates for speed, agents for intelligence{Style.RESET_ALL}")


def main():
    """Run the enhanced agentic demo"""
    
    print(f"{Fore.CYAN}🚀 Enhanced Agentic System Demo{Style.RESET_ALL}")
    print(f"{Fore.CYAN}======================================{Style.RESET_ALL}")
    print()
    
    try:
        demo_memory_intelligence()
        demo_smart_questioning() 
        demo_tech_validation()
        demo_hybrid_approach()
        demo_comparison_summary()
        
        print(f"{Fore.GREEN}✅ Demo completed successfully!{Style.RESET_ALL}")
        print()
        print(f"{Fore.CYAN}Next steps:{Style.RESET_ALL}")
        print("1. Run setup: scripts/setup-enhanced-agentic.ps1 -Enhanced")
        print("2. Test system: python test_enhanced_agentic.py") 
        print("3. Build a project with smart orchestration!")
        
    except Exception as e:
        print(f"{Fore.RED}❌ Demo failed: {e}{Style.RESET_ALL}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
