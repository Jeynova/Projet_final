"""
Spec Refiner Agent - Asks clarifying questions when specifications are unclear
Uses LLM to identify missing information and generate targeted questions
"""

import json
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from core.llm_client import LLMClient


@dataclass
class SpecAnalysis:
    """Analysis of spec completeness"""
    score: float
    missing_areas: List[str]
    unclear_areas: List[str]
    suggestions: List[str]


class SpecRefinerAgent:
    """
    Analyzes project specifications and asks clarifying questions
    - Evaluates spec completeness and clarity
    - Generates targeted questions for missing info
    - Refines specs based on user answers
    """
    
    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client
    
    def evaluate_completeness(self, spec: Dict[str, Any]) -> SpecAnalysis:
        """Evaluate how complete and clear the specification is"""
        
        # Core areas that should be specified
        required_areas = [
            "purpose",        # What does the app do?
            "users",          # Who uses it?
            "features",       # What features?
            "data",           # What data/entities?
            "tech_hints",     # Any tech preferences?
            "constraints"     # Performance, scale, etc.
        ]
        
        missing = []
        unclear = []
        score = 0.0
        
        # Check each required area
        for area in required_areas:
            if area not in spec or not spec[area]:
                missing.append(area)
            elif isinstance(spec[area], str) and len(spec[area].strip()) < 10:
                unclear.append(area)
            else:
                score += 1.0
        
        # Normalize score
        score = score / len(required_areas)
        
        # Generate suggestions
        suggestions = []
        if "purpose" in missing:
            suggestions.append("Define the core purpose and value proposition")
        if "users" in missing:
            suggestions.append("Identify target users and their needs")  
        if "data" in missing:
            suggestions.append("Specify what data the app will manage")
        
        return SpecAnalysis(
            score=score,
            missing_areas=missing,
            unclear_areas=unclear,
            suggestions=suggestions
        )
    
    def generate_questions(self, spec: Dict[str, Any], missing_areas: List[str]) -> List[str]:
        """Generate targeted clarifying questions"""
        
        questions = []
        
        # Map areas to specific questions
        question_templates = {
            "purpose": [
                "What is the main problem this application solves?",
                "What value does it provide to users?",
                "How would you describe this app in one sentence?"
            ],
            "users": [
                "Who are the primary users of this application?", 
                "What are their main goals when using the app?",
                "Are there different user types with different permissions?"
            ],
            "features": [
                "What are the 3-5 most important features?",
                "What actions should users be able to perform?",
                "Are there any admin or management features needed?"
            ],
            "data": [
                "What information does the app need to store?",
                "What are the main entities (users, products, orders, etc.)?",
                "How do these entities relate to each other?"
            ],
            "tech_hints": [
                "Do you have any technology preferences?",
                "Where will this be deployed (cloud, on-premise)?",
                "Any integration requirements with existing systems?"
            ],
            "constraints": [
                "How many users do you expect?",
                "Any performance requirements?",
                "Budget or timeline constraints?"
            ]
        }
        
        # Select questions for missing areas
        for area in missing_areas:
            if area in question_templates:
                # Pick the most relevant question for this area
                questions.extend(question_templates[area][:1])  # One question per area
        
        return questions
    
    def ask_clarifying_questions(self, spec: Dict[str, Any]) -> Dict[str, Any]:
        """Interactive question asking process"""
        
        analysis = self.evaluate_completeness(spec)
        
        if analysis.score > 0.7:
            return {"action": "sufficient", "spec": spec}
        
        questions = self.generate_questions(spec, analysis.missing_areas)
        
        print(f"\n🤔 I need some clarification to build this properly...")
        print(f"Spec completeness: {analysis.score:.1%}")
        print(f"Missing areas: {', '.join(analysis.missing_areas)}")
        
        answers = {}
        for i, question in enumerate(questions, 1):
            print(f"\nQ{i}: {question}")
            answer = input("A: ").strip()
            if answer:
                answers[f"clarification_{i}"] = {
                    "question": question,
                    "answer": answer
                }
        
        # Integrate answers back into spec
        refined_spec = self._integrate_answers(spec, answers, analysis.missing_areas)
        
        return {
            "action": "refined",
            "spec": refined_spec,
            "questions_asked": len(questions),
            "answers_received": len(answers)
        }
    
    def _integrate_answers(self, spec: Dict[str, Any], answers: Dict[str, Any], 
                          missing_areas: List[str]) -> Dict[str, Any]:
        """Integrate user answers back into the specification"""
        
        refined_spec = spec.copy()
        
        # Simple mapping of answers to spec areas
        for key, answer_data in answers.items():
            question = answer_data["question"].lower()
            answer = answer_data["answer"]
            
            if "problem" in question or "purpose" in question:
                refined_spec["purpose"] = answer
            elif "users" in question or "who" in question:
                refined_spec["users"] = answer
            elif "features" in question or "actions" in question:
                refined_spec["features"] = answer  
            elif "store" in question or "entities" in question:
                refined_spec["data"] = answer
            elif "technology" in question or "deploy" in question:
                refined_spec["tech_hints"] = answer
            elif "users do you expect" in question or "performance" in question:
                refined_spec["constraints"] = answer
        
        return refined_spec
    
    def generate_smart_questions(self, prompt: str, spec: Dict[str, Any]) -> List[str]:
        """Use LLM to generate contextual questions based on the prompt"""
        
        system_prompt = """
        You are a product analyst helping to clarify project requirements.
        Given a user's project description, identify the most important missing information
        and generate 3-5 specific, actionable questions that would help build the project successfully.
        
        Focus on:
        - Technical architecture decisions
        - Data model clarity  
        - User experience requirements
        - Integration needs
        - Non-functional requirements
        
        Return questions as a JSON list.
        """
        
        user_prompt = f"""
        Project description: "{prompt}"
        Current spec: {json.dumps(spec, indent=2)}
        
        What are the most important questions I should ask to clarify this project?
        """
        
        try:
            response = self.llm_client.complete(
                system_prompt,
                user_prompt,
                max_tokens=500,
                temperature=0.3
            )
            
            # Try to parse as JSON, fallback to simple parsing
            try:
                questions = json.loads(response)
                if isinstance(questions, list):
                    return questions[:5]  # Max 5 questions
            except json.JSONDecodeError:
                # Fallback: extract questions from text
                lines = response.split('\n')
                questions = [
                    line.strip('- ').strip() 
                    for line in lines 
                    if line.strip().startswith(('Q:', '-', '1.', '2.', '3.', '4.', '5.'))
                ][:5]
                return questions
                
        except Exception as e:
            print(f"Warning: Failed to generate smart questions: {e}")
            # Fallback to template questions
            return self.generate_questions(spec, ["purpose", "users", "features"])
        
        return []
