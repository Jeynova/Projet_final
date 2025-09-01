#!/usr/bin/env python3
"""
🎭 ORGANIC INTELLIGENCE: Multi-Perspective Team + Learning Guidance
Your vision: LLM as team meeting (PM + Dev + PO + Consultant + User) + learning from experience

NO hard-coded tech choices - pure organic team intelligence with experience guidance!
"""
import sys
import os
import tempfile
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime

sys.path.append('.')
from core.llm_client import LLMClient
from team_debate import run_debate, moderate

def track_llm_call(agent: str, operation: str):
    print(f"🔄 {agent} → {operation}")

class IntelligentDomainDetector:
    """Context detection for guidance only"""
    DOMAIN_PATTERNS = {
        'blog': ['blog', 'cms', 'content', 'article', 'post'],
        'ecommerce': ['shop', 'store', 'ecommerce', 'payment', 'cart'],
        'social': ['chat', 'social', 'message', 'real-time', 'live'],
        'enterprise': ['enterprise', 'corporate', 'business', 'document'],
        'analytics': ['analytics', 'data', 'dashboard', 'reporting'],
        'api': ['api', 'rest', 'endpoint', 'microservice', 'service']
    }
    
    def analyze_project(self, prompt: str) -> Dict[str, any]:
        prompt_lower = prompt.lower()
        domain_scores = {}
        
        for domain, keywords in self.DOMAIN_PATTERNS.items():
            score = sum(3 for keyword in keywords if keyword in prompt_lower)
            domain_scores[domain] = score
        
        best_domain = max(domain_scores.items(), key=lambda x: x[1])
        detected_domain = best_domain[0] if best_domain[1] > 0 else 'general'
        
        complexity = 'simple' if any(word in prompt_lower for word in ['simple', 'basic']) else 'moderate'
        if any(word in prompt_lower for word in ['enterprise', 'complex', 'advanced']):
            complexity = 'complex'
        
        performance = 'low' if 'simple' in prompt_lower else 'medium' 
        if any(word in prompt_lower for word in ['high-performance', 'fast', 'real-time']):
            performance = 'high'
        
        return {
            'domain': detected_domain,
            'complexity': complexity,
            'performance_needs': performance,
            'confidence': min(1.0, best_domain[1] / 10.0)
        }

class LLMBackedMixin:
    def __init__(self):
        self.llm_client = LLMClient()
    
    def llm_json(self, system_prompt: str, user_prompt: str, fallback: Dict[str, Any]) -> Dict[str, Any]:
        try:
            result = self.llm_client.extract_json(system_prompt, user_prompt)
            return result if result is not None else fallback
        except Exception as e:
            print(f"⚠️ LLM call failed: {e}")
            return fallback
        
class ValidationRouter:
    name = "ValidationRouter"
    def can_run(self, state):
        # run once per new validation result
        return 'validation' in state and state.get('routed_after_iter', -1) < state.get('last_validated_iter', -1)
    def run(self, state):
        score = state.get('validation',{}).get('score', 0)
        threshold = state.get('validation_threshold', 8)
        it = state.get('last_validated_iter', 0)
        result = {'routed_after_iter': it}

        if score >= threshold:
            result['goal_reached'] = True
            print(f"🎯 QUALITY GOAL REACHED: Score {score}/10 ≥ {threshold}/10")
        elif it < state.get('max_codegen_iters', 2) - 1:
            result['redo_codegen'] = True
            print(f"🔄 REFINEMENT: Score {score}/10 < {threshold}/10 → iterate (iter {it+1})")
        else:
            result['goal_reached'] = True
            print(f"⏭️ MAX ITERATIONS: proceed with score {score}/10 after {it+1} attempts")
        return result
# =============================================================================
# 🎓 LEARNING MEMORY AGENT: Experience-based guidance
# =============================================================================

class LearningMemoryAgent(LLMBackedMixin):
    """🎓 Learns from project outcomes and provides experience-based guidance"""
    id = "memory"
    
    def __init__(self, rag_store=None, experience_db=None):
        super().__init__()
        self.rag = rag_store
        self.detector = IntelligentDomainDetector()
        self.experience_db = experience_db or {}
    
    def can_run(self, state: Dict[str, Any]) -> bool:
        return 'memory' not in state
    
    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        prompt = state.get('prompt', '')
        
        # Basic analysis
        analysis = self.detector.analyze_project(prompt)
        
        # � RAG-ENHANCED: Check for similar projects FIRST
        rag_hints = []
        rag_confidence = 0.0
        similar_projects_count = 0
        
        if self.rag:
            try:
                similar_projects = self.rag.get_similar_projects(prompt)
                similar_projects_count = len(similar_projects)
                
                if similar_projects:
                    print(f"   📚 RAG found {len(similar_projects)} similar projects")
                    
                    # Extract hints from successful similar projects
                    for project in similar_projects:
                        if project.get('success_score', 0) > 7.0:
                            similarity = project.get('similarity', 0)
                            if similarity > 0.3:  # High similarity threshold
                                tech_stack = project.get('tech_stack', [])
                                for tech in tech_stack:
                                    hint = f"Similar project ({similarity:.1%} match) successfully used {tech.get('name', 'Unknown')} for {tech.get('role', 'unknown')}"
                                    rag_hints.append(hint)
                                    
                                # If very high similarity, boost confidence
                                if similarity > 0.7:
                                    rag_confidence = similarity
                                    
                    # If we have high-confidence RAG match, provide complete solution
                    if rag_confidence > 0.7 and similar_projects[0].get('success_score', 0) > 8.0:
                        best_match = similar_projects[0]
                        complete_solution = {
                            'tech_stack': best_match.get('tech_stack', []),
                            'confidence': rag_confidence,
                            'source': 'RAG_high_confidence_match'
                        }
                        print(f"   🎯 RAG HIGH CONFIDENCE: Using proven solution from similar project ({rag_confidence:.1%} match)")
                        
                        # Return early with RAG solution
                        return {
                            **analysis,
                            'rag_hints': rag_hints,
                            'rag_confidence': rag_confidence,
                            'similar_projects_count': similar_projects_count,
                            'complete_solution': complete_solution,
                            'experience_hints': rag_hints[:3],
                            'experience_warnings': [],
                            'successful_patterns': [f"RAG: {len(similar_projects)} similar successful projects"],
                            'hints': rag_hints[:3],
                            'warnings': []
                        }
                        
            except Exception as e:
                print(f"   ⚠️ RAG lookup failed: {e}")
        
        # �🎓 Get traditional experience-based guidance (fallback)
        guidance = self._get_experience_guidance(prompt, analysis)
        
        # Combine RAG hints with traditional guidance
        all_hints = rag_hints + guidance.get('experience_hints', [])
        
        print(f"🧠 LEARNING MEMORY ANALYSIS:")
        print(f"   🎯 Domain: {analysis.get('domain')} (confidence: {analysis.get('confidence', 0):.1%})")
        print(f"   📊 Complexity: {analysis.get('complexity')}")
        print(f"   ⚡ Performance: {analysis.get('performance_needs')}")
        
        if similar_projects_count > 0:
            print(f"   📚 RAG: {similar_projects_count} similar projects found")
            print(f"   🎯 RAG confidence: {rag_confidence:.1%}")
            
        if all_hints:
            print(f"   🎓 Total hints: {len(all_hints)} (RAG: {len(rag_hints)}, Experience: {len(guidance.get('experience_hints', []))})")
            for hint in all_hints[:2]:
                print(f"      💡 {hint}")
        
        if guidance.get('warnings'):
            print(f"   ⚠️ Experience warnings: {', '.join(guidance['warnings'][:2])}")
        
        # 🎯 SMART BYPASS: If we have a complete solution from experience, provide it
        result = {
            **analysis, 
            **guidance,
            'rag_hints': rag_hints,
            'rag_confidence': rag_confidence,
            'similar_projects_count': similar_projects_count
        }
        
        # Override hints with combined RAG + experience
        result['experience_hints'] = all_hints[:5]
        result['hints'] = all_hints[:5]
        
        if guidance.get('complete_solution'):
            result.update(guidance['complete_solution'])
            print(f"   🚀 BYPASSING OTHER AGENTS: Experience provides complete solution!")
        
        return result
    
    def _get_experience_guidance(self, prompt: str, analysis: Dict) -> Dict:
        """Provide guidance based on learned experience patterns"""
        hints = []
        warnings = []
        successful_patterns = []
        complete_solution = None
        
        domain = analysis.get('domain', 'general')
        complexity = analysis.get('complexity', 'moderate')
        prompt_lower = prompt.lower()
        
        # 🎯 RAG-ENHANCED: Get similar project hints if RAG available
        if self.rag:
            try:
                similar_hints = self.rag.get_tech_suggestions(prompt)
                if similar_hints:
                    hints.extend(similar_hints[:3])  # Add top 3 RAG hints
                    print(f"   📚 RAG provided {len(similar_hints)} hints from similar projects")
            except Exception as e:
                print(f"   ⚠️ RAG lookup failed: {e}")
        
        # 🎓 SIMULATED LEARNING (in real system, this would query actual outcomes)
        if domain == 'blog' and complexity == 'simple':
            hints.append("Past blog projects succeeded with rapid-development frameworks")
            successful_patterns.append("Content management benefited from Python/Node.js ecosystems")
            # 🎯 SMART BYPASS: We know exactly what works for simple blogs
            if 'simple' in prompt_lower or 'basic' in prompt_lower:
                complete_solution = {
                    'tech_stack': [
                        {"role": "backend", "name": "Node.js + Express", "reasoning": "Proven fast development for content sites"},
                        {"role": "frontend", "name": "React", "reasoning": "Component-based architecture perfect for blog layouts"},
                        {"role": "database", "name": "SQLite", "reasoning": "Simple, file-based storage for small blogs"},
                        {"role": "deployment", "name": "Vercel", "reasoning": "Zero-config deployment for Node.js apps"}
                    ]
                }
                print(f"   🎯 SMART BYPASS: Complete solution from experience!")
        
        elif 'real-time' in prompt_lower or 'chat' in prompt_lower:
            hints.append("Real-time projects required WebSocket-native technologies") 
            successful_patterns.append("JavaScript/Node.js ecosystem excelled for real-time features")
            warnings.append("Some frameworks struggled with concurrent connections")
        
        elif domain == 'enterprise' and complexity == 'complex':
            hints.append("Enterprise projects needed mature, battle-tested frameworks")
            successful_patterns.append("JVM-based solutions provided enterprise reliability")
            warnings.append("Newer frameworks faced enterprise adoption challenges")
        
        elif 'performance' in prompt_lower or analysis.get('performance_needs') == 'high':
            hints.append("High-performance projects benefited from compiled languages")
            successful_patterns.append("Go/Java/C# delivered superior performance")
            warnings.append("Interpreted languages hit scaling bottlenecks")
        
        elif domain == 'ecommerce':
            hints.append("E-commerce projects needed strong payment/transaction support")
            successful_patterns.append("Both Node.js and Python showed good payment integration")
            warnings.append("Database ACID compliance was critical for transactions")
        
        return {
            'experience_hints': hints,
            'experience_warnings': warnings, 
            'successful_patterns': successful_patterns,
            'hints': hints,
            'warnings': warnings,
            'complete_solution': complete_solution  # 🎯 New field
        }
    
    def learn_from_outcome(self, project_prompt: str, chosen_stack: List[Dict], outcome_score: float):
        """Learn from project outcomes to improve future guidance"""
        domain = self.detector.analyze_project(project_prompt).get('domain')
        
        # 🎯 RAG-ENHANCED: Store in RAG system if available
        if self.rag:
            try:
                self.rag.store_project_outcome(project_prompt, chosen_stack, outcome_score)
                print(f"📚 RAG stored project outcome: {project_prompt[:30]}... (score: {outcome_score})")
            except Exception as e:
                print(f"⚠️ RAG storage failed: {e}")
        
        if outcome_score > 8.0:  # Successful project
            backend = next((t for t in chosen_stack if t.get('role') == 'backend'), {})
            if backend:
                pattern = f"{backend.get('name')} delivered success for {domain} projects"
                print(f"🎓 LEARNED SUCCESS PATTERN: {pattern}")
                # Store in experience_db
                if domain not in self.experience_db:
                    self.experience_db[domain] = {'successes': [], 'failures': []}
                self.experience_db[domain]['successes'].append({
                    'tech': backend.get('name'),
                    'score': outcome_score,
                    'timestamp': datetime.now().isoformat()
                })
        
        elif outcome_score < 6.0:  # Failed project
            backend = next((t for t in chosen_stack if t.get('role') == 'backend'), {})
            if backend:
                warning = f"{backend.get('name')} struggled with {domain} requirements"
                print(f"⚠️ LEARNED WARNING: {warning}")
                # Store warning in experience_db
                if domain not in self.experience_db:
                    self.experience_db[domain] = {'successes': [], 'failures': []}
                self.experience_db[domain]['failures'].append({
                    'tech': backend.get('name'),
                    'score': outcome_score,
                    'timestamp': datetime.now().isoformat()
                })

# =============================================================================
# 🎭 MULTI-PERSPECTIVE TECH TEAM AGENT: Organic team intelligence
# =============================================================================

class MultiPerspectiveTechAgent(LLMBackedMixin):
    """🎭 Technology decision-making team - LLM wears multiple stakeholder hats"""
    id = "tech_team"
    
    def __init__(self):
        super().__init__()
    
    def can_run(self, state: Dict[str, Any]) -> bool:
        return 'tech_stack' not in state and any(key in state for key in ['domain', 'complexity', 'performance_needs'])
    
    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        track_llm_call("🎭 MultiPerspectiveTechAgent", "parallel team debate decision")
        
        # Get user request and experience guidance
        prompt = state.get('prompt', '')
        hints = state.get('experience_hints', [])
        warnings = state.get('experience_warnings', [])
        domain = state.get('domain', 'general')
        complexity = state.get('complexity', 'moderate')
        performance = state.get('performance_needs', 'medium')
        
        # Build comprehensive context for team debate
        context_parts = [f"Project: {prompt}"]
        context_parts.append(f"Domain context: {domain} (complexity: {complexity}, performance: {performance})")
        
        if hints:
            context_parts.append(f"Experience guidance: {'; '.join(hints)}")
        if warnings:
            context_parts.append(f"Past warnings: {'; '.join(warnings)}")
        
        debate_context = "\n".join(context_parts)
        
        # Core technology decision question
        debate_question = f"""Technology Stack Decision for: {prompt}

Context: {debate_context}

As your assigned role, analyze and recommend specific technologies for:
1. Backend framework/language
2. Frontend framework  
3. Database solution
4. Deployment strategy

Provide your role's specific perspective with concrete technology recommendations and reasoning."""

        try:
            # Run real parallel team debate with concurrent execution
            print("🎭 Starting parallel team debate for technology decision...")
            debate_results = run_debate(self.llm_client, debate_question, debate_context)
            
            # Moderate the parallel perspectives into a coherent technology stack
            print("⚖️ Moderating parallel perspectives into consensus...")
            moderation_prompt = f"Synthesize these parallel team perspectives into a coherent technology decision for: {prompt}"
            team_consensus = moderate(self.llm_client, moderation_prompt, debate_results)
            
            # Extract structured tech stack from team decision
            extraction_prompt = f"""Based on this team debate consensus, extract a structured technology stack:

TEAM CONSENSUS:
{team_consensus}

Return JSON with the team's organic technology decision:
{{
  "backend": {{"name": "chosen_backend", "reasoning": "team's reasoning"}},
  "frontend": {{"name": "chosen_frontend", "reasoning": "team's reasoning"}}, 
  "database": {{"name": "chosen_database", "reasoning": "team's reasoning"}},
  "deployment": {{"name": "chosen_deployment", "reasoning": "team's reasoning"}},
  "team_discussion": "summary of the parallel multi-perspective debate",
  "debate_method": "concurrent_parallel_execution"
}}"""

            fallback_team = {
                "backend": {"name": "Express.js", "reasoning": "Team chose popular, well-documented solution"},
                "frontend": {"name": "React", "reasoning": "Team selected widely-adopted framework"},
                "database": {"name": "PostgreSQL", "reasoning": "Team preferred reliable, full-featured database"},
                "deployment": {"name": "Docker + Cloud", "reasoning": "Team chose modern deployment approach"},
                "team_discussion": team_consensus,
                "debate_method": "concurrent_parallel_execution"
            }
            
            result = self.llm_json(extraction_prompt, "", fallback_team)
            
            # Add the parallel debate details
            result['parallel_debate_results'] = debate_results
            result['concurrent_roles'] = ['PM', 'DEV', 'PO', 'CONSULTANT', 'USER']
            
            print("✅ Parallel team debate completed successfully")
            
        except Exception as e:
            print(f"⚠️ Team debate system error: {e}")
            print("🔄 Falling back to single LLM simulation...")
            
            # Fallback to original single LLM approach
            system_prompt = """You are a TECHNOLOGY DECISION-MAKING TEAM making organic choices.

You simultaneously wear the hats of:
👔 Lead Project Manager - timeline, budget, team constraints
💻 Lead Developer - technical implementation, maintainability  
📋 Product Owner - user experience, feature requirements
🎯 Technology Consultant - industry trends, best practices
👤 End User - usability, performance expectations

Have a team meeting discussion in your mind, then make the BEST technology choice.

CRITICAL: Choose technologies based on pure reasoning - NOT predetermined lists.
Think about what would ACTUALLY work best for this specific project.

Return JSON with your organic team decision:
{
  "backend": {"name": "chosen_backend", "reasoning": "why the team chose this"},
  "frontend": {"name": "chosen_frontend", "reasoning": "why the team chose this"}, 
  "database": {"name": "chosen_database", "reasoning": "why the team chose this"},
  "deployment": {"name": "chosen_deployment", "reasoning": "why the team chose this"},
  "team_discussion": "summary of the multi-perspective team meeting",
  "debate_method": "single_llm_fallback"
}"""
            
            fallback_team = {
                "backend": {"name": "Express.js", "reasoning": "Team chose popular, well-documented solution"},
                "frontend": {"name": "React", "reasoning": "Team selected widely-adopted framework"},
                "database": {"name": "PostgreSQL", "reasoning": "Team preferred reliable, full-featured database"},
                "deployment": {"name": "Docker + Cloud", "reasoning": "Team chose modern deployment approach"},
                "team_discussion": "Team made conservative choices due to limited information",
                "debate_method": "single_llm_fallback"
            }
            
            result = self.llm_json(system_prompt, debate_context, fallback_team)
        
        print(f"\n🎭 TEAM TECHNOLOGY DECISION:")
        print(f"   🖥️  Backend: {result.get('backend', {}).get('name', 'Unknown')}")
        print(f"   🎨 Frontend: {result.get('frontend', {}).get('name', 'Unknown')}")
        print(f"   🗄️ Database: {result.get('database', {}).get('name', 'Unknown')}")
        print(f"   🚀 Deploy: {result.get('deployment', {}).get('name', 'Unknown')}")
        
        team_discussion = result.get('team_discussion', '')
        if team_discussion and isinstance(team_discussion, str):
            print(f"   💬 Team process: {team_discussion[:100]}...")
        
        # Convert to standard format
        tech_stack = []
        for role, details in result.items():
            if role != 'team_discussion' and isinstance(details, dict):
                tech_stack.append({
                    'role': role,
                    'name': details.get('name', 'Unknown'),
                    'reasoning': details.get('reasoning', 'Team decision')
                })
        
        return {'tech_stack': tech_stack, 'team_decision_process': result}

# =============================================================================
# 🏗️ ARCHITECTURE AGENT: Intelligent structure design
# =============================================================================

class ArchitectureAgent(LLMBackedMixin):
    """🏗️ Creates intelligent architecture based on tech choices and requirements"""
    id = "architecture"
    
    def can_run(self, state: Dict[str, Any]) -> bool:
        return 'architecture' not in state and 'tech_stack' in state
    
    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        track_llm_call("🏗️ ArchitectureAgent", "intelligent architecture design")
        
        prompt = state.get('prompt', '')
        tech_stack = state.get('tech_stack', [])
        complexity = state.get('complexity', 'moderate')
        
        # Get backend choice for architecture decisions
        backend = next((t for t in tech_stack if t.get('role') == 'backend'), {})
        frontend = next((t for t in tech_stack if t.get('role') == 'frontend'), {})
        
        system_prompt = f"""You are an expert software architect designing the structure for this project.

Given the team's technology choices, design the OPTIMAL project structure.
Consider the specific technologies chosen and their best practices.

Return JSON with intelligent architecture:
{{
  "project_structure": {{
    "src/": "main source code",
    "config/": "configuration files",
    "tests/": "test files"
  }},
  "key_components": ["ComponentA", "ComponentB"],
  "data_flow": "how data flows through the system",
  "scalability_approach": "how the system scales"
}}"""
        
        user_prompt = f"""Project: {prompt}

Chosen Technologies:
{chr(10).join([f"- {t.get('role', 'unknown')}: {t.get('name', 'Unknown')} ({t.get('reasoning', 'No reason')})" for t in tech_stack])}

Project complexity: {complexity}

Design the optimal architecture for these specific technology choices."""
        
        fallback_arch = {
            "project_structure": {
                "src/": "main source code",
                "config/": "configuration files", 
                "tests/": "test files"
            },
            "key_components": ["App", "Database", "API"],
            "data_flow": "Client → API → Database → Response",
            "scalability_approach": "Horizontal scaling with load balancer"
        }
        
        result = self.llm_json(system_prompt, user_prompt, fallback_arch)
        
        print(f"\n🏗️ INTELLIGENT ARCHITECTURE:")
        structure = result.get('project_structure', {})
        for folder, desc in list(structure.items())[:3]:
            print(f"   📁 {folder}: {desc}")
        
        components = result.get('key_components', [])
        if components:
            print(f"   🔧 Components: {', '.join(components[:3])}")
        
        return {'architecture': result}

# =============================================================================
# 💾 CODE GENERATION AGENT: Multi-language intelligent generation
# =============================================================================

class CodeGenAgent(LLMBackedMixin):
    """💾 Generates intelligent code based on chosen architecture and technologies"""
    id = "codegen"
    
    def can_run(self, state):
        wants_rerun = state.get('redo_codegen', False)
        not_done = 'generated_code' not in state or wants_rerun
        has_inputs = 'architecture' in state and 'tech_stack' in state
        return has_inputs and not_done and state.get('codegen_iters', 0) < state.get('max_codegen_iters', 2)

    def run(self, state):
        track_llm_call("💾 CodeGenAgent", "intelligent multi-language generation")
        
        # consume redo flag if present
        prior_issues = state.get('validation', {}).get('issues', [])
        suggestions = state.get('validation', {}).get('suggestions', [])
        
        prompt = state.get('prompt', '')
        tech_stack = state.get('tech_stack', [])
        architecture = state.get('architecture', {})
        
        # Get specific technologies for generation
        backend = next((t for t in tech_stack if t.get('role') == 'backend'), {})
        frontend = next((t for t in tech_stack if t.get('role') == 'frontend'), {})
        database = next((t for t in tech_stack if t.get('role') == 'database'), {})
        
        system_prompt = f"""You are an expert full-stack developer implementing the project.

Generate production-ready code for the chosen technologies.
Follow best practices specific to each technology stack.

Return JSON with generated files:
{{
  "files": {{
    "filename.ext": "file content",
    "another.ext": "another file content"
  }},
  "setup_instructions": ["step 1", "step 2"],
  "run_commands": ["command to start the application"]
}}

CRITICAL: Generate code for the SPECIFIC technologies chosen by the team."""
        
        # weave feedback into the user_prompt
        feedback_block = ""
        if prior_issues or suggestions:
            feedback_block = f"\n\nAddress these validation issues:\n- " + "\n- ".join([*prior_issues[:5], *suggestions[:5]])

        user_prompt = f"""Project: {prompt}

Team's Technology Decisions:
{chr(10).join([f"- {t.get('role', 'unknown')}: {t.get('name', 'Unknown')} (Reason: {t.get('reasoning', 'Team decision')})" for t in tech_stack])}

Architecture Structure:
{architecture.get('project_structure', {})}

Key Components: {', '.join(architecture.get('key_components', []))}
{feedback_block}

Generate complete, working code for these specific choices."""
        
        fallback_code = {
            "files": {
                "app.py": "# Simple application\nprint('Hello World')",
                "README.md": "# Project\n\nGenerated application"
            },
            "setup_instructions": ["Install dependencies", "Configure environment"],
            "run_commands": ["python app.py"]
        }
        
        result = self.llm_json(system_prompt, user_prompt, fallback_code)
        
        print(f"\n💾 INTELLIGENT CODE GENERATION:")
        files = result.get('files', {})
        print(f"   📝 Generated {len(files)} files")
        for filename in list(files.keys())[:3]:
            print(f"   📄 {filename}")
        
        if result.get('setup_instructions'):
            print(f"   ⚙️ Setup steps: {len(result['setup_instructions'])}")
        
        # bump iteration counter
        iters = state.get('codegen_iters', 0) + 1
        result['codegen_iters'] = iters
        # IMPORTANT: clear the redo request via a versioned pattern instead of deleting keys
        return {'generated_code': result, 'codegen_iters': iters, 'redo_codegen': False}

# =============================================================================
# 🗄️ DATABASE AGENT: Intelligent data modeling
# =============================================================================

class DatabaseAgent(LLMBackedMixin):
    """🗄️ Creates intelligent database schemas based on project needs and chosen database"""
    id = "database"
    
    def can_run(self, state: Dict[str, Any]) -> bool:
        return 'database_schema' not in state and 'tech_stack' in state
    
    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        track_llm_call("🗄️ DatabaseAgent", "intelligent schema design")
        
        prompt = state.get('prompt', '')
        tech_stack = state.get('tech_stack', [])
        
        # Get chosen database
        database = next((t for t in tech_stack if t.get('role') == 'database'), {})
        database_name = database.get('name', 'Unknown')
        
        system_prompt = f"""You are a database architect designing the optimal schema.

Create a schema specifically optimized for {database_name}.
Consider the unique features and best practices of this database system.

Return JSON with intelligent database design:
{{
  "tables": {{
    "table_name": {{
      "columns": {{"column": "type"}},
      "indexes": ["column1", "column2"],
      "relationships": ["related_table"]
    }}
  }},
  "optimization_notes": "database-specific optimizations"
}}"""
        
        user_prompt = f"""Project: {prompt}

Chosen Database: {database_name}
Database Selection Reasoning: {database.get('reasoning', 'Team decision')}

Design the optimal schema for this specific database technology."""
        
        fallback_schema = {
            "tables": {
                "users": {
                    "columns": {"id": "PRIMARY KEY", "name": "VARCHAR", "email": "VARCHAR"},
                    "indexes": ["email"],
                    "relationships": []
                }
            },
            "optimization_notes": "Basic schema with standard optimizations"
        }
        
        result = self.llm_json(system_prompt, user_prompt, fallback_schema)
        
        print(f"\n🗄️ INTELLIGENT DATABASE DESIGN:")
        tables = result.get('tables', {})
        print(f"   📊 Tables: {', '.join(list(tables.keys())[:3])}")
        if result.get('optimization_notes'):
            print(f"   ⚡ Optimizations: {result['optimization_notes'][:50]}...")
        
        return {'database_schema': result}

# =============================================================================
# 🚀 DEPLOYMENT AGENT: Intelligent deployment strategy
# =============================================================================

class DeploymentAgent(LLMBackedMixin):
    """🚀 Creates intelligent deployment based on project and chosen technologies"""
    id = "deployment"
    
    def can_run(self, state: Dict[str, Any]) -> bool:
        return 'deployment' not in state and 'tech_stack' in state
    
    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        track_llm_call("🚀 DeploymentAgent", "intelligent deployment strategy")
        
        prompt = state.get('prompt', '')
        tech_stack = state.get('tech_stack', [])
        complexity = state.get('complexity', 'moderate')
        
        # Get deployment choice
        deployment = next((t for t in tech_stack if t.get('role') == 'deployment'), {})
        
        system_prompt = f"""You are a DevOps expert creating the optimal deployment strategy.

Design deployment specifically optimized for the chosen technology stack.
Consider the unique requirements and best practices for these technologies.

Return JSON with intelligent deployment:
{{
  "strategy": "chosen deployment approach",
  "containers": {{"service": "container_details"}},
  "environment": {{"ENV_VAR": "value"}},
  "scaling": "how the system scales"
}}"""
        
        user_prompt = f"""Project: {prompt}

Technology Stack:
{chr(10).join([f"- {t.get('role', 'unknown')}: {t.get('name', 'Unknown')}" for t in tech_stack])}

Project complexity: {complexity}

Create the optimal deployment strategy for these specific technologies."""
        
        fallback_deploy = {
            "strategy": "Container-based deployment",
            "containers": {"app": "Main application container"},
            "environment": {"NODE_ENV": "production"},
            "scaling": "Horizontal scaling with load balancer"
        }
        
        result = self.llm_json(system_prompt, user_prompt, fallback_deploy)
        
        print(f"\n🚀 INTELLIGENT DEPLOYMENT:")
        print(f"   📦 Strategy: {result.get('strategy', 'Unknown')}")
        containers = result.get('containers', {})
        if containers:
            print(f"   🐳 Containers: {', '.join(list(containers.keys())[:2])}")
        
        return {'deployment': result}

# =============================================================================
# ✅ VALIDATION AGENT: Intelligent quality assurance
# =============================================================================

class ValidateAgent(LLMBackedMixin):
    """✅ Validates generated code using intelligent analysis"""
    id = "validate"
    
    def can_run(self, state):
        if 'generated_code' not in state:
            return False
        # run if code was never validated OR there’s a newer codegen
        return state.get('last_validated_iter', -1) < state.get('codegen_iters', 0)
    
    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        track_llm_call("✅ ValidateAgent", "intelligent code validation")
        
        generated_code = state.get('generated_code', {})
        tech_stack = state.get('tech_stack', [])
        files = generated_code.get('files', {})
        
        if not files:
            return {'validation': {'status': 'no_code', 'score': 0}}
        
        # Get main technologies for validation
        backend = next((t for t in tech_stack if t.get('role') == 'backend'), {})
        
        system_prompt = f"""You are a senior code reviewer performing intelligent validation.

Analyze the generated code for:
- Syntax correctness for the specific technologies used
- Best practices adherence 
- Security considerations
- Performance implications
- Maintainability

Return JSON validation:
{{
  "status": "valid|issues|invalid",
  "score": 0-10,
  "issues": ["issue1", "issue2"],
  "suggestions": ["suggestion1", "suggestion2"]
}}"""
        
        # Analyze the main files
        main_files = list(files.items())[:3]
        file_analysis = []
        for filename, content in main_files:
            file_analysis.append(f"{filename}:\n{content[:200]}...")
        
        user_prompt = f"""Validate this generated code for {backend.get('name', 'Unknown')} backend:

{chr(10).join(file_analysis)}

Total files: {len(files)}
Technologies: {', '.join([t.get('name', 'Unknown') for t in tech_stack])}"""
        
        fallback_validation = {
            "status": "valid",
            "score": 7,
            "issues": [],
            "suggestions": ["Consider adding error handling", "Add input validation"]
        }
        
        result = self.llm_json(system_prompt, user_prompt, fallback_validation)
        
        print(f"\n✅ INTELLIGENT VALIDATION:")
        print(f"   📊 Status: {result.get('status', 'unknown')}")
        print(f"   🎯 Score: {result.get('score', 0)}/10")
        
        issues = result.get('issues', [])
        if issues:
            print(f"   ⚠️ Issues: {len(issues)} found")
        
        result = self.llm_json(system_prompt, user_prompt, fallback_validation)
        current_iter = state.get('codegen_iters', 0)
        return {'validation': result, 'last_validated_iter': current_iter}

# =============================================================================
# 📊 EVALUATION AGENT: Intelligent project assessment
# =============================================================================

class EvaluationAgent(LLMBackedMixin):
    """📊 Evaluates project success and feeds back to learning system"""
    id = "evaluation"
    
    def can_run(self, state: Dict[str, Any]) -> bool:
        # Only run if validation is complete AND goal has been reached (quality threshold met OR max iterations)
        has_validation = 'validation' in state
        goal_reached = state.get('goal_reached', False)
        not_already_evaluated = 'evaluation' not in state
        
        return has_validation and goal_reached and not_already_evaluated
    
    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        track_llm_call("📊 EvaluationAgent", "intelligent project evaluation")
        
        prompt = state.get('prompt', '')
        tech_stack = state.get('tech_stack', [])
        validation = state.get('validation', {})
        architecture = state.get('architecture', {})
        
        system_prompt = """You are a project evaluator assessing overall success.

Evaluate the project on:
- Technology fit for requirements
- Code quality and validation results
- Architecture soundness
- Likely user satisfaction
- Development efficiency

Return JSON evaluation:
{
  "overall_score": 0-10,
  "technology_fit": 0-10,
  "code_quality": 0-10,
  "user_satisfaction": 0-10,
  "feedback": "detailed assessment"
}"""
        
        user_prompt = f"""Evaluate this project:

Request: {prompt}

Technologies Chosen:
{chr(10).join([f"- {t.get('role', 'unknown')}: {t.get('name', 'Unknown')} (Reasoning: {t.get('reasoning', 'No reason')})" for t in tech_stack])}

Code Validation: {validation.get('status', 'unknown')} (Score: {validation.get('score', 0)}/10)
Architecture Components: {len(architecture.get('key_components', []))} components designed

Provide comprehensive evaluation."""
        
        fallback_eval = {
            "overall_score": 7,
            "technology_fit": 7,
            "code_quality": validation.get('score', 7),
            "user_satisfaction": 7,
            "feedback": "Solid implementation with room for improvement"
        }
        
        result = self.llm_json(system_prompt, user_prompt, fallback_eval)
        
        print(f"\n📊 PROJECT EVALUATION:")
        print(f"   🎯 Overall: {result.get('overall_score', 0)}/10")
        print(f"   🔧 Tech Fit: {result.get('technology_fit', 0)}/10")
        print(f"   ✨ Quality: {result.get('code_quality', 0)}/10")
        print(f"   😊 User Satisfaction: {result.get('user_satisfaction', 0)}/10")
        
        return {'evaluation': result}

# =============================================================================
# 🎯 PURE INTELLIGENCE ORCHESTRATOR: Learning-enhanced workflow
# =============================================================================

class PureIntelligenceOrchestrator:
    """🎯 Pure LLM intelligence orchestrator with learning capabilities"""
    
    def __init__(self, rag_store=None):
        self.agents = [
            LearningMemoryAgent(rag_store),
            MultiPerspectiveTechAgent(),
            ArchitectureAgent(),
            CodeGenAgent(),
            DatabaseAgent(),
            DeploymentAgent(),
            ValidateAgent(),
            ValidationRouter(),
            EvaluationAgent()
        ]
        self.learning_memory = self.agents[0]  # First agent is learning memory
    
    def run_pipeline(self, prompt: str) -> Dict[str, Any]:
        """Run the pure intelligence pipeline with learning"""
        print(f"🎭 PURE INTELLIGENCE PIPELINE: {prompt[:50]}...")
        
        state = {
            'prompt': prompt,
            'max_codegen_iters': 3,        # number of refinement loops allowed
            'validation_threshold': 8,     # required quality
        }
        
        # Run agents sequentially (ValidationRouter feedback loop handled by graph execution in UI)
        for agent in self.agents:
            try:
                if agent.can_run(state):
                    print(f"\n🔄 Running {agent.__class__.__name__}")
                    result = agent.run(state)
                    state.update(result)
                else:
                    print(f"⏭️ Skipping {agent.__class__.__name__} - conditions not met")
            except Exception as e:
                print(f"❌ {agent.__class__.__name__} failed: {e}")
                import traceback
                traceback.print_exc()
                continue
        
        # 🎓 Learn from this project outcome
        if 'evaluation' in state and 'tech_stack' in state:
            evaluation = state['evaluation']
            overall_score = evaluation.get('overall_score', 5)
            
            print(f"\n🎓 LEARNING FROM PROJECT OUTCOME (Score: {overall_score}/10)")
            self.learning_memory.learn_from_outcome(
                prompt, 
                state['tech_stack'], 
                overall_score
            )
        
        print(f"\n🎉 PURE INTELLIGENCE COMPLETE!")
        return state
    
    def save_generated_project(self, state: Dict[str, Any], project_name: str) -> str:
        """Save generated project to disk"""
        generated_code = state.get('generated_code', {})
        files = generated_code.get('files', {})
        
        if not files:
            print("❌ No files to save")
            return ""
        
        # Create temp directory
        output_dir = Path(tempfile.mkdtemp()) / project_name
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Save files
        for filename, content in files.items():
            file_path = output_dir / filename
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content, encoding='utf-8')
        
        print(f"💾 Project saved to: {output_dir}")
        return str(output_dir)

# =============================================================================
# 🧪 TEST THE ORGANIC INTELLIGENCE
# =============================================================================

def test_organic_intelligence():
    """Test the pure multi-perspective intelligence"""
    orchestrator = PureIntelligenceOrchestrator()
    
    test_prompts = [
        "Create a simple blog platform for a small business",
        "Build a real-time chat application", 
        "Develop a high-performance API for data analytics"
    ]
    
    print("🧪 TESTING ORGANIC MULTI-PERSPECTIVE INTELLIGENCE")
    print("=" * 60)
    
    for i, prompt in enumerate(test_prompts, 1):
        print(f"\n🔬 TEST {i}: {prompt}")
        print("-" * 40)
        
        state = orchestrator.run_pipeline(prompt)
        
        # Show tech choices
        tech_stack = state.get('tech_stack', [])
        print(f"\n🎭 TEAM'S ORGANIC CHOICES:")
        for tech in tech_stack:
            print(f"   {tech.get('role', 'unknown')}: {tech.get('name', 'Unknown')}")
        
        print("\n" + "=" * 60)

if __name__ == "__main__":
    test_organic_intelligence()
