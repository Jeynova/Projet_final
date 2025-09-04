#!/usr/bin/env python3
"""
🧪 PIPELINE TESTS
Local testing for the organic intelligence pipeline
"""

import sys
import os
sys.path.append('.')

from orchestrators.pipeline import PureIntelligenceOrchestrator


def test_organic_intelligence():
    """Test the organic intelligence pipeline with sample projects"""
    orch = PureIntelligenceOrchestrator()
    tests = [
        "Create a simple blog platform for a small business",
        "Build a real-time chat application",
        "Develop a task management system for teams with roles and due dates"
    ]
    
    print("🧪 TESTING ORGANIC MULTI-PERSPECTIVE INTELLIGENCE")
    print("="*60)
    
    for i, p in enumerate(tests, 1):
        print(f"\n🔬 TEST {i}: {p}")
        print("-"*40)
        
        state = orch.run_pipeline(p)
        tech_stack = state.get('tech_stack', [])
        
        print(f"\n🎭 TEAM'S ORGANIC CHOICES:")
        for t in tech_stack:
            print(f"   {t.get('role','?')}: {t.get('name','?')}")
        print("\n" + "="*60)


if __name__ == "__main__":
    test_organic_intelligence()
