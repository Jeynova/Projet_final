"""
Test script for the Simple Graph Pipeline
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

print('Testing Simple Graph Pipeline...')

try:
    from orchestrators.simple_graph_pipeline import SimpleGraphPipeline
    
    pipeline = SimpleGraphPipeline(
        save_folder='test_simple_graph',
        max_iterations=1,
        target_score=6.0
    )
    
    prompt = 'Create a simple task API with user auth'
    
    result = pipeline.run(prompt, project_name='GraphAPI')
    
    print('\n🎉 Graph Result:')
    print(f'  📊 Score: {result["best_validation_score"]}/10')
    print(f'  📄 Files: {len(result["generated_code"])}')
    print(f'  🔄 Iterations: {result["final_iteration_count"]}') 
    print(f'  🎯 Target achieved: {result["achieved_target"]}')
    print(f'  💾 Saved files: {result.get("saved_files_count", 0)}')
    
    if result.get('execution_path'):
        print(f'  🛤️ Path: {" → ".join(result["execution_path"][:8])}')
    
    if result['generated_code']:
        print('  📁 Sample files:')
        for i, (filename, content) in enumerate(list(result['generated_code'].items())[:3]):
            lines = len(content.split('\n')) if content else 0
            print(f'    {filename}: {lines} lines')
    
    print('\n✅ Simple Graph Pipeline test completed successfully!')

except Exception as e:
    print(f'❌ Error: {e}')
    import traceback
    traceback.print_exc()
