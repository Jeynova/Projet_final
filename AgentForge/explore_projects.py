#!/usr/bin/env python3
"""
🔍 AgentForge Project Explorer
Explore your saved organic intelligence projects
"""
import json
import zipfile
from pathlib import Path
from datetime import datetime

def explore_json_storage():
    """Show metadata from JSON storage"""
    storage_path = Path("projects_storage.json")
    if not storage_path.exists():
        print("❌ No projects_storage.json found")
        return
    
    with open(storage_path, 'r', encoding='utf-8') as f:
        projects = json.load(f)
    
    print(f"📊 Found {len(projects)} projects in JSON storage:")
    print("=" * 80)
    
    for i, proj in enumerate(projects[-10:], 1):  # Show last 10
        print(f"\n🎯 Project {i}: {proj.get('name', 'Unknown')}")
        print(f"   📝 Prompt: {proj.get('prompt', '')[:60]}...")
        print(f"   📅 Created: {proj.get('created_at', '')}")
        print(f"   📊 Quality Score: {proj.get('stats', {}).get('quality_score', 'N/A')}/10")
        
        tech_stack = proj.get('tech_stack', [])
        if tech_stack:
            print(f"   🛠️ Tech Stack:")
            for tech in tech_stack[:4]:  # Show first 4
                print(f"      {tech.get('role', '?')}: {tech.get('name', '?')}")
        
        # Check if files exist
        data = proj.get('data', {})
        files = data.get('generated_code', {}).get('files', {})
        if files:
            print(f"   📁 Generated Files: {len(files)} files")
            for fname in list(files.keys())[:3]:
                print(f"      📄 {fname}")

def explore_generated_zips():
    """Show available ZIP downloads"""
    generated_path = Path("generated")
    if not generated_path.exists():
        print("❌ No generated/ folder found")
        return
    
    zip_files = list(generated_path.glob("organic_project_*.zip"))
    print(f"\n📦 Found {len(zip_files)} organic intelligence ZIP files:")
    print("=" * 80)
    
    for zip_path in sorted(zip_files, key=lambda x: x.stat().st_mtime, reverse=True):
        timestamp = datetime.fromtimestamp(zip_path.stat().st_mtime)
        size_kb = zip_path.stat().st_size / 1024
        
        print(f"\n📦 {zip_path.name}")
        print(f"   📅 Created: {timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"   💾 Size: {size_kb:.1f} KB")
        
        # Peek inside the ZIP
        try:
            with zipfile.ZipFile(zip_path, 'r') as zf:
                files = zf.namelist()
                print(f"   📁 Contains {len(files)} files:")
                for fname in files[:5]:  # Show first 5
                    print(f"      📄 {fname}")
                if len(files) > 5:
                    print(f"      ... and {len(files) - 5} more files")
        except Exception as e:
            print(f"   ⚠️ Error reading ZIP: {e}")

def extract_latest_project():
    """Extract the latest organic project for exploration"""
    generated_path = Path("generated")
    zip_files = list(generated_path.glob("organic_project_*.zip"))
    
    if not zip_files:
        print("❌ No organic project ZIP files found")
        return
    
    latest_zip = max(zip_files, key=lambda x: x.stat().st_mtime)
    extract_path = Path("extracted_projects") / latest_zip.stem
    extract_path.mkdir(parents=True, exist_ok=True)
    
    print(f"📂 Extracting latest project: {latest_zip.name}")
    print(f"   📁 To: {extract_path}")
    
    with zipfile.ZipFile(latest_zip, 'r') as zf:
        zf.extractall(extract_path)
    
    print(f"✅ Extracted! You can now explore: {extract_path}")
    return extract_path

if __name__ == "__main__":
    print("🔍 AGENTFORGE PROJECT EXPLORER")
    print("=" * 50)
    
    explore_json_storage()
    explore_generated_zips()
    
    print("\n" + "=" * 50)
    choice = input("Extract latest project for exploration? (y/n): ").lower()
    if choice == 'y':
        extract_latest_project()
