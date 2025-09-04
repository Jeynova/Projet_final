#!/usr/bin/env python3
"""
🎓 LEARNING MEMORY WITH PATTERN RECOGNITION
Learns from successful code patterns → Stores in RAG → Serves working code to agents
"""

from typing import Dict, Any, List
from datetime import datetime
import json
import hashlib
import re

from core.base import LLMBackedMixin
from core.domain_detection import IntelligentDomainDetector
from core.contracts import merge_contract
from core.events import has_event_type
from core.scheduling import schedule_agents


# ──────────────────────────────────────────────────────────────────────────────
# 🎓 LEARNING MEMORY (now: learns → seeds/merges contract → teaches → acts)
# ──────────────────────────────────────────────────────────────────────────────
class LearningMemoryAgent(LLMBackedMixin):
    id = "memory"
    def __init__(self, rag_store=None, experience_db=None):
        super().__init__()
        self.rag = rag_store
        self.detector = IntelligentDomainDetector()
        self.experience_db = experience_db or {}
        self.code_patterns_db = {}  # Store successful code patterns
        self.pattern_rag = {}  # Pattern-based RAG system

    def can_run(self, state: Dict[str, Any]) -> bool:
        # Don't run if quality goal has been reached
        if state.get('goal_reached', False):
            return False
            
        never_ran = 'memory' not in state
        post_validation = 'last_validated_iter' in state and state.get('memory_epoch', -1) < state.get('last_validated_iter', -1)
        
        # Use standardized event checking
        events = state.get('events', [])
        event_triggered = (has_event_type(events, 'validation_completed') or 
                          has_event_type(events, 'refinement_triggered')) and not state.get('memory_after_validation_done', False)
        
        return never_ran or post_validation or event_triggered

    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        prompt = state.get('prompt', '')
        analysis = self.detector.analyze_project(prompt)
        rag_hints, rag_conf, similar_cnt = [], 0.0, 0
        if self.rag:
            try:
                sims = self.rag.get_similar_projects(prompt); similar_cnt = len(sims)
                if sims:
                    print(f"   📚 RAG found {len(sims)} similar projects")
                    for proj in sims:
                        if proj.get('success_score',0) > 7.0:
                            sim = proj.get('similarity',0)
                            if sim > 0.3:
                                for tech in proj.get('tech_stack', []):
                                    rag_hints.append(f"Similar project ({sim:.1%}) used {tech.get('name','?')} for {tech.get('role','?')}")
                            if sim > 0.7: rag_conf = max(rag_conf, sim)
                    if rag_conf > 0.7 and sims[0].get('success_score',0) > 8.0:
                        best = sims[0]
                        return {**analysis,'rag_hints':rag_hints,'rag_confidence':rag_conf,'similar_projects_count':similar_cnt,
                                'complete_solution': {'tech_stack':best.get('tech_stack',[]),'confidence':rag_conf,'source':'RAG_high_confidence_match'},
                                'experience_hints': rag_hints[:3],'experience_warnings': [],'successful_patterns':[f"RAG: {len(sims)} strong matches"],
                                'hints': rag_hints[:3],'warnings': []}
            except Exception as e:
                print(f"   ⚠️ RAG lookup failed: {e}")

        guidance = self._get_experience_guidance(prompt, analysis)
        all_hints = (guidance.get('experience_hints') or []) + rag_hints

        # compile a COMPREHENSIVE MEMORY POLICY with template recognition
        sys_policy = """You are a SENIOR SOLUTION ARCHITECT with access to historical project data.

Analyze the project requirements and similar successful patterns to create a comprehensive memory policy.

**TEMPLATE RECOGNITION:** Identify if this matches known successful patterns:
- Authentication systems (JWT, OAuth, session management)
- CRUD applications (REST APIs, database operations)
- E-commerce platforms (payments, inventory, orders)
- Social platforms (feeds, followers, messaging)
- Admin dashboards (analytics, user management)
- File management systems (uploads, processing, storage)

**TECHNOLOGY PREFERENCES:** Based on successful patterns:
- Backend: Recommend proven combinations (Node.js+Express, Python+Django/Flask)
- Frontend: Suggest appropriate complexity (React, Vue, vanilla HTML)
- Database: Match to data requirements (PostgreSQL, MongoDB, Redis)
- Infrastructure: Production-ready patterns (Docker, K8s, AWS)

**SEED CONTRACT:** Provide comprehensive baseline based on project complexity:
- Simple: 10-15 essential files
- Moderate: 20-30 files with authentication and CRUD
- Complex: 30-50+ files with advanced features

**COACHING GUIDANCE:** Specific implementation patterns that work:
- Security best practices
- Performance optimization strategies
- Scalability patterns
- Testing approaches

Return COMPREHENSIVE JSON policy:
{{
  "template_match": {{
    "pattern": "authentication_crud|ecommerce|social|admin|file_management|custom",
    "confidence": 0.0-1.0,
    "template_files": ["template-specific files that always work"],
    "template_endpoints": ["proven API patterns"],
    "template_architecture": "known successful architecture pattern"
  }},
  "prefer": {{
    "backend": ["technologies with proven success for this pattern"],
    "frontend": ["UI frameworks that work well"],
    "database": ["data stores that scale"],
    "deployment": ["infrastructure that works"],
    "patterns": ["architectural patterns to use"]
  }},
  "avoid": {{
    "backend": ["technologies that cause issues"],
    "frontend": ["complex frameworks for simple projects"],
    "database": ["inappropriate data stores"],
    "deployment": ["over-complicated deployment"],
    "antipatterns": ["common mistakes to avoid"]
  }},
  "seed_contract": {{
    "files": ["comprehensive file list based on complexity"],
    "endpoints": ["complete API specification"],
    "tables": ["all database entities needed"],
    "infrastructure": ["docker, ci/cd, monitoring files"],
    "security": ["auth, validation, middleware files"]
  }},
  "coach_notes": [
    "specific implementation guidance",
    "performance optimization tips",
    "security best practices",
    "testing strategies",
    "deployment recommendations"
  ],
  "success_patterns": ["proven approaches that work"],
  "risk_warnings": ["common failure points to watch"]
}}

Leverage historical success data to provide actionable, proven guidance."""
        
        user_policy = f"Domain={analysis.get('domain')} perf={analysis.get('performance_needs')} hints={all_hints[:6]}"
        fallback_policy = {
            "prefer": {"backend": [], "frontend": [], "database": [], "deployment": []},
            "avoid": {"backend": [], "frontend": [], "database": [], "deployment": []},
            "seed_contract": {
                "files": ["backend/app.js","frontend/src/App.js","docker-compose.yml",".env.example","README.md","Makefile"],
                "endpoints": [{"method":"GET","path":"/api/health"},{"method":"GET","path":"/docs"}],
                "tables": [{"name":"users"}]
            },
            "validation": {"min_score": 7, "require_valid": False, "mode": "guided"},
            "coach_notes": ["use env vars", "add health check"]
        }
        policy = self.llm_json(sys_policy, user_policy, fallback_policy)

        # apply policy: seed/merge contract + set validation knobs + coach notes
        existing = state.get('contract', {})
        seeded = policy.get('seed_contract') or {}
        if seeded:
            merged = merge_contract(existing, seeded) if existing else {**seeded, "source": "memory_seed"}
            print("📐 MEMORY → seeded/merged contract")
        else:
            merged = existing

        res = {
            **analysis,
            **guidance,
            "memory_policy": policy,
            "contract": merged,
            "contract_seeded_by_memory": bool(seeded),
            "validation_threshold": policy.get('validation', {}).get('min_score', state.get('validation_threshold', 7)),
            "require_valid_status": policy.get('validation', {}).get('require_valid', state.get('require_valid_status', False)),
            "file_contract_mode": policy.get('validation', {}).get('mode', state.get('file_contract_mode','guided')),
            "coach_notes": policy.get('coach_notes', []),
            "memory": True,
            "memory_epoch": state.get('last_validated_iter', state.get('memory_epoch', 0)),
            "memory_after_validation_done": True  # Prevent thrashing
        }

        # If post-validation gaps exist, escalate strictness and schedule fixes
        if 'validation' in state:
            val = state['validation']
            gaps = (val.get('missing_files') or []) + (val.get('missing_endpoints') or [])
            if gaps and state.get('file_contract_mode') != 'strict':
                print("🧠 MEMORY → escalating contract mode to 'strict' next round")
                res['file_contract_mode'] = 'strict'
                schedule_agents(state, ['contract','codegen'], front=True)

        # echo learning analysis
        print("🧠 LEARNING MEMORY ANALYSIS:")
        print(f"   🎯 Domain: {analysis.get('domain')} (confidence: {analysis.get('confidence',0):.1%})")
        print(f"   📊 Complexity: {analysis.get('complexity')}")
        print(f"   ⚡ Performance: {analysis.get('performance_needs')}")
        if similar_cnt: print(f"   📚 RAG: {similar_cnt} similar projects found; conf {rag_conf:.1%}")
        if all_hints:
            print(f"   🎓 Total hints: {len(all_hints)}")
            for h in all_hints[:2]: print(f"      💡 {h}")

        # Build concrete code templates for other agents
        template_package = self._build_code_templates(analysis, all_hints, policy)
        res['code_templates'] = template_package

        return res

    def _get_experience_guidance(self, prompt: str, analysis: Dict) -> Dict:
        hints, warnings, patterns, complete_solution = [], [], [], None
        domain = analysis.get('domain','general'); p = (prompt or '').lower()
        if self.rag:
            try:
                sh = self.rag.get_tech_suggestions(prompt)
                if sh: hints.extend(sh[:3]); print(f"   📚 RAG provided {len(sh)} hints")
            except Exception as e:
                print(f"   ⚠️ RAG lookup failed: {e}")
        if domain == 'productivity':
            hints.append("Task/Project tools benefit from relational data (ACID, joins, reporting)")
            patterns.append("PostgreSQL + strict schemas improved integrity & reporting")
            warnings.append("Document stores complicate cross-entity queries & reporting")
        elif 'real-time' in p or 'chat' in p:
            hints.append("Real-time features benefit from WS-native stack")
            patterns.append("JS/Node excelled for long-lived connections")
        return {'experience_hints':hints,'experience_warnings':warnings,'successful_patterns':patterns,
                'hints':hints,'warnings':warnings,'complete_solution':complete_solution}

    def learn_from_outcome(self, project_prompt: str, chosen_stack: List[Dict], outcome_score: float):
        domain = self.detector.analyze_project(project_prompt).get('domain')
        if self.rag:
            try:
                self.rag.store_project_outcome(project_prompt, chosen_stack, outcome_score)
                print(f"📚 RAG stored project outcome: {project_prompt[:30]}... (score: {outcome_score})")
            except Exception as e:
                print(f"⚠️ RAG storage failed: {e}")
        backend = next((t for t in chosen_stack if t.get('role')=='backend'), {})
        if outcome_score > 8.0 and backend:
            if domain not in self.experience_db: self.experience_db[domain] = {'successes':[], 'failures':[]}
            self.experience_db[domain]['successes'].append({'tech': backend.get('name'), 'score': outcome_score, 'timestamp': datetime.now().isoformat()})
            print(f"🎓 LEARNED SUCCESS: {backend.get('name')} worked well for {domain}")
        elif outcome_score < 6.0 and backend:
            if domain not in self.experience_db: self.experience_db[domain] = {'successes':[], 'failures':[]}
            self.experience_db[domain]['failures'].append({'tech': backend.get('name'), 'score': outcome_score, 'timestamp': datetime.now().isoformat()})
            print(f"⚠️ LEARNED WARNING: {backend.get('name')} struggled for {domain}")
    
    def _build_code_templates(self, analysis: Dict, hints: List[str], policy: Dict) -> Dict:
        """Build concrete code templates that other agents can use"""
        domain = analysis.get('domain', 'general')
        complexity = analysis.get('complexity', 'simple')
        
        templates = {}
        
        # Authentication templates based on domain
        if 'auth' in str(hints).lower() or domain in ['productivity', 'blog', 'social']:
            templates['auth_service'] = '''import bcrypt from 'bcrypt';
import jwt from 'jsonwebtoken';
import { User } from '../models/User';

export class AuthService {
  async register(email: string, password: string, name: string) {
    const hashedPassword = await bcrypt.hash(password, 12);
    const user = new User({ email, password: hashedPassword, name });
    return await user.save();
  }

  async login(email: string, password: string) {
    const user = await User.findOne({ email });
    if (!user || !await bcrypt.compare(password, user.password)) {
      throw new Error('Invalid credentials');
    }
    const token = jwt.sign({ userId: user._id }, process.env.JWT_SECRET!);
    return { user: this.sanitizeUser(user), token };
  }

  private sanitizeUser(user: any) {
    const { password, ...sanitized } = user.toObject();
    return sanitized;
  }
}'''

        # CRUD templates for productivity apps  
        if domain == 'productivity' or 'task' in str(hints).lower():
            templates['crud_service'] = '''import { Request, Response } from 'express';
import { Task } from '../models/Task';

export class TaskService {
  async createTask(req: Request, res: Response) {
    try {
      const { title, description, priority, dueDate } = req.body;
      const task = new Task({
        title,
        description,
        priority: priority || 'medium',
        dueDate: dueDate ? new Date(dueDate) : null,
        userId: req.user.id,
        status: 'pending'
      });
      
      const savedTask = await task.save();
      res.status(201).json(savedTask);
    } catch (error) {
      res.status(400).json({ error: error.message });
    }
  }

  async getTasks(req: Request, res: Response) {
    try {
      const { status, priority } = req.query;
      const filter: any = { userId: req.user.id };
      
      if (status) filter.status = status;
      if (priority) filter.priority = priority;
      
      const tasks = await Task.find(filter).sort({ createdAt: -1 });
      res.json(tasks);
    } catch (error) {
      res.status(500).json({ error: error.message });
    }
  }

  async updateTask(req: Request, res: Response) {
    try {
      const task = await Task.findOneAndUpdate(
        { _id: req.params.id, userId: req.user.id },
        req.body,
        { new: true, runValidators: true }
      );
      
      if (!task) {
        return res.status(404).json({ error: 'Task not found' });
      }
      
      res.json(task);
    } catch (error) {
      res.status(400).json({ error: error.message });
    }
  }
}'''

        # React component templates based on complexity
        if complexity in ['moderate', 'complex']:
            templates['react_dashboard'] = '''import React, { useState, useEffect } from 'react';
import axios from 'axios';

interface Task {
  _id: string;
  title: string;
  description: string;
  status: 'pending' | 'in-progress' | 'completed';
  priority: 'low' | 'medium' | 'high';
  dueDate?: string;
}

export const Dashboard: React.FC = () => {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState({ status: '', priority: '' });

  useEffect(() => {
    fetchTasks();
  }, [filter]);

  const fetchTasks = async () => {
    try {
      const params = new URLSearchParams();
      if (filter.status) params.append('status', filter.status);
      if (filter.priority) params.append('priority', filter.priority);

      const response = await axios.get(`/api/tasks?${params}`, {
        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
      });
      setTasks(response.data);
    } catch (error) {
      console.error('Error fetching tasks:', error);
    } finally {
      setLoading(false);
    }
  };

  const updateTaskStatus = async (taskId: string, status: string) => {
    try {
      await axios.put(`/api/tasks/${taskId}`, { status }, {
        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
      });
      fetchTasks();
    } catch (error) {
      console.error('Error updating task:', error);
    }
  };

  if (loading) return <div className="loading">Loading tasks...</div>;

  return (
    <div className="dashboard">
      <header className="dashboard-header">
        <h1>Task Dashboard</h1>
        <div className="filters">
          <select value={filter.status} onChange={e => setFilter({...filter, status: e.target.value})}>
            <option value="">All Status</option>
            <option value="pending">Pending</option>
            <option value="in-progress">In Progress</option>
            <option value="completed">Completed</option>
          </select>
        </div>
      </header>
      
      <div className="tasks-grid">
        {tasks.map(task => (
          <div key={task._id} className={`task-card priority-${task.priority}`}>
            <h3>{task.title}</h3>
            <p>{task.description}</p>
            <div className="task-actions">
              <button onClick={() => updateTaskStatus(task._id, 'in-progress')}>
                Start
              </button>
              <button onClick={() => updateTaskStatus(task._id, 'completed')}>
                Complete
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};'''

        print(f"💡 MEMORY → Providing {len(templates)} code templates for {domain} domain")
        return templates
    
    def learn_from_successful_project(self, project_data: Dict[str, Any], validation_score: float):
        """Learn code patterns from successful projects (score >= 7.0)"""
        if validation_score < 7.0:
            return
            
        print(f"🎓 LEARNING from successful project (score: {validation_score}/10)")
        
        generated_code = project_data.get('generated_code', {})
        tech_stack = project_data.get('tech_stack', {})
        project_prompt = project_data.get('prompt', '')
        
        # Extract patterns from high-quality code
        patterns = self._extract_code_patterns(generated_code, tech_stack, project_prompt)
        
        # Store patterns in RAG with metadata
        for pattern in patterns:
            self._store_pattern_in_rag(pattern, validation_score)
            
        print(f"📚 RAG updated with {len(patterns)} new code patterns")
    
    def _extract_code_patterns(self, generated_code: Dict[str, str], tech_stack: Dict, prompt: str) -> List[Dict]:
        """Extract reusable patterns from generated code"""
        patterns = []
        domain = self.detector.analyze_project(prompt).get('domain', 'general')
        
        for filename, code_content in generated_code.items():
            if not code_content or len(str(code_content)) < 100:
                continue
                
            # Identify pattern type based on filename and content
            pattern_type = self._classify_code_pattern(filename, code_content)
            if not pattern_type:
                continue
                
            # Extract key functions/components
            key_functions = self._extract_key_functions(code_content, pattern_type)
            
            if key_functions:
                pattern = {
                    'id': hashlib.md5(f"{pattern_type}_{domain}_{filename}".encode()).hexdigest()[:8],
                    'type': pattern_type,
                    'domain': domain,
                    'filename': filename,
                    'tech_stack': tech_stack,
                    'code_snippet': code_content,
                    'key_functions': key_functions,
                    'description': f"{pattern_type} pattern for {domain} domain",
                    'learned_at': datetime.now().isoformat(),
                    'usage_keywords': self._extract_keywords(code_content, prompt)
                }
                patterns.append(pattern)
                
        return patterns
    
    def _classify_code_pattern(self, filename: str, code_content: str) -> str:
        """Classify what type of pattern this code represents"""
        filename_lower = filename.lower()
        code_lower = str(code_content).lower()
        
        # Authentication patterns
        if any(keyword in filename_lower for keyword in ['auth', 'login', 'user']) and \
           any(keyword in code_lower for keyword in ['password', 'jwt', 'bcrypt', 'login']):
            return 'authentication'
            
        # CRUD patterns  
        if any(keyword in code_lower for keyword in ['create', 'read', 'update', 'delete', 'findone', 'save']):
            return 'crud_operations'
            
        # API routing patterns
        if any(keyword in filename_lower for keyword in ['route', 'api', 'controller']) and \
           any(keyword in code_lower for keyword in ['router', 'express', 'app.get', 'app.post']):
            return 'api_routing'
            
        # React component patterns
        if filename_lower.endswith('.jsx') or filename_lower.endswith('.tsx') or \
           any(keyword in code_lower for keyword in ['usestate', 'useeffect', 'react']):
            return 'react_component'
            
        # Database model patterns
        if any(keyword in filename_lower for keyword in ['model', 'schema']) and \
           any(keyword in code_lower for keyword in ['mongoose', 'sequelize', 'schema', 'model']):
            return 'database_model'
            
        return None
    
    def _extract_key_functions(self, code_content: str, pattern_type: str) -> List[str]:
        """Extract key function names from code"""
        functions = []
        
        # Extract function/method names using regex
        patterns_regex = [
            r'(?:async\s+)?function\s+(\w+)',  # function declarations
            r'(\w+)\s*:\s*(?:async\s+)?function',  # object methods
            r'(?:async\s+)?(\w+)\s*\([^)]*\)\s*(?::\s*[^{]+)?\s*{',  # arrow functions
            r'app\.(?:get|post|put|delete|patch)\s*\(\s*[\'"`]([^\'"`]+)',  # express routes
        ]
        
        for regex in patterns_regex:
            matches = re.findall(regex, str(code_content), re.IGNORECASE)
            functions.extend(matches)
            
        return list(set(functions))[:5]  # Top 5 unique functions
    
    def _extract_keywords(self, code_content: str, prompt: str) -> List[str]:
        """Extract keywords for pattern matching"""
        keywords = []
        
        # Extract from code
        code_keywords = re.findall(r'\b(?:user|auth|task|project|crud|api|login|register|dashboard)\b', 
                                  str(code_content).lower())
        keywords.extend(code_keywords)
        
        # Extract from prompt  
        prompt_keywords = re.findall(r'\b(?:management|authentication|dashboard|crud|api|task|user|project)\b',
                                    prompt.lower())
        keywords.extend(prompt_keywords)
        
        return list(set(keywords))[:10]
    
    def _store_pattern_in_rag(self, pattern: Dict, validation_score: float):
        """Store successful pattern in RAG system"""
        pattern_id = pattern['id']
        pattern['validation_score'] = validation_score
        
        # Store in pattern RAG
        if pattern['type'] not in self.pattern_rag:
            self.pattern_rag[pattern['type']] = []
            
        self.pattern_rag[pattern['type']].append(pattern)
        
        # Keep only top 10 patterns per type (by validation score)
        self.pattern_rag[pattern['type']] = sorted(
            self.pattern_rag[pattern['type']], 
            key=lambda x: x['validation_score'], 
            reverse=True
        )[:10]
    
    def serve_working_patterns(self, context: Dict[str, Any], max_patterns: int = 3) -> List[Dict]:
        """Serve working code patterns based on current generation context"""
        prompt = context.get('prompt', '')
        component_name = context.get('component_name', '')
        tech_stack = context.get('tech_stack', {})
        domain = self.detector.analyze_project(prompt).get('domain', 'general')
        
        print(f"🔍 PATTERN SEARCH → Looking for patterns matching: {component_name} in {domain}")
        
        # Score all stored patterns by relevance
        scored_patterns = []
        for pattern_type, patterns in self.pattern_rag.items():
            for pattern in patterns:
                score = self._calculate_pattern_relevance(pattern, context, domain)
                if score > 0.3:  # Minimum relevance threshold
                    scored_patterns.append({
                        'pattern': pattern,
                        'relevance_score': score
                    })
        
        # Sort by relevance and return top matches
        scored_patterns.sort(key=lambda x: x['relevance_score'], reverse=True)
        best_patterns = [sp['pattern'] for sp in scored_patterns[:max_patterns]]
        
        if best_patterns:
            print(f"✨ SERVING {len(best_patterns)} working code patterns (relevance: {scored_patterns[0]['relevance_score']:.2f})")
            return best_patterns
        else:
            print("🔍 No relevant patterns found - using default templates")
            return []
    
    def _calculate_pattern_relevance(self, pattern: Dict, context: Dict, domain: str) -> float:
        """Calculate how relevant a stored pattern is to current generation context"""
        score = 0.0
        
        prompt = context.get('prompt', '').lower()
        component_name = context.get('component_name', '').lower()
        tech_stack = context.get('tech_stack', {})
        
        # Domain match (high weight)
        if pattern['domain'] == domain:
            score += 0.4
        
        # Component name similarity  
        if any(keyword in component_name for keyword in pattern['usage_keywords']):
            score += 0.3
            
        # Prompt keyword matches
        matching_keywords = sum(1 for keyword in pattern['usage_keywords'] 
                               if keyword in prompt)
        if matching_keywords > 0:
            score += 0.2 * min(matching_keywords / len(pattern['usage_keywords']), 1.0)
            
        # Tech stack compatibility
        pattern_tech = pattern.get('tech_stack', {})
        if pattern_tech and tech_stack:
            tech_matches = sum(1 for tech in tech_stack.values() 
                             if str(tech).lower() in str(pattern_tech).lower())
            if tech_matches > 0:
                score += 0.1 * min(tech_matches / len(tech_stack), 1.0)
        
        # Validation score boost (higher quality patterns get priority)
        validation_score = pattern.get('validation_score', 7.0)
        score *= (validation_score / 10.0)
        
        return min(score, 1.0)
    
    def format_patterns_for_generation(self, patterns: List[Dict], context: Dict) -> str:
        """Format working patterns into prompt-friendly code examples"""
        if not patterns:
            return ""
            
        formatted_examples = []
        component_name = context.get('component_name', 'Component')
        
        formatted_examples.append("🎯 WORKING CODE PATTERNS (learned from successful projects):")
        
        for i, pattern in enumerate(patterns, 1):
            pattern_type = pattern['type']
            validation_score = pattern.get('validation_score', 7.0)
            key_functions = pattern.get('key_functions', [])
            
            formatted_examples.append(f"\n--- PATTERN {i}: {pattern_type.upper()} (Score: {validation_score}/10) ---")
            formatted_examples.append(f"Key Functions: {', '.join(key_functions[:3])}")
            
            # Include relevant code snippet (truncated)
            code_snippet = pattern['code_snippet']
            if len(str(code_snippet)) > 800:
                code_snippet = str(code_snippet)[:800] + "\n// ... (pattern continues)"
                
            formatted_examples.append(f"```\n{code_snippet}\n```")
            
        formatted_examples.append(f"\n💡 Use these proven patterns as inspiration for {component_name}")
        formatted_examples.append("Focus on implementing similar structures with 50-200 lines of production code.")
        
        return "\n".join(formatted_examples)
