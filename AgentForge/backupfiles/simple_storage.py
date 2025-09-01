#!/usr/bin/env python3
"""
Simple JSON-based storage for AgentForge projects
Replaces database functionality with persistent JSON storage
"""
import json
import os
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

class SimpleProjectStorage:
    """Simple JSON-based project storage"""
    
    def __init__(self, storage_file: str = "agentforge_projects.json"):
        self.storage_path = Path(storage_file)
        self.projects = self._load_projects()
    
    def _load_projects(self) -> List[Dict[str, Any]]:
        """Load projects from JSON file"""
        if self.storage_path.exists():
            try:
                with open(self.storage_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"⚠️ Failed to load projects: {e}")
                return []
        return []
    
    def _save_projects(self):
        """Save projects to JSON file"""
        try:
            with open(self.storage_path, 'w', encoding='utf-8') as f:
                json.dump(self.projects, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"⚠️ Failed to save projects: {e}")
    
    def save_project(self, prompt: str, results: Dict[str, Any]) -> str:
        """Save a project and return its ID"""
        project_id = f"project_{len(self.projects) + 1}_{int(datetime.now().timestamp())}"
        
        project = {
            'id': project_id,
            'name': f"organic_project_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            'prompt': prompt,
            'status': 'completed',
            'created_at': datetime.now().isoformat(),
            'tech_stack': results.get('tech_stack', []),
            'evaluation': results.get('evaluation', {}),
            'stats': {
                'files_generated': len(results.get('generated_code', {}).get('files', {})),
                'llm_calls': results.get('llm_calls', 0),
                'tech_choices': len(results.get('tech_stack', [])),
                'quality_score': results.get('validation', {}).get('score', 0)
            },
            'data': results
        }
        
        self.projects.append(project)
        
        # Keep only last 50 projects
        if len(self.projects) > 50:
            self.projects = self.projects[-50:]
        
        self._save_projects()
        print(f"✅ Project saved with ID: {project_id}")
        return project_id
    
    def get_projects(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent projects"""
        return sorted(self.projects, key=lambda p: p['created_at'], reverse=True)[:limit]
    
    def get_project(self, project_id: str) -> Dict[str, Any]:
        """Get specific project by ID"""
        for project in self.projects:
            if project['id'] == project_id:
                return project
        return None
    
    def clear_projects(self):
        """Clear all projects"""
        self.projects = []
        self._save_projects()
