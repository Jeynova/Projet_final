#!/usr/bin/env python3
"""
Extract and save generated files from the Super-LLM system
"""
import os
import json
from pathlib import Path

def extract_and_save_files():
    """Extract files from the last pipeline run and save to gen2_files/"""
    
    # Create output directory
    output_dir = Path("gen2_files")
    output_dir.mkdir(exist_ok=True)
    
    print("🔍 Looking for generated files from last pipeline run...")
    
    # Try to find the storage files
    storage_files = [
        "agentforge_projects.json",
        "test_data.json", 
        "project_data.json"
    ]
    
    found_files = False
    
    for storage_file in storage_files:
        if os.path.exists(storage_file):
            print(f"📁 Found storage: {storage_file}")
            try:
                with open(storage_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Extract generated code
                if isinstance(data, dict) and 'generated_code' in data:
                    files = data['generated_code']
                    print(f"📄 Found {len(files)} generated files")
                    
                    for filename, content in files.items():
                        if isinstance(content, str) and content.strip():
                            file_path = output_dir / filename
                            file_path.parent.mkdir(parents=True, exist_ok=True)
                            
                            with open(file_path, 'w', encoding='utf-8') as f:
                                f.write(content)
                            print(f"✅ Saved: {filename} ({len(content)} chars)")
                            found_files = True
                
                # Extract other info
                validation = data.get('validation', {})
                if validation:
                    info_file = output_dir / "project_info.json"
                    with open(info_file, 'w', encoding='utf-8') as f:
                        json.dump({
                            'validation_score': data.get('best_validation_score'),
                            'architecture': data.get('architecture'),
                            'tech_stack': data.get('tech_stack'),
                            'validation_details': validation
                        }, f, indent=2)
                    print(f"📊 Saved project info")
                    
            except Exception as e:
                print(f"⚠️ Error reading {storage_file}: {e}")
    
    if not found_files:
        print("❌ No generated files found in storage")
        print("💡 Try running the pipeline first with real LLM calls")
        return False
    
    print(f"\n✅ Files extracted to: {output_dir.absolute()}")
    return True

if __name__ == "__main__":
    extract_and_save_files()
