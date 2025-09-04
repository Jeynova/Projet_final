"""
Smart Orchestrator - Enhanced Agentic System
Uses intelligent decision making and question asking.
"""

import os
import json
from typing import Dict, Any, List, Optional
from pathlib import Path
from dataclasses import dataclass
from enum import Enum
from colorama import Fore, Style

from .memory_agent import MemoryAgent
from .spec_refiner_agent import SpecRefinerAgent
from .tech_validator_agent import TechValidatorAgent
from .validation_agent import ValidationAgent
from .infra_agent import InfraAgent
from core.llm_client import LLMClient


class Mode(Enum):
    TEMPLATES_ONLY = "templates"      # Mode A - Deterministic
    AGENT_FIRST = "agent_first"       # Mode B - Full Agentic  
    HYBRID = "hybrid"                 # Mode C - Smart mix


@dataclass
class AgenticDecision:
    """Represents a decision made by an agent"""
    action: str
    confidence: float
    reasoning: str
    data: Dict[str, Any]
    skip_reason: Optional[str] = None


class SmartOrchestrator:
    """
    Enhanced orchestrator that makes intelligent decisions about:
    - Which agents to call (avoid redundancy)
    - When to ask clarifying questions  
    - When to use templates vs generate code
    - When to trust agent outputs vs validate
    """
    
    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client
        self.memory_agent = MemoryAgent(llm_client)
        self.spec_refiner = SpecRefinerAgent(llm_client)  
        self.tech_validator = TechValidatorAgent(llm_client)
        self.validation_agent = ValidationAgent(llm_client)
        self.infra_agent = InfraAgent(llm_client)
        
        # Configuration
        self.agentic_mode = os.getenv("AGENTFORGE_AGENTIC", "1") == "1"
        self.ask_questions = os.getenv("AGENTFORGE_ASK", "1") == "1"
        self.mode = Mode(os.getenv("AGENTFORGE_MODE", "hybrid"))
        
    def _check_memory_for_similar_project(self, prompt: str, tech_requirements: List[str]) -> Dict[str, Any]:
        """Check if we have similar successful projects in memory"""
        return self.memory_agent.find_similar_projects(prompt, tech_requirements)
    
    def _evaluate_spec_completeness(self, spec: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate how complete and clear the spec is"""
        analysis = self.spec_refiner.evaluate_completeness(spec)
        return {
            "score": analysis.score,
            "missing_areas": analysis.missing_areas,
            "unclear_areas": analysis.unclear_areas,
            "suggestions": analysis.suggestions
        }
    
    def _check_existing_templates(self, tech_stack: List[str]) -> Dict[str, Any]:
        """Check if we have working templates for this tech stack"""
        templates_dir = Path(__file__).parent.parent / "templates"
        available = []
        for tech in tech_stack:
            template_path = templates_dir / f"{tech}_template"
            if template_path.exists():
                available.append(tech)
        return {"available_templates": available, "coverage": len(available) / len(tech_stack) if tech_stack else 0}
    
    def _make_decision(self, context: str, question: str, tools_used: List[str]) -> AgenticDecision:
        """Use LLM to make intelligent decisions"""
        
        system_prompt = """
        You are a smart project orchestrator. Make intelligent decisions about:
        
        1. AVOID REDUNDANCY: Check memory first before calling other agents
        2. ASK SMART QUESTIONS: When specs are unclear, ask specific clarifying questions  
        3. USE WHAT WORKS: Prefer existing templates/patterns when they fit
        4. TRUST BUT VERIFY: Let agents work but validate critical outputs
        
        Respond with JSON containing:
        - action: what to do next (continue, use_memory_template, ask_questions, etc.)
        - confidence: 0.0-1.0 how sure you are
        - reasoning: why this decision
        - skip_reason: if skipping an agent, why (optional)
        
        Available context: {context}
        Tools used: {tools_used}
        """
        
        try:
            response = self.llm_client.complete(
                system_prompt.format(context=context, tools_used=tools_used),
                question,
                max_tokens=300,
                temperature=0.3
            )
            
            # Try to parse as JSON
            decision_data = json.loads(response)
            
            return AgenticDecision(
                action=decision_data.get("action", "continue"),
                confidence=decision_data.get("confidence", 0.5),
                reasoning=decision_data.get("reasoning", "LLM decision"),
                data={},
                skip_reason=decision_data.get("skip_reason")
            )
            
        except Exception as e:
            print(f"Warning: LLM decision failed: {e}")
            # Fallback to simple heuristic decision
            return AgenticDecision(
                action="continue",
                confidence=0.5,
                reasoning="Fallback decision due to LLM error",
                data={}
            )
    
    def orchestrate(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main orchestration logic - makes smart decisions about agent flow
        """
        prompt = state.get("prompt", "")
        spec = state.get("spec", {})
        
        print(f"{Fore.CYAN}🧠 Smart Orchestrator starting...{Style.RESET_ALL}")
        
        # Step 1: Memory check - do we have similar successful projects?
        memory_decision = self._check_memory_first(prompt, spec)
        if memory_decision.skip_reason:
            print(f"{Fore.GREEN}⚡ Skipping agents: {memory_decision.skip_reason}{Style.RESET_ALL}")
            return self._use_memory_template(state, memory_decision.data)
        
        # Step 2: Spec refinement - ask questions if needed
        if self.ask_questions:
            spec_decision = self._refine_spec_if_needed(state)
            if spec_decision.action == "ask_questions":
                return self._ask_clarifying_questions(state, spec_decision.data)
            state["spec"] = spec_decision.data
        
        # Step 3: Tech selection with validation
        tech_decision = self._select_and_validate_tech(state)
        state["tech_selection"] = tech_decision.data
        
        # Step 4: Code generation strategy
        codegen_decision = self._decide_codegen_strategy(state)
        
        if codegen_decision.action == "use_templates":
            return self._use_templates(state, codegen_decision.data)
        elif codegen_decision.action == "agent_generate":
            return self._agent_generate(state, codegen_decision.data)  
        else:  # hybrid
            return self._hybrid_generate(state, codegen_decision.data)
    
    def _check_memory_first(self, prompt: str, spec: Dict[str, Any]) -> AgenticDecision:
        """Check memory for similar projects before doing expensive operations"""
        
        # Extract basic tech requirements
        tech_hints = []
        for word in prompt.lower().split():
            if word in ['api', 'rest', 'fastapi', 'flask', 'django']:
                tech_hints.append('web_api')
            elif word in ['react', 'vue', 'angular', 'frontend']:
                tech_hints.append('frontend')  
            elif word in ['database', 'db', 'sql', 'mongodb']:
                tech_hints.append('database')
        
        memory_result = self.memory_agent.find_similar_projects(prompt, tech_hints)
        
        if memory_result.get("confidence", 0) > 0.8:
            return AgenticDecision(
                action="use_memory_template",
                confidence=memory_result["confidence"],
                reasoning=f"Found highly similar project: {memory_result['project_name']}",
                data=memory_result,
                skip_reason="High-confidence memory match found"
            )
        
        return AgenticDecision(
            action="continue",
            confidence=0.5,
            reasoning="No strong memory match, proceed with normal flow", 
            data={}
        )
    
    def _refine_spec_if_needed(self, state: Dict[str, Any]) -> AgenticDecision:
        """Ask clarifying questions if spec is incomplete"""
        
        spec = state.get("spec", {})
        completeness = self._evaluate_spec_completeness(spec)
        
        if completeness["score"] < 0.7:  # Spec is incomplete
            questions = self.spec_refiner.generate_questions(spec, completeness["missing_areas"])
            return AgenticDecision(
                action="ask_questions", 
                confidence=completeness["score"],
                reasoning=f"Spec completeness: {completeness['score']:.1%}, need clarification",
                data={"questions": questions, "missing_areas": completeness["missing_areas"]}
            )
        
        return AgenticDecision(
            action="continue",
            confidence=completeness["score"],
            reasoning="Spec is sufficiently complete",
            data=spec
        )
    
    def _select_and_validate_tech(self, state: Dict[str, Any]) -> AgenticDecision:
        """Select tech stack and validate it makes sense"""
        
        # Use existing tech_selector logic but with validation
        from .tech_selector_agent import run_tech_selector
        
        tech_result = run_tech_selector(state)
        tech_selection = tech_result.get("tech_selection", {})
        
        # Validate the selection
        validation = self.tech_validator.validate_selection(
            tech_selection, 
            state.get("spec", {}),
            state.get("prompt", "")
        )
        
        if validation["valid"]:
            return AgenticDecision(
                action="tech_selected",
                confidence=validation["confidence"], 
                reasoning=validation["reasoning"],
                data=tech_selection
            )
        else:
            # Tech validator suggests alternatives
            return AgenticDecision(
                action="tech_corrected",
                confidence=validation["confidence"],
                reasoning=f"Original selection invalid: {validation['issues']}",
                data=validation["suggested_alternative"]
            )
    
    def _decide_codegen_strategy(self, state: Dict[str, Any]) -> AgenticDecision:
        """Decide whether to use templates, agents, or hybrid approach"""
        
        tech_selection = state.get("tech_selection", {})
        tech_stack = tech_selection.get("stack", [])
        
        # Check template availability
        template_coverage = self._check_template_coverage(tech_stack)
        
        if self.mode == Mode.TEMPLATES_ONLY:
            return AgenticDecision(
                action="use_templates",
                confidence=template_coverage,
                reasoning="Templates-only mode configured",
                data={"coverage": template_coverage}
            )
        elif self.mode == Mode.AGENT_FIRST:
            return AgenticDecision(
                action="agent_generate", 
                confidence=0.8,
                reasoning="Agent-first mode configured",
                data={"use_templates_as_reference": template_coverage > 0.5}
            )
        else:  # HYBRID
            if template_coverage > 0.8:
                return AgenticDecision(
                    action="use_templates",
                    confidence=template_coverage,
                    reasoning="High template coverage, use deterministic approach",
                    data={"coverage": template_coverage}
                )
            elif template_coverage > 0.3:
                return AgenticDecision(
                    action="hybrid_generate",
                    confidence=0.7,
                    reasoning="Partial template coverage, use hybrid approach", 
                    data={"template_coverage": template_coverage}
                )
            else:
                return AgenticDecision(
                    action="agent_generate",
                    confidence=0.6,
                    reasoning="Low template coverage, let agents generate",
                    data={"fallback_templates": template_coverage > 0}
                )
    
    def _check_template_coverage(self, tech_stack: List[str]) -> float:
        """Check how much of the tech stack is covered by existing templates"""
        if not tech_stack:
            return 0.0
            
        templates_dir = Path(__file__).parent.parent / "templates"
        covered = 0
        
        for tech in tech_stack:
            template_paths = [
                templates_dir / f"{tech}_template",
                templates_dir / f"{tech.lower()}_template", 
                templates_dir / f"general_{tech}_template"
            ]
            if any(p.exists() for p in template_paths):
                covered += 1
                
        return covered / len(tech_stack)
    
    def _use_memory_template(self, state: Dict[str, Any], memory_data: Dict[str, Any]) -> Dict[str, Any]:
        """Use a successful project from memory as template"""
        print(f"{Fore.GREEN}📋 Using memory template: {memory_data['project_name']}{Style.RESET_ALL}")
        
        # Copy the successful project structure
        template_path = memory_data.get("project_path")
        if template_path and Path(template_path).exists():
            # Use template rendering logic
            from .utils import render_dir
            project_dir = Path(state["artifacts_dir"]) / state["name"]
            render_dir(template_path, project_dir, state)
            
            state["logs"].append(f"Used memory template: {memory_data['project_name']}")
            state["status"] = "completed"
            return state
        
        # Fallback if template not found
        state["logs"].append("Memory template not found, falling back to normal flow")
        return state
    
    def _ask_clarifying_questions(self, state: Dict[str, Any], question_data: Dict[str, Any]) -> Dict[str, Any]:
        """Present questions to user and wait for answers"""
        print(f"{Fore.YELLOW}❓ Need clarification on: {question_data['missing_areas']}{Style.RESET_ALL}")
        
        for i, question in enumerate(question_data["questions"], 1):
            print(f"{Fore.YELLOW}Q{i}: {question}{Style.RESET_ALL}")
            answer = input(f"A{i}: ").strip()
            if answer:
                # Update spec with answer
                # This is simplified - in practice would parse answers more intelligently
                state["spec"][f"clarification_{i}"] = answer
        
        state["logs"].append(f"Asked {len(question_data['questions'])} clarifying questions")
        return state
    
    def _use_templates(self, state: Dict[str, Any], template_data: Dict[str, Any]) -> Dict[str, Any]:
        """Use deterministic template-based generation"""
        print(f"{Fore.GREEN}📋 Using templates (coverage: {template_data['coverage']:.1%}){Style.RESET_ALL}")
        
        # Use existing scaffolder logic
        from .agents import scaffolder
        return scaffolder(state)
    
    def _agent_generate(self, state: Dict[str, Any], agent_data: Dict[str, Any]) -> Dict[str, Any]:
        """Let agents generate everything from scratch"""  
        print(f"{Fore.BLUE}🤖 Full agent generation{Style.RESET_ALL}")
        
        # Use existing codegen logic
        from .agents import codegen
        return codegen(state)
    
    def _hybrid_generate(self, state: Dict[str, Any], hybrid_data: Dict[str, Any]) -> Dict[str, Any]:
        """Mix of templates and agent generation"""
        print(f"{Fore.MAGENTA}🔄 Hybrid generation (templates: {hybrid_data['template_coverage']:.1%}){Style.RESET_ALL}")
        
        # Start with templates for covered parts
        state = self._use_templates(state, {"coverage": hybrid_data["template_coverage"]})
        
        # Let agents fill in the gaps
        state = self._agent_generate(state, {"fill_gaps": True})
        
        return state
