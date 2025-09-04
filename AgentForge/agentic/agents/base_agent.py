"""
Base Agent Classes for AgentForge Agentic System
"""

from typing import Dict, Any, List, Optional
import json
import random
from abc import ABC, abstractmethod
from datetime import datetime


class BaseAgent(ABC):
    """Base class for all agents in the system"""
    
    def __init__(self, name: str, role: str, model: str):
        self.name = name
        self.role = role
        self.model = model
        self.decisions_made = []
        self.reviews_given = []
        
        # Initialize LLM client
        from core.llm_client import LLMClient
        self.llm = LLMClient(preferred_model=model)
        
    def log_decision(self, decision: str, context: str = ""):
        """Log a decision made by this agent"""
        self.decisions_made.append({
            'decision': decision,
            'context': context,
            'timestamp': datetime.now().isoformat()
        })
        
    def log_review(self, review: Dict[str, Any]):
        """Log a review given by this agent"""
        self.reviews_given.append({
            **review,
            'timestamp': datetime.now().isoformat(),
            'reviewer': self.name
        })
    
    @abstractmethod
    def make_decision(self, context: Dict[str, Any], options: List[str]) -> str:
        """Make a decision based on context and available options"""
        pass
    
    @abstractmethod
    def review_code(self, filename: str, code: str) -> Dict[str, Any]:
        """Review code and provide feedback"""
        pass
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about this agent's activity"""
        return {
            'name': self.name,
            'role': self.role,
            'model': self.model,
            'decisions_count': len(self.decisions_made),
            'reviews_count': len(self.reviews_given),
            'last_activity': self.decisions_made[-1]['timestamp'] if self.decisions_made else None
        }


class SimpleAgent(BaseAgent):
    """Simple implementation of an agent that makes independent decisions"""
    
    def make_decision(self, context: Dict[str, Any], options: List[str]) -> str:
        """Agent makes independent decision using LLM or fallback"""
        try:
            prompt = f"""You are {self.name}, a {self.role}.
            
Context: {context.get('prompt', 'project')}

Choose ONE option that best fits your expertise:
{json.dumps(options, indent=2)}

Return ONLY the chosen option (exact text):"""
            
            response = self.llm.get_raw_response(
                system_prompt=f"You are {self.name}, expert {self.role}. Make independent decisions.",
                user_prompt=prompt
            )
            
            if response:
                # Find matching option
                for option in options:
                    if option.lower() in response.lower():
                        decision = option
                        self.log_decision(decision, context.get('prompt', ''))
                        print(f"🎯 {self.name}: chose '{decision}'")
                        return decision
                        
            # Fallback: random choice
            decision = random.choice(options)
            self.log_decision(decision, f"fallback_random: {context.get('prompt', '')}")
            print(f"🎲 {self.name}: random choice '{decision}'")
            return decision
            
        except Exception as e:
            print(f"❌ {self.name}: decision failed: {e}")
            decision = random.choice(options)
            self.log_decision(decision, f"error_fallback: {str(e)}")
            return decision
    
    def review_code(self, filename: str, code: str) -> Dict[str, Any]:
        """Agent reviews code and provides feedback"""
        try:
            # Count metrics
            lines = len(code.strip().split('\n'))
            has_imports = 'import ' in code or 'from ' in code
            has_functions = 'def ' in code or 'class ' in code
            
            # Simple scoring based on code characteristics
            score = 5.0
            issues = []
            
            if lines >= 10:
                score += 2.0
            else:
                issues.append(f"File too short ({lines} lines)")
                
            if has_imports:
                score += 1.0
            else:
                issues.append("Missing imports")
                
            if has_functions:
                score += 2.0
            else:
                issues.append("No functions or classes")
                
            # Random variation to simulate agent thinking
            score += random.uniform(-0.5, 1.0)
            score = min(10.0, max(1.0, score))
            
            review = {
                'filename': filename,
                'agent': self.name,
                'score': round(score, 1),
                'lines': lines,
                'issues': issues,
                'approved': score >= 6.0
            }
            
            self.log_review(review)
            return review
            
        except Exception as e:
            print(f"❌ {self.name}: review failed for {filename}: {e}")
            return {
                'filename': filename,
                'agent': self.name,
                'score': 5.0,
                'lines': 0,
                'issues': [f"Review error: {str(e)}"],
                'approved': False
            }
    
    def _clean_code(self, raw_response: str) -> str:
        """Clean up LLM response to extract just the code"""
        lines = raw_response.strip().split('\n')
        
        # Remove markdown code blocks
        if lines[0].startswith('```'):
            lines = lines[1:]
        if lines and lines[-1].startswith('```'):
            lines = lines[:-1]
            
        # Remove explanation text (common LLM behavior)
        code_lines = []
        in_code = False
        
        for line in lines:
            # Skip obvious explanation lines
            if line.strip().lower().startswith(('here', 'this', 'the above', 'explanation')):
                continue
            if '# explanation:' in line.lower() or '# note:' in line.lower():
                continue
                
            # Detect code patterns
            if any(pattern in line for pattern in ['import ', 'from ', 'def ', 'class ', '=', '{']):
                in_code = True
                
            if in_code or line.strip().startswith(('#', '//', '/*')):
                code_lines.append(line)
                
        return '\n'.join(code_lines) if code_lines else raw_response.strip()
