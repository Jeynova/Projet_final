"""
Validation Agent - Validates generated code and project structure
Runs linting, security checks, and basic functionality tests
"""

import os
import subprocess
from typing import Dict, Any, List, Optional
from pathlib import Path
from dataclasses import dataclass

from core.llm_client import LLMClient


@dataclass
class ValidationResult:
    """Result of code validation"""
    passed: bool
    confidence: float
    issues: List[str]
    warnings: List[str]
    fixes_applied: List[str]
    go_no_go: str  # "GO", "NO_GO", "CONDITIONAL_GO"


class ValidationAgent:
    """
    Validates generated projects for quality and security
    - Runs ruff for linting and formatting
    - Runs bandit for security analysis  
    - Runs pytest for functionality tests
    - Validates dependency versions and security
    - Makes GO/NO_GO decisions
    """
    
    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client
        
        # Validation thresholds
        self.thresholds = {
            "max_lint_errors": 5,
            "max_security_issues": 2,
            "min_test_coverage": 0.7,
            "max_critical_vulns": 0
        }
    
    def validate_project(self, project_dir: Path, spec: Dict[str, Any]) -> ValidationResult:
        """Run comprehensive validation on generated project"""
        
        if not project_dir.exists():
            return ValidationResult(
                passed=False,
                confidence=0.0,
                issues=["Project directory does not exist"],
                warnings=[],
                fixes_applied=[],
                go_no_go="NO_GO"
            )
        
        print(f"🔍 Validating project: {project_dir}")
        
        issues = []
        warnings = []
        fixes_applied = []
        
        # 1. Code linting and formatting
        lint_result = self._run_lint_checks(project_dir)
        if lint_result["errors"]:
            if len(lint_result["errors"]) > self.thresholds["max_lint_errors"]:
                issues.extend(lint_result["errors"][:5])  # Show first 5
            else:
                warnings.extend(lint_result["errors"])
        
        fixes_applied.extend(lint_result["fixes"])
        
        # 2. Security analysis
        security_result = self._run_security_checks(project_dir)
        if security_result["critical"]:
            issues.extend(security_result["critical"])
        if security_result["medium"]:
            warnings.extend(security_result["medium"][:3])
        
        # 3. Test validation
        test_result = self._run_test_validation(project_dir)
        if test_result["failed_tests"]:
            if len(test_result["failed_tests"]) > 2:
                issues.append(f"Multiple test failures: {len(test_result['failed_tests'])} tests failed")
            else:
                warnings.extend(test_result["failed_tests"])
        
        # 4. Dependency validation
        deps_result = self._validate_dependencies(project_dir)
        if deps_result["critical_vulns"]:
            issues.extend(deps_result["critical_vulns"])
        if deps_result["outdated"]:
            warnings.extend(deps_result["outdated"][:3])
        
        # 5. Project structure validation
        structure_result = self._validate_structure(project_dir, spec)
        if structure_result["missing_critical"]:
            issues.extend(structure_result["missing_critical"])
        if structure_result["missing_optional"]:
            warnings.extend(structure_result["missing_optional"])
        
        # Calculate confidence and make GO/NO_GO decision
        confidence = self._calculate_confidence(issues, warnings, fixes_applied)
        go_no_go = self._make_go_no_go_decision(issues, warnings, confidence)
        
        return ValidationResult(
            passed=len(issues) == 0,
            confidence=confidence,
            issues=issues,
            warnings=warnings,
            fixes_applied=fixes_applied,
            go_no_go=go_no_go
        )
    
    def _run_lint_checks(self, project_dir: Path) -> Dict[str, Any]:
        """Run ruff linting and formatting checks"""
        
        result = {"errors": [], "fixes": []}
        
        # Find Python files
        python_files = list(project_dir.rglob("*.py"))
        if not python_files:
            return result
        
        try:
            # Run ruff check
            cmd = ["ruff", "check", str(project_dir), "--fix"]
            process = subprocess.run(cmd, capture_output=True, text=True, cwd=project_dir)
            
            if process.returncode != 0:
                # Parse ruff output for errors
                lines = process.stdout.split('\n')
                for line in lines:
                    if line.strip() and not line.startswith('['):
                        result["errors"].append(f"Lint: {line.strip()}")
            else:
                result["fixes"].append("Ruff linting passed")
            
            # Run ruff format
            cmd = ["ruff", "format", str(project_dir), "--check"]
            process = subprocess.run(cmd, capture_output=True, text=True, cwd=project_dir)
            
            if process.returncode != 0:
                result["errors"].append("Code formatting issues detected")
                # Auto-fix formatting
                subprocess.run(["ruff", "format", str(project_dir)], cwd=project_dir)
                result["fixes"].append("Auto-fixed code formatting")
            
        except FileNotFoundError:
            result["errors"].append("Ruff not installed - skipping lint checks")
        except Exception as e:
            result["errors"].append(f"Lint check failed: {str(e)}")
        
        return result
    
    def _run_security_checks(self, project_dir: Path) -> Dict[str, Any]:
        """Run bandit security analysis"""
        
        result = {"critical": [], "medium": []}
        
        try:
            cmd = ["bandit", "-r", str(project_dir), "-f", "json"]
            process = subprocess.run(cmd, capture_output=True, text=True, cwd=project_dir)
            
            if process.stdout:
                import json
                bandit_result = json.loads(process.stdout)
                
                for issue in bandit_result.get("results", []):
                    severity = issue.get("issue_severity", "").lower()
                    confidence = issue.get("issue_confidence", "").lower()
                    
                    issue_text = f"Security: {issue.get('test_name', 'Unknown')} in {issue.get('filename', 'Unknown')}"
                    
                    if severity in ["high", "critical"] and confidence in ["high", "medium"]:
                        result["critical"].append(issue_text)
                    elif severity in ["medium", "low"]:
                        result["medium"].append(issue_text)
                        
        except FileNotFoundError:
            result["medium"].append("Bandit not installed - skipping security checks")
        except Exception as e:
            result["medium"].append(f"Security check failed: {str(e)}")
        
        return result
    
    def _run_test_validation(self, project_dir: Path) -> Dict[str, Any]:
        """Run pytest and validate test results"""
        
        result = {"failed_tests": [], "coverage": 0.0}
        
        # Check if tests exist
        test_files = list(project_dir.rglob("test_*.py")) + list(project_dir.rglob("*_test.py"))
        if not test_files:
            result["failed_tests"].append("No test files found")
            return result
        
        try:
            # Run pytest
            cmd = ["python", "-m", "pytest", str(project_dir), "-v", "--tb=short"]
            process = subprocess.run(cmd, capture_output=True, text=True, cwd=project_dir)
            
            if process.returncode != 0:
                # Parse pytest output for specific failures
                lines = process.stdout.split('\n')
                for line in lines:
                    if "FAILED" in line:
                        result["failed_tests"].append(f"Test failed: {line.strip()}")
            
            # Try to get coverage if available
            try:
                cmd = ["python", "-m", "pytest", str(project_dir), "--cov=.", "--cov-report=term-missing"]
                cov_process = subprocess.run(cmd, capture_output=True, text=True, cwd=project_dir)
                
                # Parse coverage from output
                for line in cov_process.stdout.split('\n'):
                    if "TOTAL" in line and "%" in line:
                        try:
                            coverage_str = line.split()[-1].replace('%', '')
                            result["coverage"] = float(coverage_str) / 100.0
                        except:
                            pass
            except:
                pass  # Coverage optional
                
        except Exception as e:
            result["failed_tests"].append(f"Test execution failed: {str(e)}")
        
        return result
    
    def _validate_dependencies(self, project_dir: Path) -> Dict[str, Any]:
        """Validate dependencies for security and compatibility"""
        
        result = {"critical_vulns": [], "outdated": []}
        
        requirements_file = project_dir / "requirements.txt"
        if not requirements_file.exists():
            result["outdated"].append("No requirements.txt found")
            return result
        
        try:
            # Use safety to check for known vulnerabilities
            cmd = ["safety", "check", "-r", str(requirements_file)]
            process = subprocess.run(cmd, capture_output=True, text=True, cwd=project_dir)
            
            if process.returncode != 0:
                lines = process.stdout.split('\n')
                for line in lines:
                    if "vulnerability" in line.lower():
                        result["critical_vulns"].append(f"Vulnerability: {line.strip()}")
            
        except FileNotFoundError:
            result["outdated"].append("Safety not installed - skipping vulnerability checks")
        except Exception as e:
            result["outdated"].append(f"Dependency check failed: {str(e)}")
        
        return result
    
    def _validate_structure(self, project_dir: Path, spec: Dict[str, Any]) -> Dict[str, Any]:
        """Validate project structure meets expectations"""
        
        result = {"missing_critical": [], "missing_optional": []}
        
        # Critical files that should exist
        critical_files = ["requirements.txt", "README.md"]
        
        # Check for main application file
        app_files = list(project_dir.rglob("app.py")) + list(project_dir.rglob("main.py"))
        if not app_files:
            result["missing_critical"].append("No main application file (app.py or main.py) found")
        
        for file_name in critical_files:
            file_path = project_dir / file_name
            if not file_path.exists():
                result["missing_critical"].append(f"Missing critical file: {file_name}")
        
        # Optional but recommended files
        optional_files = [".gitignore", "Dockerfile", "docker-compose.yml"]
        
        for file_name in optional_files:
            file_path = project_dir / file_name
            if not file_path.exists():
                result["missing_optional"].append(f"Missing recommended file: {file_name}")
        
        return result
    
    def _calculate_confidence(self, issues: List[str], warnings: List[str], 
                            fixes_applied: List[str]) -> float:
        """Calculate confidence score based on validation results"""
        
        confidence = 1.0
        
        # Reduce confidence for issues
        confidence -= len(issues) * 0.2
        confidence -= len(warnings) * 0.05
        
        # Boost confidence for fixes
        confidence += len(fixes_applied) * 0.1
        
        return max(0.0, min(1.0, confidence))
    
    def _make_go_no_go_decision(self, issues: List[str], warnings: List[str], 
                              confidence: float) -> str:
        """Make final GO/NO_GO decision"""
        
        if len(issues) == 0 and confidence > 0.8:
            return "GO"
        elif len(issues) > 0 and any("security" in issue.lower() for issue in issues):
            return "NO_GO"  
        elif len(issues) == 0 and len(warnings) <= 3:
            return "CONDITIONAL_GO"
        else:
            return "NO_GO"
