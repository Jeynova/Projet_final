#!/usr/bin/env python3
"""
Test script to verify the Enhanced Super-LLM system with real Ollama calls
"""
import os
import time
from orchestrators.pipeline import PureIntelligenceOrchestrator

def test_enhanced_system():
    print("🧪 TESTING ENHANCED SUPER-LLM SYSTEM")
    print("=" * 50)
    
    # Set environment to use Ollama
    os.environ['AGENTFORGE_LLM'] = 'ollama'
    print(f"✅ AGENTFORGE_LLM = {os.getenv('AGENTFORGE_LLM')}")
    
    # Initialize orchestrator
    orchestrator = PureIntelligenceOrchestrator()
    
    # Simple test prompt
    prompt = """Create a basic calculator web app with:
- HTML interface with buttons (0-9, +, -, *, /, =, C)
- JavaScript for calculations
- CSS for styling
- Error handling for division by zero"""
    
    print("\n🚀 Running pipeline with REAL LLM calls...")
    print("⏱️  This will take time as each agent calls specialized models:")
    print("   📐 LearningMemoryAgent → mistral:7b")
    print("   🏗️ ArchitectureAgent → mistral:7b") 
    print("   💾 CodeGenAgent → codellama:7b")
    print("   ✅ ValidateAgent → qwen2.5-coder:7b")
    
    start_time = time.time()
    result = orchestrator.run_pipeline(prompt)
    end_time = time.time()
    
    print(f"\n🎉 Pipeline completed in {end_time - start_time:.1f} seconds!")
    
    # Analyze results
    files = result.get('generated_code', {})
    validation_score = result.get('best_validation_score', 'N/A')
    
    print(f"📊 Results:")
    print(f"   📄 Files generated: {len(files)}")
    print(f"   🎯 Validation score: {validation_score}/10")
    
    # Show file contents
    if files:
        print(f"\n📋 Generated files:")
        for i, (filename, content) in enumerate(files.items()):
            if i < 3:  # Show first 3 files
                lines = len(content.split('\n')) if isinstance(content, str) else 0
                size = len(content) if isinstance(content, str) else 0
                print(f"   📄 {filename}: {lines} lines, {size} chars")
                
                # Show first few lines
                if isinstance(content, str) and content.strip():
                    content_lines = content.split('\n')[:3]
                    for line in content_lines:
                        print(f"      {line[:60]}{'...' if len(line) > 60 else ''}")
                    if lines > 3:
                        print(f"      ... ({lines-3} more lines)")
                print()
    
    return len(files) > 0 and validation_score != 'N/A'

if __name__ == "__main__":
    success = test_enhanced_system()
    if success:
        print("✅ SUCCESS: Enhanced Super-LLM system working with real LLM calls!")
    else:
        print("❌ FAILED: System not generating real content")
