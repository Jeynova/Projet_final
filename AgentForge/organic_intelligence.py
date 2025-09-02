#!/usr/bin/env python3
"""
🎭 ORGANIC INTELLIGENCE - MAIN ENTRY POINT
Clean modular entry point for the refactored system
"""

import sys
import os

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from orchestrators.pipeline import PureIntelligenceOrchestrator
from tests.test_pipeline import test_organic_intelligence


def main():
    """Main entry point for organic intelligence system"""
    if len(sys.argv) > 1:
        prompt = " ".join(sys.argv[1:])
        print(f"🎭 Running organic intelligence on: {prompt}")
        
        orchestrator = PureIntelligenceOrchestrator()
        result = orchestrator.run_pipeline(prompt)
        
        print(f"\n🎯 FINAL RESULT:")
        if 'tech_stack' in result:
            print("Technology Stack:")
            for tech in result['tech_stack']:
                print(f"  - {tech.get('role', '?')}: {tech.get('name', '?')}")
        
        if 'validation' in result:
            score = result['validation'].get('score', 0)
            status = result['validation'].get('status', 'unknown')
            print(f"Validation: {score}/10 ({status})")
            
    else:
        print("🧪 Running test suite...")
        test_organic_intelligence()


if __name__ == "__main__":
    main()
