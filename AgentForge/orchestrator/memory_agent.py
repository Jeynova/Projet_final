"""
Memory Agent - Retrieves preferences and historical success patterns
Uses RAG to find similar projects and successful patterns
"""

import json
import os
from typing import Dict, Any, List, Optional
from pathlib import Path
from dataclasses import dataclass
from datetime import datetime

from core.llm_client import LLMClient


@dataclass 
class ProjectMemory:
    """Represents a successful project in memory"""
    name: str
    prompt: str
    tech_stack: List[str]
    success_score: float
    created_at: datetime
    project_path: Optional[str] = None
    lessons_learned: List[str] = None


class MemoryAgent:
    """
    Manages project memory and preferences
    - Stores successful project patterns
    - Retrieves similar projects for reuse
    - Updates preferences based on success/failure
    """
    
    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client
        self.memory_file = Path(__file__).parent.parent / "agentforge.db.json"
        self._load_memory()
        
    def _load_memory(self):
        """Load project memories from storage"""
        if self.memory_file.exists():
            with open(self.memory_file, 'r') as f:
                data = json.load(f)
                self.projects = []
                for p in data.get("projects", []):
                    # Convert created_at string back to datetime
                    if isinstance(p.get("created_at"), str):
                        try:
                            p["created_at"] = datetime.fromisoformat(p["created_at"])
                        except:
                            p["created_at"] = datetime.now()
                    self.projects.append(ProjectMemory(**p))
                self.preferences = data.get("preferences", {})
        else:
            self.projects = []
            self.preferences = {}
    
    def _save_memory(self):
        """Save memories to storage"""
        data = {
            "projects": [
                {
                    "name": p.name,
                    "prompt": p.prompt, 
                    "tech_stack": p.tech_stack,
                    "success_score": p.success_score,
                    "created_at": p.created_at.isoformat() if hasattr(p.created_at, 'isoformat') else str(p.created_at),
                    "project_path": p.project_path,
                    "lessons_learned": p.lessons_learned or []
                }
                for p in self.projects
            ],
            "preferences": self.preferences
        }
        
        self.memory_file.parent.mkdir(exist_ok=True)
        with open(self.memory_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def find_similar_projects(self, prompt: str, tech_requirements: List[str]) -> Dict[str, Any]:
        """Find projects similar to the current request"""
        
        if not self.projects:
            return {"confidence": 0.0, "matches": []}
        
        # Simple similarity scoring (in practice, would use embeddings)
        matches = []
        for project in self.projects:
            similarity_score = self._calculate_similarity(prompt, tech_requirements, project)
            if similarity_score > 0.5:  # Threshold for relevance
                matches.append({
                    "project": project,
                    "similarity": similarity_score,
                    "success_score": project.success_score
                })
        
        # Sort by combined similarity and success
        matches.sort(key=lambda x: x["similarity"] * x["success_score"], reverse=True)
        
        if matches:
            best_match = matches[0]
            return {
                "confidence": best_match["similarity"] * best_match["success_score"],
                "project_name": best_match["project"].name,
                "project_path": best_match["project"].project_path,
                "tech_stack": best_match["project"].tech_stack,
                "lessons_learned": best_match["project"].lessons_learned,
                "all_matches": matches[:3]  # Top 3 matches
            }
        
        return {"confidence": 0.0, "matches": []}
    
    def _calculate_similarity(self, prompt: str, tech_requirements: List[str], project: ProjectMemory) -> float:
        """Calculate similarity between current request and stored project"""
        
        # Text similarity (simplified - would use embeddings in practice)
        prompt_words = set(prompt.lower().split())
        project_words = set(project.prompt.lower().split())
        text_similarity = len(prompt_words & project_words) / len(prompt_words | project_words)
        
        # Tech stack similarity
        tech_overlap = len(set(tech_requirements) & set(project.tech_stack))
        tech_similarity = tech_overlap / max(len(tech_requirements), len(project.tech_stack), 1)
        
        # Weight text more than tech (assuming prompt describes intent better)
        return 0.6 * text_similarity + 0.4 * tech_similarity
    
    def store_successful_project(self, name: str, prompt: str, tech_stack: List[str], 
                               project_path: str, success_score: float = 1.0,
                               lessons_learned: List[str] = None):
        """Store a successful project for future reference"""
        
        memory = ProjectMemory(
            name=name,
            prompt=prompt,
            tech_stack=tech_stack,
            success_score=success_score,
            created_at=datetime.now(),
            project_path=project_path,
            lessons_learned=lessons_learned or []
        )
        
        self.projects.append(memory)
        self._save_memory()
        
        print(f"📚 Stored successful project: {name} (score: {success_score:.2f})")
    
    def update_preferences(self, key: str, value: Any):
        """Update user preferences based on success/failure patterns"""
        self.preferences[key] = value
        self._save_memory()
    
    def get_preference(self, key: str, default: Any = None) -> Any:
        """Get user preference"""
        return self.preferences.get(key, default)
    
    def get_tech_stack_preferences(self) -> Dict[str, float]:
        """Get preferred tech stacks based on historical success"""
        tech_scores = {}
        
        for project in self.projects:
            for tech in project.tech_stack:
                if tech not in tech_scores:
                    tech_scores[tech] = []
                tech_scores[tech].append(project.success_score)
        
        # Average success scores per tech
        return {
            tech: sum(scores) / len(scores) 
            for tech, scores in tech_scores.items()
        }
    
    def should_skip_agent(self, agent_name: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Determine if an agent can be skipped based on memory"""
        
        # Check if we have strong patterns for this type of request
        similar = self.find_similar_projects(
            context.get("prompt", ""),
            context.get("tech_requirements", [])
        )
        
        if similar["confidence"] > 0.9:
            if agent_name == "tech_selector":
                return {
                    "skip": True,
                    "reason": f"High-confidence match uses: {', '.join(similar['tech_stack'])}",
                    "recommended_tech": similar["tech_stack"]
                }
            elif agent_name == "spec_refiner" and similar["confidence"] > 0.95:
                return {
                    "skip": True, 
                    "reason": "Nearly identical project found, specs likely sufficient",
                    "reference_project": similar["project_name"]
                }
        
        return {"skip": False}
