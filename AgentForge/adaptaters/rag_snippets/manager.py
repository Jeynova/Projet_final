"""
🎯 Enhanced RAG Manager - Template Recognition & Pattern Matching
Provides comprehensive similarity matching, template recognition, and success pattern analysis
"""
import json
import os
from pathlib import Path
from typing import Dict, List, Any, Tuple
from datetime import datetime
import re

class EnhancedRAGStore:
    """Enhanced RAG storage with template recognition and pattern matching"""
    
    def __init__(self, storage_path: str = None):
        self.storage_path = Path(storage_path) if storage_path else Path(__file__).parent / "rag_data"
        self.storage_path.mkdir(exist_ok=True)
        
        self.prompt_tech_file = self.storage_path / "prompt_tech_mappings.json"
        self.templates_file = self.storage_path / "code_templates.json"
        self.experience_file = self.storage_path / "experience_patterns.json"
        self.success_patterns_file = self.storage_path / "success_patterns.json"
        self.architecture_templates_file = self.storage_path / "architecture_templates.json"
        
        # Load existing data
        self.prompt_tech_mappings = self._load_json(self.prompt_tech_file, [])
        self.code_templates = self._load_json(self.templates_file, {})
        self.experience_patterns = self._load_json(self.experience_file, {})
        self.success_patterns = self._load_json(self.success_patterns_file, {})
        self.architecture_templates = self._load_json(self.architecture_templates_file, {})
        
        # Initialize with common patterns if empty
        self._ensure_base_templates()
    
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
    
    def _ensure_base_templates(self):
        """Initialize base templates for common project patterns"""
        if not self.architecture_templates:
            self.architecture_templates = {
                "authentication_crud": {
                    "pattern": "authentication + CRUD operations",
                    "files": [
                        "backend/models/User.js", "backend/models/Auth.js",
                        "backend/routes/auth.js", "backend/routes/users.js", 
                        "backend/middleware/auth.js", "backend/config/database.js",
                        "frontend/src/components/Login.js", "frontend/src/components/Dashboard.js",
                        "frontend/src/services/api.js", "frontend/src/context/AuthContext.js"
                    ],
                    "endpoints": [
                        {"method": "POST", "path": "/api/auth/login"},
                        {"method": "POST", "path": "/api/auth/register"},
                        {"method": "POST", "path": "/api/auth/logout"},
                        {"method": "GET", "path": "/api/users/profile"},
                        {"method": "PUT", "path": "/api/users/profile"}
                    ],
                    "success_rate": 0.95
                },
                "ecommerce": {
                    "pattern": "e-commerce platform with payments",
                    "files": [
                        "backend/models/Product.js", "backend/models/Order.js", "backend/models/Cart.js",
                        "backend/routes/products.js", "backend/routes/orders.js", "backend/routes/payments.js",
                        "backend/services/paymentService.js", "backend/middleware/auth.js",
                        "frontend/src/components/ProductList.js", "frontend/src/components/Cart.js",
                        "frontend/src/components/Checkout.js", "frontend/src/pages/ProductDetail.js"
                    ],
                    "success_rate": 0.87
                }
            }
            self._save_json(self.architecture_templates_file, self.architecture_templates)
    
    def recognize_pattern(self, prompt: str) -> Dict[str, Any]:
        """Recognize project pattern and return template match"""
        prompt_lower = prompt.lower()
        
        # Pattern recognition keywords
        patterns = {
            "authentication_crud": ["login", "auth", "user", "crud", "manage", "dashboard"],
            "ecommerce": ["ecommerce", "shop", "product", "cart", "order", "payment", "buy", "sell"],
            "social": ["social", "feed", "follow", "post", "comment", "like", "share"],
            "admin": ["admin", "dashboard", "management", "analytics", "report"],
            "file_management": ["file", "upload", "download", "media", "document"]
        }
        
        best_match = None
        best_score = 0.0
        
        for pattern_name, keywords in patterns.items():
            score = sum(1 for keyword in keywords if keyword in prompt_lower) / len(keywords)
            if score > best_score and score > 0.3:  # 30% keyword match threshold
                best_score = score
                best_match = pattern_name
        
        if best_match and best_match in self.architecture_templates:
            template = self.architecture_templates[best_match]
            return {
                "pattern": best_match,
                "confidence": best_score,
                "template": template,
                "recommended_files": template.get("files", []),
                "recommended_endpoints": template.get("endpoints", [])
            }
        
        return {"pattern": "custom", "confidence": 0.0, "template": None}
    
    def find_similar_prompts(self, prompt: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Enhanced similarity matching with pattern recognition"""
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
    """Enhanced RAG manager with template recognition and pattern matching"""
    
    def __init__(self, storage_path: str = None):
        self.store = EnhancedRAGStore(storage_path)
    
    def get_similar_projects(self, prompt: str) -> List[Dict]:
        """Get similar projects for tech guidance with pattern recognition"""
        similar_projects = self.store.find_similar_prompts(prompt)
        pattern_match = self.store.recognize_pattern(prompt)
        
        # Enhance similar projects with pattern information
        for project in similar_projects:
            project['pattern_match'] = pattern_match
        
        return similar_projects
    
    def get_template_match(self, prompt: str) -> Dict[str, Any]:
        """Get template match for the prompt"""
        return self.store.recognize_pattern(prompt)
    
    def store_project_outcome(self, prompt: str, tech_stack: List[Dict], success_score: float, generated_files: List[str] = None):
        """Enhanced project outcome storage with template learning"""
        # Store the basic mapping
        self.store.store_prompt_tech_mapping(prompt, tech_stack, success_score)
        
        # If this was very successful, potentially update templates
        if success_score > 8.5 and generated_files:
            pattern_match = self.store.recognize_pattern(prompt)
            if pattern_match["confidence"] > 0.7:
                # Update template success rate
                pattern_name = pattern_match["pattern"]
                if pattern_name in self.store.architecture_templates:
                    template = self.store.architecture_templates[pattern_name]
                    current_rate = template.get("success_rate", 0.5)
                    # Weighted average with new success
                    new_rate = (current_rate * 0.9) + (success_score / 10 * 0.1)
                    template["success_rate"] = new_rate
                    self.store._save_json(self.store.architecture_templates_file, self.store.architecture_templates)
    
    def get_tech_suggestions(self, prompt: str) -> List[str]:
        """Enhanced technology suggestions with template-based recommendations"""
        basic_suggestions = self.store.get_tech_hints(prompt)
        pattern_match = self.store.recognize_pattern(prompt)
        
        template_suggestions = []
        if pattern_match["template"] and pattern_match["confidence"] > 0.5:
            template = pattern_match["template"]
            success_rate = template.get("success_rate", 0.5)
            if success_rate > 0.8:
                template_suggestions.append(f"High-success pattern detected: {pattern_match['pattern']} (success rate: {success_rate:.1%})")
                template_suggestions.extend([f"Template file: {f}" for f in template.get("files", [])[:3]])
        
        return template_suggestions + basic_suggestions
    
    def get_comprehensive_guidance(self, prompt: str) -> Dict[str, Any]:
        """Get comprehensive guidance including templates, patterns, and similar projects"""
        similar_projects = self.get_similar_projects(prompt)
        template_match = self.get_template_match(prompt)
        tech_suggestions = self.get_tech_suggestions(prompt)
        
        return {
            "similar_projects": similar_projects,
            "template_match": template_match,
            "tech_suggestions": tech_suggestions,
            "has_strong_template": template_match["confidence"] > 0.7,
            "recommended_approach": "template_based" if template_match["confidence"] > 0.7 else "similar_projects"
        }
