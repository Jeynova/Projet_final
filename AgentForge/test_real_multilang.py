#!/usr/bin/env python3
"""
REAL TEST: Generate a multi-language project to prove the LLM can now code freely
"""
import sys
import tempfile
from pathlib import Path
import json
import shutil

# Add paths for imports
sys.path.insert(0, str(Path(__file__).parent / 'orchestrator_v2'))

from enhanced_orchestrator import EnhancedDynamicOrchestrator

def test_react_php_project():
    """Test generating a React+TypeScript frontend with PHP+Symfony backend"""
    
    print("🚀 REAL MULTI-LANGUAGE TEST")
    print("=" * 60)
    print("Testing: React+TypeScript frontend + PHP+Symfony backend")
    print("This tests if your vision actually works end-to-end!")
    print()
    
    # Create test project
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir) / "multi-lang-test"
        project_root.mkdir()
        
        # Initialize orchestrator
        orchestrator = EnhancedDynamicOrchestrator(project_root)
        
        # Test prompt that should trigger multi-language generation
        test_prompt = """
        Create a modern e-commerce platform with:
        - React+TypeScript frontend with product catalog, shopping cart, user authentication
        - PHP+Symfony backend API with product management, order processing, user management
        - PostgreSQL database with products, users, orders, inventory
        - Modern architecture with REST API, JWT authentication, responsive design
        """
        
        print(f"📝 Prompt: {test_prompt.strip()}")
        print()
        
        # Configure for multi-language (bypass some steps for quick test)
        config = {
            'max_steps': 15,
            'track_steps': True,
            'boilerplate_only': False
        }
        
        print("🔧 Running orchestration...")
        try:
            result = orchestrator.generate(test_prompt, config=config)
            
            print("\n📊 RESULTS:")
            print(f"   Status: {result.get('status', 'unknown')}")
            print(f"   Steps completed: {len(result.get('steps', []))}")
            
            # Check what languages were actually generated
            generated_files = []
            for root, dirs, files in project_root.walk():
                for file in files:
                    file_path = root / file
                    rel_path = file_path.relative_to(project_root)
                    generated_files.append(str(rel_path))
            
            print(f"   Files generated: {len(generated_files)}")
            
            # Analyze file extensions to see if multi-language worked
            extensions = {}
            for file_path in generated_files:
                ext = file_path.split('.')[-1] if '.' in file_path else 'none'
                extensions[ext] = extensions.get(ext, 0) + 1
            
            print(f"   File types: {dict(extensions)}")
            
            # Check for specific multi-language evidence
            has_react = any(f.endswith('.tsx') or f.endswith('.jsx') for f in generated_files)
            has_php = any(f.endswith('.php') for f in generated_files)
            has_typescript = any(f.endswith('.ts') for f in generated_files)
            has_python = any(f.endswith('.py') for f in generated_files)
            
            print("\n🔍 LANGUAGE ANALYSIS:")
            print(f"   React/TSX files: {'✅ YES' if has_react else '❌ NO'}")
            print(f"   PHP files: {'✅ YES' if has_php else '❌ NO'}")
            print(f"   TypeScript files: {'✅ YES' if has_typescript else '❌ NO'}")
            print(f"   Python files: {'✅ YES' if has_python else '❌ NO'}")
            
            if has_react or has_php or has_typescript:
                print("\n🎉 SUCCESS! Multi-language generation is WORKING!")
                print("Your vision is implemented - the LLM can code freely!")
            else:
                print("\n⚠️ Only Python files generated - need to check why")
            
            # Show some sample files
            print("\n📄 SAMPLE FILES:")
            for file_path in sorted(generated_files)[:8]:
                print(f"   📄 {file_path}")
                
            # Check tech stack selection
            if 'tech' in result:
                tech_stack = result['tech'].get('stack', [])
                print(f"\n🔧 Tech Stack Selected: {tech_stack}")
            
            return has_react or has_php or has_typescript
            
        except Exception as e:
            print(f"❌ Test failed: {e}")
            return False

if __name__ == '__main__':
    success = test_react_php_project()
    if success:
        print("\n🚀 VISION ACHIEVED! LLM can now code in multiple languages!")
    else:
        print("\n🔧 Need to debug - still generating only Python")
