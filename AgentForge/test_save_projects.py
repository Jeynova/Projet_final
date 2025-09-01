#!/usr/bin/env python3
"""
🎭 Test organic intelligence and SAVE the generated projects
"""
import sys
import os
import tempfile
from pathlib import Path

sys.path.append('.')
from phase2_pure_intelligence import PureIntelligenceOrchestrator

def test_and_save_projects():
    """Test organic intelligence and save generated projects to disk"""
    orchestrator = PureIntelligenceOrchestrator()
    
    test_prompts = [
        ("blog-platform", "Create a simple blog platform for a small business"),
        ("realtime-chat", "Build a real-time chat application"), 
        ("analytics-api", "Develop a high-performance API for data analytics")
    ]
    
    print("🎭 TESTING ORGANIC INTELLIGENCE + SAVING PROJECTS")
    print("=" * 60)
    
    generated_projects = []
    
    for project_name, prompt in test_prompts:
        print(f"\n🔬 GENERATING: {prompt}")
        print("-" * 40)
        
        # Run the organic intelligence pipeline
        state = orchestrator.run_pipeline(prompt)
        
        # Show the team's organic tech choices
        tech_stack = state.get('tech_stack', [])
        print(f"\n🎭 TEAM'S ORGANIC TECH CHOICES:")
        for tech in tech_stack:
            print(f"   {tech.get('role', 'unknown')}: {tech.get('name', 'Unknown')}")
        
        # Save the generated project to disk
        generated_code = state.get('generated_code', {})
        if generated_code and generated_code.get('files'):
            print(f"\n💾 SAVING PROJECT: {project_name}")
            
            # Create project directory
            output_dir = Path("generated") / f"organic-{project_name}"
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Save all generated files
            files = generated_code.get('files', {})
            saved_files = []
            
            for filename, content in files.items():
                file_path = output_dir / filename
                file_path.parent.mkdir(parents=True, exist_ok=True)
                
                try:
                    file_path.write_text(content, encoding='utf-8')
                    saved_files.append(filename)
                    print(f"   📄 {filename}")
                except Exception as e:
                    print(f"   ❌ Failed to save {filename}: {e}")
            
            # Save project summary
            summary = {
                "prompt": prompt,
                "tech_stack": tech_stack,
                "architecture": state.get('architecture', {}),
                "validation": state.get('validation', {}),
                "evaluation": state.get('evaluation', {}),
                "setup_instructions": generated_code.get('setup_instructions', []),
                "run_commands": generated_code.get('run_commands', [])
            }
            
            summary_path = output_dir / "PROJECT_SUMMARY.md"
            summary_content = f"""# {project_name.replace('-', ' ').title()}

## Original Request
{prompt}

## Team's Technology Choices
{chr(10).join([f"- **{tech.get('role', 'unknown').title()}**: {tech.get('name', 'Unknown')}" for tech in tech_stack])}

## Architecture
{state.get('architecture', {}).get('data_flow', 'Not specified')}

## Setup Instructions
{chr(10).join([f"{i+1}. {step}" for i, step in enumerate(generated_code.get('setup_instructions', []))])}

## Run Commands
```bash
{chr(10).join(generated_code.get('run_commands', []))}
```

## Evaluation Results
- Overall Score: {state.get('evaluation', {}).get('overall_score', 'N/A')}/10
- Technology Fit: {state.get('evaluation', {}).get('technology_fit', 'N/A')}/10
- Code Quality: {state.get('evaluation', {}).get('code_quality', 'N/A')}/10

## Generated Files
{chr(10).join([f"- {filename}" for filename in saved_files])}
"""
            
            summary_path.write_text(summary_content, encoding='utf-8')
            print(f"   📋 PROJECT_SUMMARY.md")
            
            generated_projects.append({
                "name": project_name,
                "path": str(output_dir),
                "files_count": len(saved_files),
                "tech_stack": tech_stack
            })
            
            print(f"   ✅ Saved to: {output_dir}")
        else:
            print(f"   ❌ No files generated for {project_name}")
        
        print("\n" + "=" * 60)
    
    # Summary of all generated projects
    print(f"\n🎉 GENERATED {len(generated_projects)} PROJECTS:")
    for project in generated_projects:
        print(f"   📁 {project['name']}: {project['files_count']} files in {project['path']}")
        backend = next((t for t in project['tech_stack'] if t.get('role') == 'backend'), {})
        if backend:
            print(f"      🖥️ Backend: {backend.get('name', 'Unknown')}")

if __name__ == "__main__":
    test_and_save_projects()
