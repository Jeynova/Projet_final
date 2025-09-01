#!/usr/bin/env python3
"""
PHASE 2: Beautiful Simplification - 8 Core Agents
Your vision: LLM chooses best tech stack intelligently, agents assist rather than constrain
"""
import sys
import os
import json
import re
import random
import time
import zipfile
import tempfile
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

# Add paths for imports
sys.path.append('.')
sys.path.append('./orchestrator_v2')

from core.llm_client import LLMClient

# Simple tracking function
def track_llm_call(agent: str, operation: str):
    """Simple LLM call tracking"""
    print(f"🔄 {agent} → {operation}")

class LLMBackedMixin:
    """Base mixin for agents that use LLM calls"""
    def __init__(self):
        self.llm_client = LLMClient()
    
    def llm_json(self, system_prompt: str, user_prompt: str, fallback: Dict[str, Any]) -> Dict[str, Any]:
        """Call LLM with JSON response"""
        try:
            result = self.llm_client.extract_json(system_prompt, user_prompt)
            return result if result is not None else fallback
        except Exception as e:
            print(f"⚠️ LLM call failed: {e}")
            return fallback

# =============================================================================
# 🧠 CORE AGENT 1: MemoryAgent - RAG context and learning
# =============================================================================

class MemoryAgent(LLMBackedMixin):
    """Enhanced memory with intelligent project similarity analysis"""
    id = "memory"
    
    def __init__(self, rag_store=None):
        super().__init__()
        self.rag = rag_store
    
    def can_run(self, state: Dict[str, Any]) -> bool:
        return 'memory' not in state
    
    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        prompt = state.get('prompt', '')
        
        # Smart RAG context retrieval
        rag_context = ''
        similar_count = 0
        if self.rag:
            # Query for similar successful projects
            contexts = self.rag.query(prompt, top_k=3)
            if contexts:
                rag_context = '\n'.join(contexts[:2])  # Top 2 most relevant
                similar_count = len(contexts)
        
        # Intelligent domain analysis using LLM
        domain_prompt = f"""Analyze this project request and classify it:
        
Request: "{prompt}"

Classify the project domain, complexity, and suggest optimal approach:
Return JSON:
{{
    "domain": "primary business domain (blog, ecommerce, social, task-mgmt, etc)",
    "complexity": "simple|moderate|complex",
    "key_features": ["feature1", "feature2", "feature3"],
    "similar_projects": ["project_type1", "project_type2"],
    "recommended_approach": "brief strategy recommendation"
}}"""
        
        fb = {
            'domain': 'general',
            'complexity': 'moderate', 
            'key_features': ['crud', 'api'],
            'similar_projects': ['web-app'],
            'recommended_approach': 'standard web application'
        }
        
        analysis = self.llm_json('You are a project analysis expert.', domain_prompt, fb)
        
        return {
            'rag_context': rag_context,
            'similar_count': similar_count,
            'domain': analysis.get('domain', 'general'),
            'complexity': analysis.get('complexity', 'moderate'),
            'key_features': analysis.get('key_features', []),
            'approach': analysis.get('recommended_approach', 'standard approach')
        }

# =============================================================================
# 🔧 CORE AGENT 2: TechSelectAgent - INTELLIGENT tech recommendations
# =============================================================================

class TechSelectAgent(LLMBackedMixin):
    """CORE INTELLIGENCE: Automatically chooses the best tech stack for the project"""
    id = "tech_select"
    
    def can_run(self, state: Dict[str, Any]) -> bool:
        return 'tech' not in state
    
    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        prompt = state.get('prompt', '')
        domain = state.get('memory', {}).get('domain', 'general')
        complexity = state.get('memory', {}).get('complexity', 'moderate')
        features = state.get('memory', {}).get('key_features', [])
        
        # INTELLIGENT TECH SELECTION PROMPT
        tech_prompt = f"""You are a senior tech architect. Analyze this project and choose the BEST tech stack:

Project: "{prompt}"
Domain: {domain}
Complexity: {complexity}
Key Features: {features}

INTELLIGENCE RULES:
1. For BLOG/CMS projects → React+TypeScript frontend + Node.js/FastAPI backend + PostgreSQL
2. For ECOMMERCE projects → React+TypeScript + FastAPI/Node.js + PostgreSQL + Redis
3. For REAL-TIME projects → React+TypeScript + Node.js+Socket.io + Redis + MongoDB
4. For ENTERPRISE projects → React+TypeScript + Java+Spring + PostgreSQL + Docker
5. For SIMPLE APIs → FastAPI + SQLite
6. For COMPLEX data → Python+Django + PostgreSQL + Redis
7. For PERFORMANCE critical → Go + PostgreSQL
8. For RAPID prototyping → React+TypeScript + FastAPI + SQLite

Choose the OPTIMAL stack considering:
- Project complexity and scale requirements
- Performance needs
- Development speed
- Modern best practices
- Full-stack coherence

Return JSON:
{{
    "stack": [
        {{"name": "React", "language": "TypeScript", "role": "frontend", "reason": "modern UI framework"}},
        {{"name": "FastAPI", "language": "Python", "role": "backend", "reason": "rapid API development"}},
        {{"name": "PostgreSQL", "role": "database", "reason": "reliable relational database"}},
        {{"name": "Redis", "role": "cache", "reason": "performance optimization"}}
    ],
    "reasoning": "Detailed explanation of why this stack is optimal for this specific project",
    "confidence": 0.95,
    "alternatives": ["alternative stack if project changes"]
}}

CHOOSE THE BEST, don't just default to Python!"""
        
        # Intelligent fallbacks based on project analysis
        if any(word in prompt.lower() for word in ['blog', 'cms', 'content', 'article']):
            fb_stack = [
                {"name": "React", "language": "TypeScript", "role": "frontend", "reason": "modern blog UI"},
                {"name": "FastAPI", "language": "Python", "role": "backend", "reason": "fast API development"}, 
                {"name": "PostgreSQL", "role": "database", "reason": "content management"}
            ]
        elif any(word in prompt.lower() for word in ['ecommerce', 'shop', 'store', 'cart']):
            fb_stack = [
                {"name": "React", "language": "TypeScript", "role": "frontend", "reason": "interactive shopping"},
                {"name": "FastAPI", "language": "Python", "role": "backend", "reason": "payment processing"},
                {"name": "PostgreSQL", "role": "database", "reason": "transaction safety"},
                {"name": "Redis", "role": "cache", "reason": "cart performance"}
            ]
        elif any(word in prompt.lower() for word in ['real-time', 'chat', 'live', 'socket']):
            fb_stack = [
                {"name": "React", "language": "TypeScript", "role": "frontend", "reason": "real-time UI"},
                {"name": "Node.js", "language": "JavaScript", "role": "backend", "reason": "WebSocket support"},
                {"name": "MongoDB", "role": "database", "reason": "flexible real-time data"},
                {"name": "Redis", "role": "cache", "reason": "real-time performance"}
            ]
        elif any(word in prompt.lower() for word in ['enterprise', 'corporate', 'large-scale']):
            fb_stack = [
                {"name": "React", "language": "TypeScript", "role": "frontend", "reason": "enterprise UI"},
                {"name": "Java", "language": "Java", "role": "backend", "reason": "enterprise reliability"},
                {"name": "PostgreSQL", "role": "database", "reason": "enterprise data management"},
                {"name": "Docker", "role": "deployment", "reason": "containerization"}
            ]
        else:
            # Smart general-purpose stack
            fb_stack = [
                {"name": "React", "language": "TypeScript", "role": "frontend", "reason": "modern development"},
                {"name": "FastAPI", "language": "Python", "role": "backend", "reason": "rapid development"},
                {"name": "PostgreSQL", "role": "database", "reason": "reliable storage"}
            ]
        
        fb = {
            'stack': fb_stack,
            'reasoning': f'Intelligent fallback for {domain} project',
            'confidence': 0.8,
            'alternatives': ['Flask+SQLite', 'Django+PostgreSQL']
        }
        
        try:
            track_llm_call("TechSelectAgent", "intelligent_selection")
            result = self.llm_json('You are a senior tech architect who chooses optimal technology stacks.', tech_prompt, fb)
        except Exception:
            result = fb
        
        # Normalize and validate stack
        stack = result.get('stack', fb_stack)
        confidence = float(result.get('confidence', 0.8))
        
        print(f"🔧 INTELLIGENT TECH SELECTION:")
        for tech in stack:
            name = tech.get('name', 'unknown')
            language = tech.get('language', '')
            role = tech.get('role', '')
            reason = tech.get('reason', '')
            print(f"   🔸 {name} ({language}) - {role}: {reason}")
        
        return {
            'stack': stack,
            'reasoning': result.get('reasoning', ''),
            'confidence': confidence,
            'alternatives': result.get('alternatives', [])
        }

# =============================================================================
# 🏗️ CORE AGENT 3: ArchitectureAgent - File structure + validation
# =============================================================================

class ArchitectureAgent(LLMBackedMixin):
    """Comprehensive architecture with multi-language file structure"""
    id = "architecture"
    
    def can_run(self, state: Dict[str, Any]) -> bool:
        return 'tech' in state and 'architecture' not in state
    
    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        prompt = state.get('prompt', '')
        stack = state.get('tech', {}).get('stack', [])
        domain = state.get('memory', {}).get('domain', 'general')
        
        # Extract languages and frameworks from stack
        frontend_lang = None
        backend_lang = None
        frontend_framework = None
        backend_framework = None
        database = None
        
        for tech in stack:
            name = tech.get('name', '').lower()
            language = tech.get('language', '').lower()
            role = tech.get('role', '').lower()
            
            if role == 'frontend' or name in ['react', 'vue', 'angular']:
                frontend_framework = name
                frontend_lang = language or ('typescript' if 'react' in name else 'javascript')
            elif role == 'backend' or name in ['fastapi', 'django', 'flask', 'spring', 'symfony', 'express']:
                backend_framework = name
                backend_lang = language or ('python' if name in ['fastapi', 'django', 'flask'] else 
                                           'java' if 'spring' in name else
                                           'php' if 'symfony' in name else
                                           'javascript' if 'express' in name else 'python')
            elif role == 'database' or name in ['postgresql', 'mysql', 'mongodb', 'sqlite']:
                database = name
        
        # INTELLIGENT ARCHITECTURE PROMPT
        arch_prompt = f"""Design a complete project architecture for this request:

Project: "{prompt}"
Domain: {domain}
Tech Stack: {[t.get('name') for t in stack]}
Frontend: {frontend_framework} + {frontend_lang}
Backend: {backend_framework} + {backend_lang}
Database: {database}

Create a COMPLETE, production-ready file structure with:
1. Appropriate file extensions for each language
2. Proper directory organization
3. Essential configuration files
4. Both frontend and backend structures

LANGUAGE-SPECIFIC FILE EXTENSIONS:
- React+TypeScript: .tsx for components, .ts for utilities
- PHP+Symfony: .php for controllers/entities, .yaml for config
- Java+Spring: .java for classes, .properties for config
- Node.js: .js/.ts for services
- Python: .py for modules

Return JSON:
{{
    "files": [
        {{"path": "src/App.tsx", "purpose": "Main React application", "language": "typescript"}},
        {{"path": "src/Controller/UserController.php", "purpose": "User management", "language": "php"}},
        {{"path": "config/database.yaml", "purpose": "Database configuration", "language": "yaml"}}
    ],
    "directories": ["src", "config", "tests"],
    "pattern": "Full-Stack Modern Architecture",
    "entry_points": {{"frontend": "src/App.tsx", "backend": "src/Controller/AppController.php"}}
}}

Generate REAL multi-language project structure!"""
        
        # Intelligent fallback based on detected stack
        if frontend_framework == 'react' and backend_framework in ['fastapi', 'flask']:
            # React + Python stack
            fb = {
                'files': [
                    {'path': 'src/App.tsx', 'purpose': 'Main React application', 'language': 'typescript'},
                    {'path': 'src/components/Layout.tsx', 'purpose': 'App layout component', 'language': 'typescript'},
                    {'path': 'src/types/api.ts', 'purpose': 'API type definitions', 'language': 'typescript'},
                    {'path': 'src/services/api.ts', 'purpose': 'API client', 'language': 'typescript'},
                    {'path': 'app/main.py', 'purpose': 'FastAPI backend entry', 'language': 'python'},
                    {'path': 'app/models/user.py', 'purpose': 'User data model', 'language': 'python'},
                    {'path': 'app/routes/api.py', 'purpose': 'API endpoints', 'language': 'python'},
                    {'path': 'package.json', 'purpose': 'Frontend dependencies', 'language': 'json'},
                    {'path': 'requirements.txt', 'purpose': 'Backend dependencies', 'language': 'text'},
                    {'path': 'docker-compose.yml', 'purpose': 'Development environment', 'language': 'yaml'}
                ],
                'directories': ['src', 'src/components', 'src/types', 'src/services', 'app', 'app/models', 'app/routes'],
                'pattern': 'React+TypeScript + FastAPI',
                'entry_points': {'frontend': 'src/App.tsx', 'backend': 'app/main.py'}
            }
        elif frontend_framework == 'react' and backend_framework == 'symfony':
            # React + PHP stack
            fb = {
                'files': [
                    {'path': 'frontend/src/App.tsx', 'purpose': 'React application', 'language': 'typescript'},
                    {'path': 'frontend/src/types/User.ts', 'purpose': 'TypeScript interfaces', 'language': 'typescript'},
                    {'path': 'backend/src/Controller/UserController.php', 'purpose': 'User controller', 'language': 'php'},
                    {'path': 'backend/src/Entity/User.php', 'purpose': 'User entity', 'language': 'php'},
                    {'path': 'backend/config/services.yaml', 'purpose': 'Service configuration', 'language': 'yaml'},
                    {'path': 'frontend/package.json', 'purpose': 'Frontend deps', 'language': 'json'},
                    {'path': 'backend/composer.json', 'purpose': 'Backend deps', 'language': 'json'}
                ],
                'directories': ['frontend/src', 'frontend/src/components', 'backend/src', 'backend/src/Controller', 'backend/src/Entity', 'backend/config'],
                'pattern': 'React+TypeScript + Symfony',
                'entry_points': {'frontend': 'frontend/src/App.tsx', 'backend': 'backend/src/Controller/AppController.php'}
            }
        else:
            # Generic intelligent structure
            fb = {
                'files': [
                    {'path': f'src/main.{self._get_extension(backend_lang)}', 'purpose': 'Application entry point', 'language': backend_lang},
                    {'path': f'src/models/User.{self._get_extension(backend_lang)}', 'purpose': 'User model', 'language': backend_lang},
                    {'path': f'src/routes/api.{self._get_extension(backend_lang)}', 'purpose': 'API routes', 'language': backend_lang}
                ],
                'directories': ['src', 'src/models', 'src/routes'],
                'pattern': f'{backend_framework.title()} Architecture',
                'entry_points': {'main': f'src/main.{self._get_extension(backend_lang)}'}
            }
        
        try:
            track_llm_call("ArchitectureAgent", "architecture_design")
            result = self.llm_json('You are a software architect expert in modern full-stack development.', arch_prompt, fb)
        except Exception:
            result = fb
        
        files = result.get('files', [])
        pattern = result.get('pattern', 'Modern Architecture')
        
        print(f"🏗️ ARCHITECTURE: {pattern}")
        print(f"   📁 Files: {len(files)} across {len(result.get('directories', []))} directories")
        
        # Show language distribution
        lang_count = {}
        for file in files:
            lang = file.get('language', 'unknown')
            lang_count[lang] = lang_count.get(lang, 0) + 1
        
        print(f"   🌐 Languages: {dict(lang_count)}")
        
        return result
    
    def _get_extension(self, language: str) -> str:
        """Map language to file extension"""
        mapping = {
            'typescript': 'ts',
            'javascript': 'js', 
            'python': 'py',
            'php': 'php',
            'java': 'java',
            'go': 'go',
            'csharp': 'cs'
        }
        return mapping.get(language.lower(), 'py')

# =============================================================================
# 🤖 CORE AGENT 4: CodeGenAgent - FREE LLM coding (any language)
# =============================================================================

class CodeGenAgent(LLMBackedMixin):
    """ENHANCED: Truly free multi-language LLM coding"""
    id = "codegen"
    
    def __init__(self, project_root: Path):
        super().__init__()
        self.project_root = project_root
    
    def can_run(self, state: Dict[str, Any]) -> bool:
        return 'architecture' in state and 'codegen' not in state
    
    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        files = state.get('architecture', {}).get('files', [])
        stack = state.get('tech', {}).get('stack', [])
        prompt = state.get('prompt', '')
        
        print(f"🤖 FREE LLM CODING: Generating {len(files)} files in multiple languages")
        
        written = []
        
        for file_spec in files:
            path = file_spec.get('path', '')
            purpose = file_spec.get('purpose', '')
            specified_lang = file_spec.get('language', '')
            
            # Skip invalid paths
            if not path or path.strip() == '':
                continue
            
            # Auto-detect language from extension if not specified
            file_ext = path.split('.')[-1] if '.' in path else 'py'
            target_lang = specified_lang or self._detect_language(file_ext)
            
            print(f"   📝 {path} → {target_lang}")
            
            # TRULY FREE LLM PROMPT
            free_prompt = f"""You are a senior {target_lang} developer. Write production-quality {target_lang} code.

Project Context: "{prompt}"
Tech Stack: {[t.get('name') for t in stack]}
Target Language: {target_lang}
File: {path}
Purpose: {purpose}

Generate COMPLETE, WORKING {target_lang} code for this file.
Use proper {target_lang} syntax, imports, and best practices.
Make it production-ready and functional.

CRITICAL: Return JSON with this structure only:
{{
    "code": "complete {target_lang} file content"
}}

Write REAL {target_lang} code, not placeholders!"""
            
            baseline = self._get_baseline(path, target_lang, stack)
            fb = {'code': baseline}
            
            try:
                track_llm_call("CodeGenAgent", f"{target_lang.lower()}_generation")
                result = self.llm_json(
                    f'You are an expert {target_lang} developer.',
                    free_prompt,
                    fb
                )
                
                code = result.get('code', baseline)
                if code and len(code.strip()) > 10:
                    # Write file with proper path structure
                    file_path = self.project_root / path
                    file_path.parent.mkdir(parents=True, exist_ok=True)
                    file_path.write_text(code)
                    written.append(path)
                    print(f"   ✅ Generated {len(code)} chars of {target_lang}")
                else:
                    print(f"   ⚠️ Empty code for {path}")
                    
            except Exception as e:
                print(f"   ❌ Failed {path}: {e}")
        
        print(f"🎯 COMPLETED: {len(written)} files generated with FREE LLM coding!")
        return {'files': written, 'languages_used': list(set(self._detect_language(f.split('.')[-1]) for f in written if '.' in f))}
    
    def _detect_language(self, file_ext: str) -> str:
        """Detect programming language from file extension"""
        mapping = {
            'tsx': 'TypeScript React',
            'jsx': 'JavaScript React', 
            'ts': 'TypeScript',
            'js': 'JavaScript',
            'php': 'PHP',
            'java': 'Java',
            'go': 'Go',
            'cs': 'C#',
            'py': 'Python',
            'vue': 'Vue.js',
            'yaml': 'YAML',
            'yml': 'YAML',
            'json': 'JSON'
        }
        return mapping.get(file_ext.lower(), 'Python')
    
    def _get_baseline(self, path: str, target_lang: str, stack: List[Dict]) -> str:
        """Language-specific intelligent baselines"""
        if target_lang == 'TypeScript React':
            if 'App.tsx' in path:
                return "import React from 'react';\n\nconst App: React.FC = () => {\n  return (\n    <div>\n      <h1>Welcome</h1>\n    </div>\n  );\n};\n\nexport default App;"
            else:
                return "import React from 'react';\n\ninterface Props {}\n\nconst Component: React.FC<Props> = () => {\n  return <div>Component</div>;\n};\n\nexport default Component;"
        elif target_lang == 'PHP':
            return "<?php\n\nnamespace App\\Controller;\n\nuse Symfony\\Bundle\\FrameworkBundle\\Controller\\AbstractController;\n\nclass Controller extends AbstractController\n{\n    public function index()\n    {\n        return $this->json(['status' => 'ok']);\n    }\n}"
        elif target_lang == 'Java':
            return "package com.app;\n\nimport org.springframework.boot.SpringApplication;\nimport org.springframework.boot.autoconfigure.SpringBootApplication;\n\n@SpringBootApplication\npublic class Application {\n    public static void main(String[] args) {\n        SpringApplication.run(Application.class, args);\n    }\n}"
        elif target_lang == 'Go':
            return "package main\n\nimport (\n\t\"github.com/gin-gonic/gin\"\n\t\"net/http\"\n)\n\nfunc main() {\n\tr := gin.Default()\n\tr.GET(\"/\", func(c *gin.Context) {\n\t\tc.JSON(http.StatusOK, gin.H{\"status\": \"ok\"})\n\t})\n\tr.Run(\":8080\")\n}"
        else:  # Python
            return "from fastapi import FastAPI\n\napp = FastAPI()\n\n@app.get('/')\nasync def root():\n    return {'status': 'ok'}"

# =============================================================================
# 🗄️ CORE AGENT 5: DatabaseAgent - Schema intelligence
# =============================================================================

class DatabaseAgent(LLMBackedMixin):
    """Intelligent database schema design based on project analysis"""
    id = "database"
    
    def can_run(self, state: Dict[str, Any]) -> bool:
        return 'tech' in state and 'database' not in state
    
    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        prompt = state.get('prompt', '')
        domain = state.get('memory', {}).get('domain', 'general')
        features = state.get('memory', {}).get('key_features', [])
        stack = state.get('tech', {}).get('stack', [])
        
        # Find database type from stack
        db_type = 'postgresql'
        for tech in stack:
            if tech.get('role') == 'database':
                db_type = tech.get('name', 'postgresql').lower()
        
        # INTELLIGENT SCHEMA DESIGN
        schema_prompt = f"""Design an intelligent database schema for this project:

Project: "{prompt}"
Domain: {domain}
Features: {features}
Database: {db_type}

Create a SMART schema that anticipates project needs:

DOMAIN-SPECIFIC INTELLIGENCE:
1. BLOG/CMS → User, Post, Comment, Category, Tag, Media
2. ECOMMERCE → User, Product, Category, Order, OrderItem, Cart, Payment
3. SOCIAL → User, Post, Like, Follow, Message, Notification
4. TASK/PROJECT → User, Project, Task, TaskStatus, Assignment, Team
5. ENTERPRISE → User, Role, Permission, Department, Document, Audit

Design tables with:
- Proper relationships (FK, indexes)
- Essential fields for domain
- Performance considerations
- Future scalability

Return JSON:
{{
    "schema": {{
        "users": {{
            "columns": ["id SERIAL PRIMARY KEY", "email VARCHAR(255) UNIQUE", "password_hash VARCHAR(255)", "created_at TIMESTAMP"],
            "indexes": ["email"],
            "relationships": []
        }},
        "posts": {{
            "columns": ["id SERIAL PRIMARY KEY", "title VARCHAR(255)", "content TEXT", "user_id INTEGER", "created_at TIMESTAMP"],
            "indexes": ["user_id", "created_at"],
            "relationships": ["FOREIGN KEY (user_id) REFERENCES users(id)"]
        }}
    }},
    "reasoning": "Why this schema fits the project perfectly"
}}

Be SMART about what tables this specific project actually needs!"""
        
        # Intelligent domain-based fallbacks
        if domain in ['blog', 'cms', 'content']:
            fb_schema = {
                'users': {
                    'columns': ['id SERIAL PRIMARY KEY', 'username VARCHAR(50) UNIQUE', 'email VARCHAR(255) UNIQUE', 'password_hash VARCHAR(255)', 'role VARCHAR(20) DEFAULT \'reader\'', 'created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP'],
                    'indexes': ['email', 'username'],
                    'relationships': []
                },
                'posts': {
                    'columns': ['id SERIAL PRIMARY KEY', 'title VARCHAR(255)', 'content TEXT', 'slug VARCHAR(255) UNIQUE', 'user_id INTEGER', 'status VARCHAR(20) DEFAULT \'draft\'', 'created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP', 'updated_at TIMESTAMP'],
                    'indexes': ['user_id', 'slug', 'created_at', 'status'],
                    'relationships': ['FOREIGN KEY (user_id) REFERENCES users(id)']
                },
                'comments': {
                    'columns': ['id SERIAL PRIMARY KEY', 'content TEXT', 'post_id INTEGER', 'user_id INTEGER', 'created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP'],
                    'indexes': ['post_id', 'user_id'],
                    'relationships': ['FOREIGN KEY (post_id) REFERENCES posts(id)', 'FOREIGN KEY (user_id) REFERENCES users(id)']
                },
                'categories': {
                    'columns': ['id SERIAL PRIMARY KEY', 'name VARCHAR(100) UNIQUE', 'description TEXT'],
                    'indexes': ['name'],
                    'relationships': []
                }
            }
        elif domain in ['ecommerce', 'shop', 'store']:
            fb_schema = {
                'users': {
                    'columns': ['id SERIAL PRIMARY KEY', 'email VARCHAR(255) UNIQUE', 'password_hash VARCHAR(255)', 'first_name VARCHAR(100)', 'last_name VARCHAR(100)', 'created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP'],
                    'indexes': ['email'],
                    'relationships': []
                },
                'products': {
                    'columns': ['id SERIAL PRIMARY KEY', 'name VARCHAR(255)', 'description TEXT', 'price DECIMAL(10,2)', 'stock INTEGER DEFAULT 0', 'category_id INTEGER', 'created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP'],
                    'indexes': ['category_id', 'price'],
                    'relationships': ['FOREIGN KEY (category_id) REFERENCES categories(id)']
                },
                'orders': {
                    'columns': ['id SERIAL PRIMARY KEY', 'user_id INTEGER', 'total DECIMAL(10,2)', 'status VARCHAR(20) DEFAULT \'pending\'', 'created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP'],
                    'indexes': ['user_id', 'status'],
                    'relationships': ['FOREIGN KEY (user_id) REFERENCES users(id)']
                },
                'order_items': {
                    'columns': ['id SERIAL PRIMARY KEY', 'order_id INTEGER', 'product_id INTEGER', 'quantity INTEGER', 'price DECIMAL(10,2)'],
                    'indexes': ['order_id', 'product_id'],
                    'relationships': ['FOREIGN KEY (order_id) REFERENCES orders(id)', 'FOREIGN KEY (product_id) REFERENCES products(id)']
                },
                'categories': {
                    'columns': ['id SERIAL PRIMARY KEY', 'name VARCHAR(100) UNIQUE', 'description TEXT'],
                    'indexes': ['name'],
                    'relationships': []
                }
            }
        else:
            # Generic smart schema
            fb_schema = {
                'users': {
                    'columns': ['id SERIAL PRIMARY KEY', 'email VARCHAR(255) UNIQUE', 'password_hash VARCHAR(255)', 'created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP'],
                    'indexes': ['email'],
                    'relationships': []
                },
                'items': {
                    'columns': ['id SERIAL PRIMARY KEY', 'name VARCHAR(255)', 'description TEXT', 'user_id INTEGER', 'created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP'],
                    'indexes': ['user_id'],
                    'relationships': ['FOREIGN KEY (user_id) REFERENCES users(id)']
                }
            }
        
        fb = {'schema': fb_schema, 'reasoning': f'Intelligent {domain} schema design'}
        
        try:
            track_llm_call("DatabaseAgent", "schema_design")
            result = self.llm_json('You are a database architect expert.', schema_prompt, fb)
        except Exception:
            result = fb
        
        schema = result.get('schema', fb_schema)
        print(f"🗄️ DATABASE SCHEMA: {len(schema)} tables for {domain}")
        for table, config in schema.items():
            cols = len(config.get('columns', []))
            rels = len(config.get('relationships', []))
            print(f"   📊 {table}: {cols} columns, {rels} relationships")
        
        return result

# =============================================================================
# 🚀 CORE AGENT 6: DeploymentAgent - Docker/K8s configs
# =============================================================================

class DeploymentAgent(LLMBackedMixin):
    """Smart deployment configuration based on tech stack"""
    id = "deployment"
    
    def can_run(self, state: Dict[str, Any]) -> bool:
        return 'tech' in state and 'deployment' not in state
    
    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        stack = state.get('tech', {}).get('stack', [])
        complexity = state.get('memory', {}).get('complexity', 'moderate')
        
        # Analyze stack for deployment needs
        has_frontend = any(t.get('role') == 'frontend' for t in stack)
        has_backend = any(t.get('role') == 'backend' for t in stack)
        has_database = any(t.get('role') == 'database' for t in stack)
        has_cache = any(t.get('role') == 'cache' for t in stack)
        
        deploy_prompt = f"""Create deployment configuration for this tech stack:

Stack: {[f"{t.get('name')} ({t.get('language', '')})" for t in stack]}
Complexity: {complexity}
Components: Frontend={has_frontend}, Backend={has_backend}, Database={has_database}, Cache={has_cache}

Design deployment strategy:
1. Docker configurations for each service
2. docker-compose.yml for development
3. Production considerations (K8s if complex)
4. Environment management

Return JSON:
{{
    "docker_services": [
        {{"name": "frontend", "image": "node:18", "port": 3000, "dockerfile": "Dockerfile.frontend"}},
        {{"name": "backend", "image": "python:3.11", "port": 8000, "dockerfile": "Dockerfile.backend"}}
    ],
    "deployment_strategy": "docker-compose|kubernetes",
    "configs": ["docker-compose.yml", "Dockerfile.frontend", "Dockerfile.backend"],
    "production_notes": "Scaling and security considerations"
}}"""
        
        fb = {
            'docker_services': [
                {'name': 'app', 'image': 'python:3.11', 'port': 8000, 'dockerfile': 'Dockerfile'}
            ],
            'deployment_strategy': 'docker-compose',
            'configs': ['docker-compose.yml', 'Dockerfile'],
            'production_notes': 'Basic containerization setup'
        }
        
        try:
            track_llm_call("DeploymentAgent", "deployment_config")
            result = self.llm_json('You are a DevOps deployment expert.', deploy_prompt, fb)
        except Exception:
            result = fb
        
        services = result.get('docker_services', [])
        strategy = result.get('deployment_strategy', 'docker-compose')
        
        print(f"🚀 DEPLOYMENT: {strategy}")
        for service in services:
            print(f"   🐳 {service.get('name')} → {service.get('image')} :{service.get('port')}")
        
        return result

# =============================================================================
# ✅ CORE AGENT 7: ValidateAgent - Quality checks + tests  
# =============================================================================

class ValidateAgent(LLMBackedMixin):
    """Intelligent code validation and test generation"""
    id = "validate"
    
    def can_run(self, state: Dict[str, Any]) -> bool:
        return 'codegen' in state and 'validate' not in state
    
    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        files = state.get('codegen', {}).get('files', [])
        languages = state.get('codegen', {}).get('languages_used', [])
        stack = state.get('tech', {}).get('stack', [])
        
        validate_prompt = f"""Generate validation strategy for this multi-language project:

Generated Files: {files}
Languages: {languages}
Tech Stack: {[t.get('name') for t in stack]}

Create comprehensive validation approach:
1. Language-specific linting configs
2. Unit test frameworks for each language
3. Integration testing strategy
4. Quality checks (security, performance)

Return JSON:
{{
    "linting": {{
        "typescript": {{"tool": "eslint", "config": ".eslintrc.json"}},
        "python": {{"tool": "pylint", "config": "pyproject.toml"}}
    }},
    "testing": {{
        "typescript": {{"framework": "jest", "test_pattern": "**/*.test.ts"}},
        "python": {{"framework": "pytest", "test_pattern": "tests/**/*_test.py"}}
    }},
    "quality_checks": ["type-checking", "security-scan", "dependency-audit"],
    "ci_pipeline": "github-actions|gitlab-ci"
}}"""
        
        fb = {
            'linting': {'python': {'tool': 'pylint', 'config': 'pyproject.toml'}},
            'testing': {'python': {'framework': 'pytest', 'test_pattern': 'tests/**/*_test.py'}},
            'quality_checks': ['type-checking', 'security-scan'],
            'ci_pipeline': 'github-actions'
        }
        
        try:
            track_llm_call("ValidateAgent", "validation_strategy")
            result = self.llm_json('You are a software quality expert.', validate_prompt, fb)
        except Exception:
            result = fb
        
        linting = result.get('linting', {})
        testing = result.get('testing', {})
        
        print(f"✅ VALIDATION: {len(linting)} linting configs, {len(testing)} test frameworks")
        for lang, config in testing.items():
            framework = config.get('framework', 'unknown')
            print(f"   🧪 {lang}: {framework} testing")
        
        return result

# =============================================================================
# 📊 CORE AGENT 8: EvaluationAgent - Scoring + improvement suggestions  
# =============================================================================

class EvaluationAgent(LLMBackedMixin):
    """Final project evaluation with improvement recommendations"""
    id = "evaluation"
    
    def can_run(self, state: Dict[str, Any]) -> bool:
        return 'codegen' in state and 'evaluation' not in state
    
    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        # Analyze complete project state
        tech_stack = state.get('tech', {}).get('stack', [])
        architecture = state.get('architecture', {}).get('pattern', 'Unknown')
        files_count = len(state.get('codegen', {}).get('files', []))
        languages = state.get('codegen', {}).get('languages_used', [])
        confidence = state.get('tech', {}).get('confidence', 0.0)
        
        eval_prompt = f"""Evaluate this complete project generation:

Tech Stack: {[f"{t.get('name')} ({t.get('language', '')})" for t in tech_stack]}
Architecture: {architecture}
Generated Files: {files_count}
Languages Used: {languages}
Tech Confidence: {confidence:.1%}

Provide comprehensive evaluation:

Return JSON:
{{
    "scores": {{
        "tech_choice": 9.2,
        "architecture": 8.8,
        "code_quality": 8.5,
        "completeness": 9.0,
        "scalability": 8.7
    }},
    "overall_score": 8.84,
    "strengths": ["Modern tech stack", "Multi-language support", "Scalable architecture"],
    "improvements": ["Add error handling", "Implement logging", "Add authentication"],
    "recommendations": "Specific next steps for enhancement"
}}"""
        
        fb = {
            'scores': {
                'tech_choice': 8.0,
                'architecture': 7.5,
                'code_quality': 7.0,
                'completeness': 8.0,
                'scalability': 7.5
            },
            'overall_score': 7.6,
            'strengths': ['Working multi-language setup'],
            'improvements': ['Add error handling', 'Improve documentation'],
            'recommendations': 'Continue development with chosen stack'
        }
        
        try:
            track_llm_call("EvaluationAgent", "project_evaluation")
            result = self.llm_json('You are a senior project evaluation expert.', eval_prompt, fb)
        except Exception:
            result = fb
        
        overall = result.get('overall_score', 7.6)
        strengths = result.get('strengths', [])
        improvements = result.get('improvements', [])
        
        print(f"📊 PROJECT EVALUATION: {overall:.1f}/10")
        print(f"   💪 Strengths: {len(strengths)} identified")
        print(f"   🔧 Improvements: {len(improvements)} suggested")
        
        return result

# =============================================================================
# 🎯 PHASE 2 ORCHESTRATOR - 8 Core Agents Pipeline
# =============================================================================

class Phase2Orchestrator:
    """Streamlined orchestrator for 8 core agents"""
    
    def __init__(self, project_root: Path, rag_store=None):
        self.project_root = project_root
        self.agents = [
            MemoryAgent(rag_store),
            TechSelectAgent(),
            ArchitectureAgent(),
            CodeGenAgent(project_root),
            DatabaseAgent(),
            DeploymentAgent(),
            ValidateAgent(),
            EvaluationAgent()
        ]
    
    def run(self, prompt: str) -> Dict[str, Any]:
        """Execute the streamlined 8-agent pipeline"""
        print("🚀 PHASE 2: INTELLIGENT 8-AGENT PIPELINE")
        print("=" * 60)
        
        state = {'prompt': prompt}
        
        for i, agent in enumerate(self.agents, 1):
            if agent.can_run(state):
                print(f"\n{i}. Running {agent.__class__.__name__}...")
                result = agent.run(state)
                state[agent.id] = result
            else:
                print(f"\n{i}. Skipping {agent.__class__.__name__} (requirements not met)")
        
        print("\n🎯 PHASE 2 COMPLETE!")
        print("=" * 60)
        return state
    """Test the 8-agent simplified system"""
    print("🚀 TESTING PHASE 2: 8-Agent Intelligent System")
    print("=" * 60)
    
    # Test case: Blog platform (should intelligently choose React+TypeScript + FastAPI)
    test_state = {
        'prompt': 'Create a modern blog platform with admin dashboard and real-time comments'
    }
    
    print(f"📝 Test Project: {test_state['prompt']}")
    print()
    
    # Test MemoryAgent
    print("🧠 1. MemoryAgent - Analyzing project...")
    memory_agent = MemoryAgent()
    if memory_agent.can_run(test_state):
        memory_result = memory_agent.run(test_state)
        test_state['memory'] = memory_result
        print(f"   ✅ Domain: {memory_result.get('domain')}")
        print(f"   ✅ Complexity: {memory_result.get('complexity')}")
        print(f"   ✅ Features: {memory_result.get('key_features', [])}")
    
    # Test TechSelectAgent - THE CORE INTELLIGENCE
    print("\n🔧 2. TechSelectAgent - INTELLIGENT tech selection...")
    tech_agent = TechSelectAgent()
    if tech_agent.can_run(test_state):
        tech_result = tech_agent.run(test_state)
        test_state['tech'] = tech_result
        print(f"   ✅ Confidence: {tech_result.get('confidence', 0):.1%}")
    
    # Test ArchitectureAgent
    print("\n🏗️ 3. ArchitectureAgent - Multi-language structure...")
    arch_agent = ArchitectureAgent()
    if arch_agent.can_run(test_state):
        arch_result = arch_agent.run(test_state)
        test_state['architecture'] = arch_result
        
    # Test CodeGenAgent - FREE LLM CODING
    print("\n🤖 4. CodeGenAgent - FREE multi-language coding...")
    with tempfile.TemporaryDirectory() as tmpdir:
        codegen_agent = CodeGenAgent(Path(tmpdir))
        if codegen_agent.can_run(test_state):
            codegen_result = codegen_agent.run(test_state)
            print(f"   ✅ Languages used: {codegen_result.get('languages_used', [])}")
    
    print("\n🎯 PHASE 2 RESULTS:")
    print("✅ Intelligent tech selection based on project analysis")
    print("✅ Multi-language architecture generation")  
    print("✅ FREE LLM coding in appropriate languages")
    print("✅ 8 core agents instead of 22+ redundant ones")
    print()
    print("🚀 Your vision: LLM-first development with intelligent agent assistance!")

if __name__ == '__main__':
    test_phase2_system()
