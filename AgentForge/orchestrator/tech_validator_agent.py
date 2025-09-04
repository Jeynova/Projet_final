"""
Tech Validator Agent - Validates technology selections against project requirements
Ensures tech choices make sense and are supported by the system
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from core.llm_client import LLMClient


@dataclass
class TechValidation:
    """Result of tech stack validation"""
    valid: bool
    confidence: float
    reasoning: str
    issues: List[str]
    suggested_alternative: Optional[Dict[str, Any]] = None


class TechValidatorAgent:
    """
    Validates technology selections and suggests alternatives
    - Checks if selected tech fits the project requirements
    - Validates against supported templates and patterns
    - Suggests better alternatives when needed
    """
    
    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client
        
        # Define supported tech stacks and their capabilities
        self.supported_stacks = {
            "web_api": {
                "fastapi": {"strengths": ["async", "modern", "fast"], "good_for": ["apis", "microservices"]},
                "flask": {"strengths": ["simple", "flexible"], "good_for": ["simple_apis", "prototypes"]}, 
                "django": {"strengths": ["batteries_included", "admin"], "good_for": ["complex_apps", "cms"]}
            },
            "frontend": {
                "react": {"strengths": ["popular", "ecosystem"], "good_for": ["spas", "complex_ui"]},
                "vue": {"strengths": ["gentle_learning", "flexible"], "good_for": ["gradual_adoption"]},
                "vanilla": {"strengths": ["no_deps", "fast"], "good_for": ["simple_ui", "prototypes"]}
            },
            "database": {
                "postgresql": {"strengths": ["robust", "features"], "good_for": ["complex_data", "production"]},
                "sqlite": {"strengths": ["simple", "embedded"], "good_for": ["prototypes", "small_apps"]},
                "mongodb": {"strengths": ["flexible_schema"], "good_for": ["document_data", "rapid_dev"]}
            }
        }
        
        # Common anti-patterns to avoid
        self.anti_patterns = [
            {"pattern": ["react", "django"], "issue": "Full-stack Django doesn't need React for simple cases"},
            {"pattern": ["mongodb", "small"], "issue": "MongoDB overkill for small applications"},
            {"pattern": ["postgresql", "prototype"], "issue": "SQLite sufficient for prototyping"}
        ]
    
    def validate_selection(self, tech_selection: Dict[str, Any], 
                          spec: Dict[str, Any], prompt: str) -> TechValidation:
        """Validate a technology selection against project requirements"""
        
        stack = tech_selection.get("stack", [])
        reasoning = tech_selection.get("reasoning", "")
        confidence = tech_selection.get("confidence", 0.5)
        
        issues = []
        
        # Check 1: Are all selected technologies supported?
        unsupported = self._check_supported_tech(stack)
        if unsupported:
            issues.append(f"Unsupported technologies: {', '.join(unsupported)}")
        
        # Check 2: Do technologies work well together?
        compatibility_issues = self._check_compatibility(stack)
        if compatibility_issues:
            issues.extend(compatibility_issues)
        
        # Check 3: Are technologies appropriate for project scale/complexity?
        complexity_issues = self._check_complexity_match(stack, spec, prompt)
        if complexity_issues:
            issues.extend(complexity_issues)
        
        # Check 4: Are there any anti-patterns?
        antipattern_issues = self._check_anti_patterns(stack, spec)
        if antipattern_issues:
            issues.extend(antipattern_issues)
        
        if issues:
            # Generate alternative suggestion
            alternative = self._suggest_alternative(stack, spec, prompt, issues)
            return TechValidation(
                valid=False,
                confidence=max(0.2, confidence - 0.3),  # Reduce confidence
                reasoning=f"Issues found: {'; '.join(issues)}",
                issues=issues,
                suggested_alternative=alternative
            )
        
        # Validation passed
        return TechValidation(
            valid=True,
            confidence=min(1.0, confidence + 0.1),  # Slight confidence boost
            reasoning=f"Tech stack validated successfully: {reasoning}",
            issues=[]
        )
    
    def _check_supported_tech(self, stack: List[str]) -> List[str]:
        """Check if all technologies in stack are supported"""
        unsupported = []
        
        all_supported = set()
        for category in self.supported_stacks.values():
            all_supported.update(category.keys())
        
        for tech in stack:
            if tech.lower() not in all_supported:
                unsupported.append(tech)
        
        return unsupported
    
    def _check_compatibility(self, stack: List[str]) -> List[str]:
        """Check if technologies in stack are compatible"""
        issues = []
        
        # Check for conflicting frameworks in same category
        categories = {}
        for tech in stack:
            tech_category = self._get_tech_category(tech.lower())
            if tech_category:
                if tech_category not in categories:
                    categories[tech_category] = []
                categories[tech_category].append(tech)
        
        # Flag if multiple frameworks in same category
        for category, techs in categories.items():
            if len(techs) > 1 and category in ["web_api", "frontend"]:
                issues.append(f"Multiple {category} frameworks: {', '.join(techs)}")
        
        return issues
    
    def _get_tech_category(self, tech: str) -> Optional[str]:
        """Get the category of a technology"""
        for category, techs in self.supported_stacks.items():
            if tech in techs:
                return category
        return None
    
    def _check_complexity_match(self, stack: List[str], spec: Dict[str, Any], 
                               prompt: str) -> List[str]:
        """Check if tech choices match project complexity"""
        issues = []
        
        # Estimate project complexity
        complexity = self._estimate_complexity(spec, prompt)
        
        if complexity == "simple":
            # Check for over-engineering
            if "react" in [t.lower() for t in stack] and "simple" in prompt.lower():
                issues.append("React might be overkill for a simple application")
            if "postgresql" in [t.lower() for t in stack] and not any(
                word in prompt.lower() for word in ["production", "scale", "complex"]
            ):
                issues.append("PostgreSQL might be overkill - consider SQLite for prototyping")
        
        elif complexity == "complex":
            # Check for under-engineering  
            if "sqlite" in [t.lower() for t in stack]:
                issues.append("SQLite insufficient for complex applications - consider PostgreSQL")
            if "flask" in [t.lower() for t in stack] and "large" in prompt.lower():
                issues.append("Flask might be insufficient for large applications - consider Django")
        
        return issues
    
    def _estimate_complexity(self, spec: Dict[str, Any], prompt: str) -> str:
        """Estimate project complexity based on spec and prompt"""
        
        complexity_indicators = {
            "simple": ["prototype", "simple", "basic", "small", "demo"],
            "complex": ["production", "scale", "enterprise", "large", "complex", "multiple users"]
        }
        
        prompt_lower = prompt.lower()
        
        for level, indicators in complexity_indicators.items():
            if any(indicator in prompt_lower for indicator in indicators):
                return level
        
        # Check spec for complexity indicators
        features = spec.get("features", "")
        if isinstance(features, str):
            if len(features) > 100 or "admin" in features.lower():
                return "complex"
        
        return "medium"
    
    def _check_anti_patterns(self, stack: List[str], spec: Dict[str, Any]) -> List[str]:
        """Check for known anti-patterns"""
        issues = []
        
        stack_lower = [t.lower() for t in stack]
        
        for anti_pattern in self.anti_patterns:
            pattern_techs = anti_pattern["pattern"]
            if all(tech in stack_lower for tech in pattern_techs):
                issues.append(anti_pattern["issue"])
        
        return issues
    
    def _suggest_alternative(self, original_stack: List[str], spec: Dict[str, Any], 
                           prompt: str, issues: List[str]) -> Dict[str, Any]:
        """Suggest an alternative tech stack"""
        
        complexity = self._estimate_complexity(spec, prompt)
        
        # Build alternative based on complexity and issues
        alternative_stack = []
        
        # Web framework
        if complexity == "simple":
            alternative_stack.append("flask")
        elif complexity == "complex":
            alternative_stack.append("django")
        else:
            alternative_stack.append("fastapi")
        
        # Database
        if complexity == "simple" or "prototype" in prompt.lower():
            alternative_stack.append("sqlite")
        else:
            alternative_stack.append("postgresql")
        
        # Frontend (if needed)
        if any(word in prompt.lower() for word in ["ui", "frontend", "interface"]):
            if complexity == "simple":
                alternative_stack.append("vanilla")
            else:
                alternative_stack.append("react")
        
        return {
            "stack": alternative_stack,
            "reasoning": f"Alternative for {complexity} complexity project addressing: {'; '.join(issues[:2])}",
            "confidence": 0.8,
            "changes_from_original": list(set(original_stack) - set(alternative_stack))
        }
