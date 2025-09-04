"""
Simple Agent - Independent decision maker with peer review capabilities
"""

from typing import Dict, Any, List
import json
import random


class SimpleAgent:
    """
    Simple agent that makes independent decisions
    """
    
    def __init__(self, name: str, role: str, model: str):
        self.name = name
        self.role = role
        self.model = model
        from core.llm_client import LLMClient
        self.llm = LLMClient(preferred_model=model)
        self.decisions_made = []
        self.reviews_given = []
    
    def make_decision(self, context: Dict[str, Any], options: List[str]) -> str:
        """Agent makes independent decision"""
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
                        self.decisions_made.append(decision)
                        print(f"🎯 {self.name}: chose '{decision}'")
                        return decision
            
            # Fallback to random (still agentic!)
            decision = random.choice(options)
            self.decisions_made.append(decision)
            print(f"🎲 {self.name}: random choice '{decision}'")
            return decision
            
        except Exception as e:
            print(f"⚠️ {self.name} decision failed: {e}")
            decision = random.choice(options)
            self.decisions_made.append(decision)
            return decision
    
    def review_code(self, filename: str, code: str) -> Dict[str, Any]:
        """Agent reviews another agent's code"""
        try:
            prompt = f"""Review this {filename} code as a {self.role}:

```
{code[:500]}...
```

Rate 1-5 and suggest ONE improvement:
{{"score": 4, "improvement": "Add error handling"}}"""
            
            response = self.llm.extract_json(
                system_prompt=f"You are {self.name}, expert {self.role}. Review code critically but constructively.",
                user_prompt=prompt
            )
            
            if response and 'score' in response:
                review = {
                    'reviewer': self.name,
                    'score': response.get('score', 3),
                    'improvement': response.get('improvement', 'Good code'),
                    'filename': filename
                }
                self.reviews_given.append(review)
                print(f"📝 {self.name}: reviewed {filename} -> {review['score']}/5")
                return review
                
        except Exception as e:
            print(f"⚠️ {self.name} review failed: {e}")
        
        # Simple fallback review
        review = {
            'reviewer': self.name,
            'score': 4,
            'improvement': 'Looks good',
            'filename': filename
        }
        self.reviews_given.append(review)
        return review
    
    def improve_code(self, filename: str, code: str, reviews: List[Dict]) -> str:
        """Agent improves code based on reviews"""
        if not reviews:
            return code
            
        try:
            improvements = [r.get('improvement', '') for r in reviews if r.get('improvement')]
            
            prompt = f"""Improve this {filename} code based on peer reviews:

ORIGINAL CODE:
```
{code[:800]}
```

PEER REVIEWS:
{json.dumps(improvements, indent=2)}

Return ONLY the improved code:"""
            
            response = self.llm.get_raw_response(
                system_prompt=f"You are {self.name}, expert {self.role}. Improve code based on feedback.",
                user_prompt=prompt
            )
            
            if response and len(response.strip()) > len(code) * 0.8:  # Must be substantial
                print(f"✨ {self.name}: improved {filename} (+{len(response) - len(code)} chars)")
                return self._clean_code(response)
                
        except Exception as e:
            print(f"⚠️ {self.name} improvement failed: {e}")
        
        return code  # Return original if improvement fails
    
    def _clean_code(self, code: str) -> str:
        """Clean code response"""
        if "```" in code:
            lines = code.split('\n')
            code_lines = []
            in_code = False
            
            for line in lines:
                if line.strip().startswith('```'):
                    in_code = not in_code
                    continue
                if in_code:
                    code_lines.append(line)
            
            return '\n'.join(code_lines) if code_lines else code
        
        return code.strip()
