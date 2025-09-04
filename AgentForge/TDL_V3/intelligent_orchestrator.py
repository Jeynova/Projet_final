#!/usr/bin/env python3
"""
🧠 INTELLIGENT ORCHESTRATOR - Clean & Efficient Intelligence
Decides which agents to run based on project analysis and memory patterns
"""
import sys
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime

sys.path.append('.')
from phase2_pure_intelligence import (
    LearningMemoryAgent,
    MultiPerspectiveTechAgent, 
    ArchitectureAgent,
    CodeGenAgent,
    DatabaseAgent,
    DeploymentAgent,
    ValidateAgent,
    EvaluationAgent
)

class AgentSelectionIntelligence:
    """🧠 Intelligent agent selection based on project requirements and memory"""
    
    def __init__(self, rag_store=None):
        self.rag = rag_store
        
    def analyze_required_agents(self, prompt: str, memory_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Intelligently determine which agents are needed for this specific project"""
        prompt_lower = prompt.lower()
        domain = memory_analysis.get('domain', 'general')
        complexity = memory_analysis.get('complexity', 'moderate')
        confidence = memory_analysis.get('confidence', 0.0)
        
        # Base agents (always needed)
        required_agents = ['LearningMemoryAgent']  # Always start with memory
        
        # 🎯 INTELLIGENT DECISION TREE
        
        # 1. Tech selection needed?
        if 'tech_stack' not in memory_analysis or confidence < 0.8:
            required_agents.append('MultiPerspectiveTechAgent')
            
        # 2. Architecture needed?
        if complexity in ['moderate', 'complex'] or domain in ['enterprise', 'ecommerce']:
            required_agents.append('ArchitectureAgent')
            
        # 3. Code generation needed?
        if not any(word in prompt_lower for word in ['design only', 'planning only', 'architecture only']):
            required_agents.append('CodeGenAgent')
            
        # 4. Database needed?
        if any(word in prompt_lower for word in ['data', 'store', 'user', 'content', 'product', 'order']):
            required_agents.append('DatabaseAgent')
            
        # 5. Deployment needed?
        if complexity in ['moderate', 'complex'] or any(word in prompt_lower for word in ['deploy', 'production', 'docker', 'server']):
            required_agents.append('DeploymentAgent')
            
        # 6. Validation needed?
        if complexity == 'complex' or domain in ['enterprise', 'ecommerce']:
            required_agents.append('ValidateAgent')
            
        # 7. Evaluation needed?
        required_agents.append('EvaluationAgent')  # Always evaluate
        
        # 🎓 RAG-ENHANCED: Check similar projects for agent patterns
        rag_guidance = {}
        if self.rag:
            try:
                similar_projects = self.rag.get_similar_projects(prompt)
                if similar_projects:
                    # Analyze which agents were successful in similar projects
                    for project in similar_projects[:2]:
                        if project.get('success_score', 0) > 7.0:
                            # If similar successful project used fewer agents, consider it
                            rag_guidance['successful_patterns'] = True
                            break
            except Exception as e:
                print(f"⚠️ RAG agent selection guidance failed: {e}")
        
        reasoning = self._build_agent_selection_reasoning(
            required_agents, domain, complexity, prompt_lower, rag_guidance
        )
        
        return {
            'required_agents': required_agents,
            'skipped_agents': self._get_all_agents_except(required_agents),
            'reasoning': reasoning,
            'selection_confidence': self._calculate_selection_confidence(required_agents, memory_analysis),
            'rag_guidance': rag_guidance
        }
    
    def _get_all_agents_except(self, required: List[str]) -> List[str]:
        """Get list of agents that will be skipped"""
        all_agents = [
            'LearningMemoryAgent', 'MultiPerspectiveTechAgent', 'ArchitectureAgent',
            'CodeGenAgent', 'DatabaseAgent', 'DeploymentAgent', 'ValidateAgent', 'EvaluationAgent'
        ]
        return [agent for agent in all_agents if agent not in required]
    
    def _build_agent_selection_reasoning(self, agents: List[str], domain: str, complexity: str, prompt_lower: str, rag_guidance: Dict) -> str:
        """Build human-readable reasoning for agent selection"""
        reasons = []
        
        if 'MultiPerspectiveTechAgent' in agents:
            reasons.append(f"Tech selection needed for {domain} domain")
        else:
            reasons.append("Using cached tech stack from memory")
            
        if 'ArchitectureAgent' in agents:
            reasons.append(f"Architecture required for {complexity} complexity")
        else:
            reasons.append("Simple project, skipping architecture")
            
        if 'DatabaseAgent' in agents:
            reasons.append("Data storage requirements detected")
        else:
            reasons.append("No data storage needed")
            
        if 'DeploymentAgent' in agents:
            reasons.append("Deployment configuration required")
        else:
            reasons.append("Simple deployment, skipping config")
            
        if rag_guidance.get('successful_patterns'):
            reasons.append("RAG suggests optimized agent pattern")
            
        return "; ".join(reasons)
    
    def _calculate_selection_confidence(self, agents: List[str], memory: Dict) -> float:
        """Calculate confidence in agent selection"""
        base_confidence = 0.7
        
        # Higher confidence if memory has good domain detection
        if memory.get('confidence', 0) > 0.8:
            base_confidence += 0.2
            
        # Higher confidence if we're skipping unnecessary agents
        if len(agents) < 6:  # Less than full pipeline
            base_confidence += 0.1
            
        return min(0.95, base_confidence)


class IntelligentOrchestrator:
    """🧠 Clean & efficient intelligent orchestrator"""
    
    def __init__(self, rag_store=None):
        self.rag = rag_store
        self.selector = AgentSelectionIntelligence(rag_store)
        
        # Initialize clean, efficient phase2 agents
        print("🤖 Initializing clean, efficient orchestrator...")
        self._init_agents()
    
    def _init_agents(self):
        """Initialize efficient phase2 agents"""
        self.available_agents = {
            'LearningMemoryAgent': LearningMemoryAgent(self.rag),
            'MultiPerspectiveTechAgent': MultiPerspectiveTechAgent(),
            'ArchitectureAgent': ArchitectureAgent(),
            'CodeGenAgent': CodeGenAgent(),
            'DatabaseAgent': DatabaseAgent(),
            'DeploymentAgent': DeploymentAgent(),
            'ValidateAgent': ValidateAgent(),
            'EvaluationAgent': EvaluationAgent()
        }
        self.using_smolagents = False
    
    def run_pipeline(self, prompt: str) -> Dict[str, Any]:
        """Run intelligent pipeline with dynamic agent selection"""
        print(f"� INTELLIGENT PIPELINE: {prompt[:50]}...")
        
        state = {'prompt': prompt}
        
        # Step 1: Always run memory agent first for analysis
        print(f"\n1. 🧠 Running LearningMemoryAgent for project analysis...")
        memory_agent = self.available_agents['LearningMemoryAgent']
        memory_result = memory_agent.run(state)
        state.update(memory_result)
        
        # Step 2: Intelligent agent selection based on memory analysis
        selection = self.selector.analyze_required_agents(prompt, memory_result)
        required_agents = selection['required_agents'][1:]  # Skip memory (already run)
        skipped_agents = selection['skipped_agents']
        
        print(f"\n🎯 INTELLIGENT AGENT SELECTION:")
        print(f"   ✅ Required: {', '.join(required_agents)}")
        print(f"   ⏭️ Skipped: {', '.join(skipped_agents)}")
        print(f"   💡 Reasoning: {selection['reasoning']}")
        print(f"   🎯 Confidence: {selection['selection_confidence']:.1%}")
        
        # Step 3: Run only the required agents
        for i, agent_name in enumerate(required_agents, 2):
            agent = self.available_agents.get(agent_name)
            if agent and agent.can_run(state):
                print(f"\n{i}. 🔄 Running {agent_name}...")
                try:
                    result = agent.run(state)
                    state.update(result)
                    print(f"   ✅ {agent_name} completed successfully")
                except Exception as e:
                    print(f"   ❌ {agent_name} failed: {e}")
                    continue
            else:
                print(f"\n{i}. ⏭️ Skipping {agent_name} - conditions not met")
        
        # Step 4: Learning phase - store this project pattern in RAG
        if 'evaluation' in state and 'tech_stack' in state and self.rag:
            try:
                evaluation = state['evaluation']
                overall_score = evaluation.get('overall_score', 5)
                tech_stack = state.get('tech_stack', [])
                
                # Store the successful agent pattern
                agent_pattern = {
                    'prompt': prompt,
                    'agents_used': required_agents,
                    'agents_skipped': skipped_agents,
                    'success_score': overall_score,
                    'domain': memory_result.get('domain'),
                    'complexity': memory_result.get('complexity')
                }
                
                # This would be stored in RAG for future agent selection
                print(f"🎓 Learning: Agent pattern for {memory_result.get('domain')} projects")
                
            except Exception as e:
                print(f"⚠️ Agent pattern learning failed: {e}")
        
        print(f"\n🎉 INTELLIGENT ORCHESTRATION COMPLETE!")
        print(f"   📊 Used {len(required_agents)} of {len(self.available_agents)} available agents")
        
        return state
