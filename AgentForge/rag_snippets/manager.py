"""
🎯 Simple RAG Manager - MVP Implementation
Provides basic similarity matching for prompts and tech stacks
"""
import json
import os
from pathlib import Path
from typing import Dict, List, Any, Tuple
from datetime import datetime

class SimpleRAGStore:
    """Simple file-based RAG storage for prompt->tech mappings"""
    
    def __init__(self, storage_path: str = None):
        self.storage_path = Path(storage_path) if storage_path else Path(__file__).parent / "rag_data"
        self.storage_path.mkdir(exist_ok=True)
        
        self.prompt_tech_file = self.storage_path / "prompt_tech_mappings.json"
        self.templates_file = self.storage_path / "code_templates.json"
        self.experience_file = self.storage_path / "experience_patterns.json"
        
        # Load existing data
        self.prompt_tech_mappings = self._load_json(self.prompt_tech_file, [])
        self.code_templates = self._load_json(self.templates_file, {})
        self.experience_patterns = self._load_json(self.experience_file, {})
    
    def _load_json(self, file_path: Path, default):
        """Load JSON file or return default"""
        try:
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"⚠️ Failed to load {file_path}: {e}")
        return default
    
    def _save_json(self, file_path: Path, data):
        """Save data to JSON file"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"⚠️ Failed to save {file_path}: {e}")
    
    def find_similar_prompts(self, prompt: str, limit: int = 3) -> List[Dict[str, Any]]:
        """Find similar prompts using simple text similarity"""
        prompt_lower = prompt.lower()
        prompt_words = set(prompt_lower.split())
        
        similarities = []
        for entry in self.prompt_tech_mappings:
            stored_prompt = entry.get('prompt', '').lower()
            stored_words = set(stored_prompt.split())
            
            # Simple Jaccard similarity
            intersection = len(prompt_words & stored_words)
            union = len(prompt_words | stored_words)
            similarity = intersection / union if union > 0 else 0
            
            if similarity > 0.1:  # Minimum threshold
                similarities.append({
                    'similarity': similarity,
                    'prompt': entry.get('prompt', ''),
                    'tech_stack': entry.get('tech_stack', []),
                    'success_score': entry.get('success_score', 5),
                    'timestamp': entry.get('timestamp', '')
                })
        
        # Sort by similarity and return top results
        similarities.sort(key=lambda x: x['similarity'], reverse=True)
        return similarities[:limit]
    
    def store_prompt_tech_mapping(self, prompt: str, tech_stack: List[Dict], success_score: float = 5.0):
        """Store a prompt->tech_stack mapping with success score"""
        entry = {
            'prompt': prompt,
            'tech_stack': tech_stack,
            'success_score': success_score,
            'timestamp': datetime.now().isoformat()
        }
        
        self.prompt_tech_mappings.append(entry)
        
        # Keep only last 100 entries to prevent file bloat
        if len(self.prompt_tech_mappings) > 100:
            self.prompt_tech_mappings = self.prompt_tech_mappings[-100:]
        
        self._save_json(self.prompt_tech_file, self.prompt_tech_mappings)
        print(f"📚 Stored prompt mapping: {prompt[:30]}... → {len(tech_stack)} technologies")
    
    def get_tech_hints(self, prompt: str) -> List[str]:
        """Get technology hints based on similar prompts"""
        similar = self.find_similar_prompts(prompt)
        hints = []
        
        for match in similar:
            if match['success_score'] > 7.0:  # Only high-success projects
                for tech in match['tech_stack']:
                    hint = f"Similar project ({match['similarity']:.1%} match) used {tech.get('name', 'Unknown')} for {tech.get('role', 'unknown')}"
                    hints.append(hint)
        
        return hints[:5]  # Limit to 5 hints

class RAGSnippetManager:
    """Enhanced RAG manager with simple storage"""
    
    def __init__(self, storage_path: str = None):
        self.store = SimpleRAGStore(storage_path)
    
    def get_similar_projects(self, prompt: str) -> List[Dict]:
        """Get similar projects for tech guidance"""
        return self.store.find_similar_prompts(prompt)
    
    def store_project_outcome(self, prompt: str, tech_stack: List[Dict], success_score: float):
        """Store project outcome for future learning"""
        self.store.store_prompt_tech_mapping(prompt, tech_stack, success_score)
    
    def get_tech_suggestions(self, prompt: str) -> List[str]:
        """Get technology suggestions based on similar projects"""
        return self.store.get_tech_hints(prompt)
