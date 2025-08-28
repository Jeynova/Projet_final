"""
Test script for the enhanced agentic system
Demonstrates the smart orchestrator making intelligent decisions
"""

import os
import sys
from pathlib import Path

# Add the current directory to the Python path
sys.path.insert(0, str(Path(__file__).parent))

from orchestrator.smart_orchestrator import SmartOrchestrator
from core.llm_client import LLMClient


def test_memory_based_decision():
    """Test that the orchestrator can skip agents based on memory"""
    
    print("🧪 Test 1: Memory-based decision making")
    
    # Mock LLM client
    llm_client = LLMClient()
    orchestrator = SmartOrchestrator(llm_client)
    
    # Test state
    state = {
        "prompt": "Create a simple REST API for user management with FastAPI",
        "name": "user-api", 
        "spec": {
            "purpose": "User management API",
            "features": "CRUD operations for users",
            "tech_hints": "FastAPI, SQLite"
        },
        "logs": []
    }
    
    # Check memory first
    memory_decision = orchestrator._check_memory_first(state["prompt"], state["spec"])
    
    print(f"Memory decision: {memory_decision.action}")
    print(f"Confidence: {memory_decision.confidence:.2f}")
    print(f"Reasoning: {memory_decision.reasoning}")
    
    if memory_decision.skip_reason:
        print(f"Skip reason: {memory_decision.skip_reason}")
        
    print()


def test_spec_refinement():
    """Test spec refinement and question asking"""
    
    print("🧪 Test 2: Spec refinement and question asking")
    
    llm_client = LLMClient()
    orchestrator = SmartOrchestrator(llm_client)
    
    # Incomplete spec
    incomplete_spec = {
        "purpose": "Some kind of web app"
    }
    
    completeness = orchestrator._evaluate_spec_completeness(incomplete_spec)
    print(f"Spec completeness score: {completeness['score']:.1%}")
    print(f"Missing areas: {completeness['missing_areas']}")
    
    # Generate questions
    questions = orchestrator.spec_refiner.generate_questions(
        incomplete_spec, 
        completeness["missing_areas"]
    )
    
    print(f"Generated {len(questions)} clarifying questions:")
    for i, question in enumerate(questions, 1):
        print(f"  Q{i}: {question}")
        
    print()


def test_tech_validation():
    """Test tech stack validation"""
    
    print("🧪 Test 3: Tech stack validation")
    
    llm_client = LLMClient()
    orchestrator = SmartOrchestrator(llm_client)
    
    # Test various tech combinations
    test_cases = [
        {
            "name": "Good combination",
            "tech_selection": {
                "stack": ["fastapi", "postgresql"],
                "confidence": 0.8,
                "reasoning": "Modern async API with robust database"
            },
            "spec": {"purpose": "Production API"},
            "prompt": "production-ready user management API"
        },
        {
            "name": "Overkill combination", 
            "tech_selection": {
                "stack": ["react", "django", "postgresql"],
                "confidence": 0.7,
                "reasoning": "Full-stack solution"
            },
            "spec": {"purpose": "Simple prototype"},
            "prompt": "simple prototype for user management"
        }
    ]
    
    for test_case in test_cases:
        print(f"Testing: {test_case['name']}")
        validation = orchestrator.tech_validator.validate_selection(
            test_case["tech_selection"],
            test_case["spec"], 
            test_case["prompt"]
        )
        
        print(f"  Valid: {validation.valid}")
        print(f"  Confidence: {validation.confidence:.2f}")
        print(f"  Reasoning: {validation.reasoning}")
        if validation.issues:
            print(f"  Issues: {validation.issues}")
        if validation.suggested_alternative:
            print(f"  Alternative: {validation.suggested_alternative}")
        print()


def test_template_coverage():
    """Test template coverage checking"""
    
    print("🧪 Test 4: Template coverage checking")
    
    llm_client = LLMClient()
    orchestrator = SmartOrchestrator(llm_client)
    
    test_stacks = [
        ["fastapi", "sqlite"],
        ["react", "fastapi", "postgresql"],
        ["unknown_framework", "exotic_db"]
    ]
    
    for stack in test_stacks:
        coverage_data = orchestrator._check_existing_templates(stack)
        coverage = coverage_data["coverage"]
        available = coverage_data["available_templates"]
        
        print(f"Stack: {stack}")
        print(f"  Coverage: {coverage:.1%}")
        print(f"  Available templates: {available}")
        print()


def test_codegen_strategy_decision():
    """Test code generation strategy decision"""
    
    print("🧪 Test 5: Code generation strategy decision")
    
    llm_client = LLMClient() 
    orchestrator = SmartOrchestrator(llm_client)
    
    test_states = [
        {
            "name": "High template coverage",
            "tech_selection": {"stack": ["fastapi", "sqlite"]},
            "spec": {"purpose": "Simple API"}
        },
        {
            "name": "Low template coverage",
            "tech_selection": {"stack": ["unknown_framework", "exotic_db"]}, 
            "spec": {"purpose": "Complex system"}
        }
    ]
    
    for state in test_states:
        print(f"Testing: {state['name']}")
        decision = orchestrator._decide_codegen_strategy(state)
        
        print(f"  Action: {decision.action}")
        print(f"  Confidence: {decision.confidence:.2f}")
        print(f"  Reasoning: {decision.reasoning}")
        print()


def main():
    """Run all tests"""
    
    print("🚀 Testing Enhanced Agentic System\n")
    
    # Set test environment
    os.environ["AGENTFORGE_AGENTIC"] = "1"
    os.environ["AGENTFORGE_ASK"] = "1" 
    os.environ["AGENTFORGE_MODE"] = "hybrid"
    
    test_memory_based_decision()
    test_spec_refinement()
    test_tech_validation()
    test_template_coverage()
    test_codegen_strategy_decision()
    
    print("✅ All tests completed!")


if __name__ == "__main__":
    main()
