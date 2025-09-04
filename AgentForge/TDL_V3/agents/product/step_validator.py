"""
Step Validator for Progressive Code Generation

Handles validation, feedback generation, and quality assessment
for individual files and complete steps.
"""

import re
from typing import Dict, List, Any, Tuple, Optional


class StepValidator:
    """Validates generated code and provides feedback for improvement"""
    
    def __init__(self):
        self.validation_history = []
        
    def validate_file(self, filename: str, content: str, requirements: Dict[str, Any],
                     context: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
        """
        Validate a single file for completeness, quality, and requirements adherence
        Returns (is_valid, feedback_dict)
        """
        
        if not content or not isinstance(content, str):
            return False, {
                "score": 0,
                "issues": ["File is empty or invalid"],
                "suggestions": ["Generate actual file content"],
                "critical_errors": ["No content provided"]
            }
        
        feedback = {
            "score": 0,
            "issues": [],
            "suggestions": [],
            "critical_errors": [],
            "strengths": [],
            "line_count": 0,
            "logic_lines": 0,
            "stub_patterns": 0
        }
        
        # Basic metrics
        lines = content.split('\n')
        feedback["line_count"] = len(lines)
        
        # Count logical lines (not comments, imports, or braces)
        logic_lines = 0
        for line in lines:
            stripped = line.strip()
            if (stripped and 
                not stripped.startswith('//') and 
                not stripped.startswith('/*') and
                not stripped.startswith('import ') and
                not stripped.startswith('export ') and
                stripped not in ['{', '}', '};', ');', '*/']):
                logic_lines += 1
        
        feedback["logic_lines"] = logic_lines
        
        # 1. Length and substance validation
        min_lines = requirements.get('min_lines', 50)
        min_logic_lines = requirements.get('min_logic_lines', 15)
        
        if feedback["line_count"] < min_lines:
            feedback["critical_errors"].append(f"File too short: {feedback['line_count']} lines (need {min_lines}+)")
        
        if feedback["logic_lines"] < min_logic_lines:
            feedback["critical_errors"].append(f"Insufficient logic: {feedback['logic_lines']} lines (need {min_logic_lines}+)")
        
        # 2. Stub pattern detection
        stub_patterns = [
            (r'\{\s*\}', "Empty function bodies"),
            (r'//\s*(?:TODO|IMPLEMENT|PLACEHOLDER)', "TODO/placeholder comments"),
            (r'throw new Error\(["\']Not implemented["\']', "Not implemented errors"),
            (r'//\s*(?:Create|Update|Delete|Get)\s+\w+', "Comment-only implementations"),
            (r'class\s+\w+\s*\{\s*\w+:\s*\w+;\s*\}', "Minimal class definitions"),
            (r'export\s+class\s+\w+\s*\{\s*[\w\s:;]*\}', "Basic export classes"),
        ]
        
        total_stubs = 0
        stub_details = []
        
        for pattern, description in stub_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE | re.MULTILINE | re.DOTALL)
            count = len(matches)
            total_stubs += count
            if count > 0:
                stub_details.append(f"{description}: {count} found")
        
        feedback["stub_patterns"] = total_stubs
        
        if total_stubs > 2:
            feedback["critical_errors"].append(f"Too many stub patterns: {total_stubs}")
            feedback["issues"].extend(stub_details)
        
        # 3. File-specific requirements
        file_ext = filename.split('.')[-1].lower()
        file_type = self._determine_file_type(filename)
        
        type_validation = self._validate_file_type_requirements(content, file_type, file_ext)
        feedback["issues"].extend(type_validation["issues"])
        feedback["suggestions"].extend(type_validation["suggestions"])
        feedback["strengths"].extend(type_validation["strengths"])
        
        # 4. Quality checks
        quality_score = self._assess_code_quality(content, file_ext)
        feedback["quality_score"] = quality_score
        
        # 5. Calculate overall score
        base_score = 10
        
        # Penalize critical errors heavily
        base_score -= len(feedback["critical_errors"]) * 3
        
        # Penalize issues
        base_score -= len(feedback["issues"]) * 1
        
        # Penalize stub patterns
        base_score -= min(total_stubs, 5)
        
        # Bonus for good length
        if feedback["line_count"] >= min_lines * 2:
            base_score += 1
        
        # Bonus for logic content
        if feedback["logic_lines"] >= min_logic_lines * 2:
            base_score += 1
        
        # Quality bonus
        base_score += quality_score
        
        feedback["score"] = max(0, min(10, base_score))
        
        # Determine if valid
        is_valid = (len(feedback["critical_errors"]) == 0 and 
                   feedback["score"] >= requirements.get('min_score', 6))
        
        # Generate suggestions for improvement
        if not is_valid:
            feedback["suggestions"].extend(self._generate_improvement_suggestions(
                filename, content, feedback, requirements
            ))
        
        return is_valid, feedback
    
    def _determine_file_type(self, filename: str) -> str:
        """Determine the type of file based on name and path"""
        filename_lower = filename.lower()
        
        if 'controller' in filename_lower:
            return 'controller'
        elif 'service' in filename_lower:
            return 'service'
        elif 'model' in filename_lower:
            return 'model'
        elif 'component' in filename_lower:
            return 'component'
        elif 'route' in filename_lower or 'router' in filename_lower:
            return 'router'
        elif 'util' in filename_lower or 'helper' in filename_lower:
            return 'utility'
        elif filename_lower.endswith('.css'):
            return 'stylesheet'
        elif 'docker' in filename_lower:
            return 'docker'
        elif filename_lower.endswith('.sql'):
            return 'database'
        elif 'schema' in filename_lower:
            return 'schema'
        else:
            return 'general'
    
    def _validate_file_type_requirements(self, content: str, file_type: str, 
                                       file_ext: str) -> Dict[str, List[str]]:
        """Validate specific requirements based on file type"""
        result = {"issues": [], "suggestions": [], "strengths": []}
        
        if file_type == 'controller':
            # Controllers should have endpoints, error handling
            if not re.search(r'(router\.|app\.|@\w+\()', content):
                result["issues"].append("Missing route/endpoint definitions")
            
            if not re.search(r'(try\s*\{|catch|\.catch)', content):
                result["issues"].append("Missing error handling")
            else:
                result["strengths"].append("Has error handling")
                
        elif file_type == 'service':
            # Services should have business logic, validation
            if not re.search(r'(async|await|Promise)', content):
                result["issues"].append("Missing async operations")
            
            if re.search(r'(validate|check|verify)', content, re.IGNORECASE):
                result["strengths"].append("Has validation logic")
                
        elif file_type == 'model':
            # Models should have schema definitions, relationships
            if file_ext in ['ts', 'js']:
                if not re.search(r'(class|interface|type)', content):
                    result["issues"].append("Missing type/class definitions")
                    
            if re.search(r'(relationship|foreign|key)', content, re.IGNORECASE):
                result["strengths"].append("Has relationship definitions")
                
        elif file_type == 'component':
            # React components should have JSX, state management
            if file_ext in ['tsx', 'jsx']:
                if not re.search(r'(<\w+|jsx)', content):
                    result["issues"].append("Missing JSX elements")
                
                if re.search(r'(useState|useEffect|useContext)', content):
                    result["strengths"].append("Uses React hooks")
        
        return result
    
    def _assess_code_quality(self, content: str, file_ext: str) -> int:
        """Assess code quality and return a score 0-3"""
        quality_score = 0
        
        # Has meaningful comments
        comment_lines = len(re.findall(r'//.*\w+.*\w+', content))
        if comment_lines >= 3:
            quality_score += 1
        
        # Has proper error handling
        if re.search(r'(try\s*\{|catch|\.catch|throw)', content):
            quality_score += 1
        
        # Has proper imports/exports structure
        if re.search(r'(import.*from|export)', content):
            quality_score += 1
        
        return quality_score
    
    def _generate_improvement_suggestions(self, filename: str, content: str, 
                                        feedback: Dict[str, Any], 
                                        requirements: Dict[str, Any]) -> List[str]:
        """Generate specific suggestions for improving the file"""
        suggestions = []
        
        if feedback["line_count"] < requirements.get('min_lines', 50):
            suggestions.append(f"Expand to at least {requirements.get('min_lines', 50)} lines with complete implementations")
        
        if feedback["logic_lines"] < requirements.get('min_logic_lines', 15):
            suggestions.append("Add more business logic, validation, and error handling")
        
        if feedback["stub_patterns"] > 0:
            suggestions.append("Replace all empty functions and TODO comments with actual implementations")
        
        file_type = self._determine_file_type(filename)
        
        if file_type == 'controller':
            suggestions.append("Add comprehensive endpoint handlers with request validation and error responses")
        elif file_type == 'service':
            suggestions.append("Implement complete CRUD operations with business logic and data validation")
        elif file_type == 'model':
            suggestions.append("Define complete data models with proper relationships and validation rules")
        
        return suggestions
    
    def validate_step(self, step_name: str, generated_files: Dict[str, str], 
                     requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Validate an entire step (multiple files)"""
        
        step_result = {
            "step_name": step_name,
            "is_valid": True,
            "overall_score": 0,
            "file_results": {},
            "step_issues": [],
            "step_suggestions": [],
            "files_passed": 0,
            "files_failed": 0,
            "total_lines": 0,
            "average_score": 0
        }
        
        scores = []
        
        # Validate each file
        for filename, content in generated_files.items():
            if not isinstance(content, str):
                content = str(content) if content else ""
                
            is_valid, feedback = self.validate_file(filename, content, requirements, {})
            
            step_result["file_results"][filename] = {
                "is_valid": is_valid,
                "feedback": feedback
            }
            
            if is_valid:
                step_result["files_passed"] += 1
            else:
                step_result["files_failed"] += 1
                step_result["is_valid"] = False
            
            scores.append(feedback["score"])
            step_result["total_lines"] += feedback.get("line_count", 0)
        
        # Calculate step metrics
        if scores:
            step_result["average_score"] = sum(scores) / len(scores)
            step_result["overall_score"] = step_result["average_score"]
        
        # Step-level validation
        min_files = requirements.get('min_files_per_step', 1)
        if len(generated_files) < min_files:
            step_result["step_issues"].append(f"Too few files: {len(generated_files)} (need {min_files}+)")
            step_result["is_valid"] = False
        
        min_total_lines = requirements.get('min_total_lines_per_step', 100)
        if step_result["total_lines"] < min_total_lines:
            step_result["step_issues"].append(f"Insufficient total content: {step_result['total_lines']} lines (need {min_total_lines}+)")
        
        # Generate step-level suggestions
        if not step_result["is_valid"]:
            failed_files = [f for f, r in step_result["file_results"].items() if not r["is_valid"]]
            step_result["step_suggestions"].append(f"Regenerate failed files: {', '.join(failed_files)}")
            
            if step_result["files_failed"] > step_result["files_passed"]:
                step_result["step_suggestions"].append("Consider regenerating entire step with enhanced context")
        
        return step_result
    
    def get_retry_context(self, filename: str, validation_feedback: Dict[str, Any]) -> str:
        """Generate context for retry attempts based on validation feedback"""
        
        context_parts = [
            f"PREVIOUS ATTEMPT FAILED for {filename}",
            f"Score: {validation_feedback.get('score', 0)}/10",
            ""
        ]
        
        if validation_feedback.get("critical_errors"):
            context_parts.append("CRITICAL ERRORS TO FIX:")
            for error in validation_feedback["critical_errors"]:
                context_parts.append(f"  - {error}")
            context_parts.append("")
        
        if validation_feedback.get("issues"):
            context_parts.append("ISSUES TO ADDRESS:")
            for issue in validation_feedback["issues"]:
                context_parts.append(f"  - {issue}")
            context_parts.append("")
        
        if validation_feedback.get("suggestions"):
            context_parts.append("SPECIFIC IMPROVEMENTS NEEDED:")
            for suggestion in validation_feedback["suggestions"]:
                context_parts.append(f"  - {suggestion}")
            context_parts.append("")
        
        context_parts.append("REQUIREMENTS:")
        context_parts.append(f"  - Minimum {validation_feedback.get('min_lines', 50)} lines")
        context_parts.append(f"  - Minimum {validation_feedback.get('min_logic_lines', 15)} logic lines")
        context_parts.append("  - No empty functions or TODO comments")
        context_parts.append("  - Complete, production-ready implementation")
        
        return "\n".join(context_parts)
    
    def should_retry_step(self, step_result: Dict[str, Any], max_retries: int = 2) -> bool:
        """Determine if a step should be retried based on validation results"""
        
        # Don't retry if we've already tried too many times
        retry_count = step_result.get("retry_count", 0)
        if retry_count >= max_retries:
            return False
        
        # Retry if step failed validation
        if not step_result.get("is_valid", False):
            return True
        
        # Retry if overall score is too low
        if step_result.get("overall_score", 0) < 6:
            return True
        
        # Retry if more than half the files failed
        total_files = step_result.get("files_passed", 0) + step_result.get("files_failed", 0)
        if total_files > 0 and step_result.get("files_failed", 0) / total_files > 0.5:
            return True
        
        return False
