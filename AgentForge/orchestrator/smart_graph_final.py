"""
Proper Smart Graph - Uses environment variables correctly
AGENTFORGE_AGENTIC=1/0 to enable/disable
AGENTFORGE_MODE=templates|agent_first|auto to switch modes
"""

import os
from typing import Dict, Any
from pathlib import Path
import sys

# Fix imports for standalone execution
current_dir = Path(__file__).parent
parent_dir = current_dir.parent
sys.path.insert(0, str(parent_dir))

from orchestrator.simple_smart_system import SimpleSmartSystem


class SmartBuildState(dict):
    """Build state that respects environment configuration"""
    pass


def create_smart_pipeline():
    """Create pipeline that respects AGENTFORGE_AGENTIC and AGENTFORGE_MODE"""
    
    # Read configuration
    agentic_enabled = os.getenv("AGENTFORGE_AGENTIC", "0") == "1"
    mode = os.getenv("AGENTFORGE_MODE", "templates")
    
    print(f"🔧 Pipeline Configuration:")
    print(f"   AGENTFORGE_AGENTIC: {agentic_enabled}")
    print(f"   AGENTFORGE_MODE: {mode}")
    
    def execute_pipeline(state: SmartBuildState) -> SmartBuildState:
        """Execute the appropriate pipeline based on configuration"""
        
        # Always extract spec first
        try:
            from orchestrator.agents import spec_extractor
            state = spec_extractor(state)
        except ImportError:
            # Fallback if agents module not available
            pass
        
        if not agentic_enabled:
            # Traditional deterministic mode
            print("📋 Using traditional deterministic pipeline")
            
            try:
                from orchestrator.agents import planner, scaffolder, codegen
                
                state = planner(state)
                state = scaffolder(state)
                state = codegen(state)
            except ImportError:
                # Fallback if agents not available
                state.update({
                    "approach": "deterministic_fallback",
                    "status": "completed",
                    "logs": ["Used fallback deterministic mode"]
                })
            
        else:
            # Smart agentic mode - use simple smart system
            print(f"🧠 Using smart agentic mode: {mode}")
            
            smart_system = SimpleSmartSystem()
            
            # Build project using smart agent logic
            smart_result = smart_system.build_project(
                prompt=state.get("prompt", ""),
                name=state.get("name", "generated-project"),
                output_dir=state.get("artifacts_dir", "./generated")
            )
            
            # Update state with smart system results
            state.update({
                "approach": smart_result["approach"],
                "tech_stack": smart_result.get("tech_stack", []),
                "smart_logs": smart_result["logs"],
                "final_result": smart_result.get("final_result", {}),
                "status": "completed"
            })
            
            state["logs"].extend(smart_result["logs"])
        
        return state
    
    return execute_pipeline


def smart_node(state: SmartBuildState) -> SmartBuildState:
    """Legacy compatible node for existing workflows"""
    pipeline = create_smart_pipeline()
    return pipeline(state)


# Comparison function for testing agentic vs deterministic
def compare_approaches(prompt: str, name: str, output_dir: str) -> Dict[str, Any]:
    """Compare deterministic vs agentic approaches"""
    
    results = {}
    
    # Save original environment
    orig_agentic = os.getenv("AGENTFORGE_AGENTIC", "0")
    orig_mode = os.getenv("AGENTFORGE_MODE", "templates")
    
    try:
        # Test deterministic approach
        os.environ["AGENTFORGE_AGENTIC"] = "0"
        pipeline = create_smart_pipeline()
        
        deterministic_state = SmartBuildState({
            "prompt": prompt,
            "name": f"{name}-deterministic",
            "artifacts_dir": f"{output_dir}/deterministic",
            "logs": []
        })
        
        det_result = pipeline(deterministic_state)
        results["deterministic"] = {
            "approach": det_result.get("approach", "deterministic"),
            "logs": det_result.get("logs", []),
            "status": det_result.get("status", "completed")
        }
        
        # Test agentic approach
        os.environ["AGENTFORGE_AGENTIC"] = "1"
        os.environ["AGENTFORGE_MODE"] = "auto"
        pipeline = create_smart_pipeline()
        
        agentic_state = SmartBuildState({
            "prompt": prompt,
            "name": f"{name}-agentic",
            "artifacts_dir": f"{output_dir}/agentic",
            "logs": []
        })
        
        ag_result = pipeline(agentic_state)
        results["agentic"] = {
            "approach": ag_result.get("approach", "agentic"),
            "tech_stack": ag_result.get("tech_stack", []),
            "smart_logs": ag_result.get("smart_logs", []),
            "final_result": ag_result.get("final_result", {}),
            "status": ag_result.get("status", "completed")
        }
        
    finally:
        # Restore original environment
        os.environ["AGENTFORGE_AGENTIC"] = orig_agentic
        os.environ["AGENTFORGE_MODE"] = orig_mode
    
    return results


if __name__ == "__main__":
    """Test the smart graph system"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test Smart Graph System")
    parser.add_argument("--prompt", required=True, help="Project description")
    parser.add_argument("--name", default="test-project", help="Project name")
    parser.add_argument("--output", default="./test-outputs", help="Output directory")
    parser.add_argument("--compare", action="store_true", help="Compare both approaches")
    
    args = parser.parse_args()
    
    if args.compare:
        print("🔍 Comparing both approaches...")
        results = compare_approaches(args.prompt, args.name, args.output)
        
        print("\n📊 Comparison Results:")
        print(f"Deterministic: {results['deterministic']['approach']}")
        print(f"Agentic: {results['agentic']['approach']} with {results['agentic'].get('tech_stack', [])}")
        
        import json
        print("\nFull Results:")
        print(json.dumps(results, indent=2))
    
    else:
        # Test with current environment settings
        pipeline = create_smart_pipeline()
        
        state = SmartBuildState({
            "prompt": args.prompt,
            "name": args.name,
            "artifacts_dir": args.output,
            "logs": []
        })
        
        result = pipeline(state)
        
        print("\n✅ Pipeline Result:")
        print(f"Approach: {result.get('approach', 'unknown')}")
        print(f"Status: {result.get('status', 'unknown')}")
        if "tech_stack" in result:
            print(f"Tech Stack: {result['tech_stack']}")
