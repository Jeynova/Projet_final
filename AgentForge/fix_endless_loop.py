#!/usr/bin/env python3
"""
Fix endless loop issue by adding goal_reached checks to all agents
"""
import os
import re
from pathlib import Path

def fix_agent_can_run(file_path):
    """Add goal_reached check to can_run method if not present"""
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Skip if already has goal_reached check
    if 'goal_reached' in content:
        print(f"✅ {file_path.name} already has goal_reached check")
        return False
        
    # Skip if no can_run method
    if 'def can_run(' not in content:
        print(f"⏭️ {file_path.name} has no can_run method")
        return False
    
    # Find can_run method and add goal_reached check
    pattern = r'(    def can_run\(self, state[^)]*\) -> bool:\n)'
    
    def replacement(match):
        return match.group(1) + '        # Don\'t run if quality goal has been reached\n        if state.get(\'goal_reached\', False):\n            return False\n            \n'
    
    new_content = re.sub(pattern, replacement, content)
    
    if new_content != content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"🔧 Fixed {file_path.name}")
        return True
    else:
        print(f"❌ Could not fix {file_path.name}")
        return False

def main():
    base_dir = Path(__file__).parent
    agents_dir = base_dir / 'agents'
    
    fixed_count = 0
    
    print("🔄 Fixing endless loop by adding goal_reached checks...")
    
    # Find all Python files in agents directory
    for py_file in agents_dir.rglob('*.py'):
        if py_file.name != '__init__.py':
            if fix_agent_can_run(py_file):
                fixed_count += 1
    
    print(f"\n✅ Fixed {fixed_count} agent files")
    print("🎯 The endless loop should now stop when quality goals are reached!")

if __name__ == '__main__':
    main()
