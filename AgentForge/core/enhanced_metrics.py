#!/usr/bin/env python3
"""
📊 ENHANCED PROJECT METRICS
Comprehensive project quality assessment with production readiness scoring
"""

from typing import Dict, Any, List
from pathlib import Path
import json
import re

class ProductionQualityMetrics:
    """Comprehensive metrics for production-ready project assessment"""
    
    def __init__(self):
        self.baseline_requirements = {
            "docker-compose.yml": "Container orchestration",
            ".env.example": "Environment configuration",
            "README.md": "Project documentation",
            "Dockerfile": "Container definition"
        }
        
        self.security_files = {
            "backend/middleware/auth.js": "Authentication middleware",
            "backend/middleware/security.js": "Security headers",
            "backend/config/cors.js": "CORS configuration"
        }
        
        self.api_patterns = {
            "health": r"/api/health",
            "docs": r"/(docs|swagger|api-docs)",
            "auth": r"/api/(auth|login|register)",
            "crud": r"/api/\w+/(get|post|put|delete)"
        }
    
    def assess_project_quality(self, generated_code: Dict[str, Any], contract: Dict[str, Any] = None) -> Dict[str, Any]:
        """Comprehensive project quality assessment"""
        files = generated_code.get('files', {}) or {}
        
        # File-based assessments
        baseline_score = self._assess_baseline_requirements(files)
        architecture_score = self._assess_architecture_quality(files)
        security_score = self._assess_security_implementation(files)
        production_score = self._assess_production_readiness(files)
        
        # Contract compliance (if available)
        contract_score = self._assess_contract_compliance(files, contract) if contract else 8.0
        
        # Code quality analysis
        code_quality_score = self._assess_code_quality(files)
        
        # Overall scoring
        overall_score = (
            baseline_score * 0.15 +       # 15% - Must have basics
            architecture_score * 0.20 +   # 20% - Good structure
            security_score * 0.15 +       # 15% - Security basics
            production_score * 0.20 +     # 20% - Production ready
            contract_score * 0.15 +       # 15% - Contract compliance
            code_quality_score * 0.15     # 15% - Code quality
        )
        
        return {
            "overall_score": round(overall_score, 1),
            "baseline_score": round(baseline_score, 1),
            "architecture_score": round(architecture_score, 1),
            "security_score": round(security_score, 1),
            "production_score": round(production_score, 1),
            "contract_score": round(contract_score, 1),
            "code_quality_score": round(code_quality_score, 1),
            "file_count": len(files),
            "production_ready": overall_score >= 8.0,
            "recommendations": self._generate_recommendations(files, overall_score)
        }
    
    def _assess_baseline_requirements(self, files: Dict[str, Any]) -> float:
        """Check if basic project requirements are met"""
        score = 0.0
        total_requirements = len(self.baseline_requirements)
        
        for required_file, purpose in self.baseline_requirements.items():
            if any(required_file in path for path in files.keys()):
                score += 1
            elif required_file == "Dockerfile" and "docker-compose.yml" in str(files.keys()):
                score += 0.5  # Docker compose might contain build instructions
        
        return (score / total_requirements) * 10
    
    def _assess_architecture_quality(self, files: Dict[str, Any]) -> float:
        """Assess project architecture and structure"""
        score = 0.0
        
        # Check for proper separation of concerns
        has_models = any("model" in path.lower() for path in files.keys())
        has_routes = any("route" in path.lower() or "controller" in path.lower() for path in files.keys())
        has_middleware = any("middleware" in path.lower() for path in files.keys())
        has_config = any("config" in path.lower() for path in files.keys())
        has_services = any("service" in path.lower() for path in files.keys())
        has_tests = any("test" in path.lower() for path in files.keys())
        
        # Score based on architecture components
        if has_models: score += 1.5
        if has_routes: score += 1.5
        if has_middleware: score += 1.0
        if has_config: score += 1.0
        if has_services: score += 1.0
        if has_tests: score += 1.0
        
        # Bonus for good structure
        frontend_structure = any("components" in path.lower() for path in files.keys())
        backend_structure = any("backend" in path.lower() for path in files.keys())
        if frontend_structure: score += 1.0
        if backend_structure: score += 1.0
        
        return min(score, 10.0)
    
    def _assess_security_implementation(self, files: Dict[str, Any]) -> float:
        """Assess security implementation"""
        score = 0.0
        
        # Check for security-related files
        has_auth = any("auth" in path.lower() for path in files.keys())
        has_middleware = any("middleware" in path.lower() for path in files.keys())
        has_validation = any("validation" in path.lower() or "validator" in path.lower() for path in files.keys())
        
        if has_auth: score += 3.0
        if has_middleware: score += 2.0
        if has_validation: score += 2.0
        
        # Check code content for security patterns (if available)
        security_keywords = ["jwt", "bcrypt", "helmet", "cors", "rate-limit", "validator"]
        for path, content in files.items():
            if isinstance(content, str):
                content_lower = content.lower()
                for keyword in security_keywords:
                    if keyword in content_lower:
                        score += 0.5
                        break
        
        return min(score, 10.0)
    
    def _assess_production_readiness(self, files: Dict[str, Any]) -> float:
        """Assess production deployment readiness"""
        score = 0.0
        
        # Docker and containerization
        has_docker_compose = any("docker-compose" in path.lower() for path in files.keys())
        has_dockerfile = any("dockerfile" in path.lower() for path in files.keys())
        has_env_config = any(".env" in path.lower() for path in files.keys())
        
        if has_docker_compose: score += 2.0
        if has_dockerfile: score += 1.5
        if has_env_config: score += 1.5
        
        # Monitoring and health checks
        has_health_check = any("health" in path.lower() for path in files.keys())
        has_logging = any("log" in path.lower() for path in files.keys())
        
        if has_health_check: score += 1.5
        if has_logging: score += 1.0
        
        # Build and deployment scripts
        has_scripts = any("script" in path.lower() or "makefile" in path.lower() for path in files.keys())
        has_ci_cd = any(".github" in path.lower() or "gitlab" in path.lower() for path in files.keys())
        
        if has_scripts: score += 1.0
        if has_ci_cd: score += 1.5
        
        return min(score, 10.0)
    
    def _assess_contract_compliance(self, files: Dict[str, Any], contract: Dict[str, Any]) -> float:
        """Assess compliance with defined contract"""
        if not contract:
            return 8.0  # Default score if no contract
        
        required_files = contract.get('files', [])
        required_endpoints = contract.get('endpoints', [])
        
        if not required_files and not required_endpoints:
            return 8.0
        
        file_score = 0.0
        if required_files:
            matched_files = 0
            for required in required_files:
                if any(self._file_matches_pattern(path, required) for path in files.keys()):
                    matched_files += 1
            file_score = (matched_files / len(required_files)) * 10
        
        # Note: Endpoint checking would require code parsing, simplified here
        endpoint_score = 7.0  # Default assumption
        
        return (file_score + endpoint_score) / 2
    
    def _assess_code_quality(self, files: Dict[str, Any]) -> float:
        """Assess code quality based on file content"""
        score = 5.0  # Base score
        
        # Check for comprehensive files (not just stubs)
        substantial_files = 0
        total_content_length = 0
        
        for path, content in files.items():
            if isinstance(content, str) and len(content.strip()) > 100:  # Not just a stub
                substantial_files += 1
                total_content_length += len(content)
                
                # Quality indicators
                if "try" in content and "catch" in content:
                    score += 0.2  # Error handling
                if "console.log" in content or "logger" in content or "logging" in content:
                    score += 0.1  # Logging
                if "const" in content or "class" in content:
                    score += 0.1  # Modern patterns
        
        # Bonus for file depth and completeness
        if substantial_files >= 10:
            score += 1.0
        if total_content_length > 5000:  # Substantial codebase
            score += 1.0
        
        return min(score, 10.0)
    
    def _file_matches_pattern(self, file_path: str, pattern: str) -> bool:
        """Check if file path matches pattern"""
        # Handle wildcards
        if "*" in pattern:
            import fnmatch
            return fnmatch.fnmatch(file_path, pattern)
        return pattern in file_path
    
    def _generate_recommendations(self, files: Dict[str, Any], overall_score: float) -> List[str]:
        """Generate improvement recommendations"""
        recommendations = []
        
        if overall_score < 6.0:
            recommendations.append("Critical: Add basic project structure (models, routes, config)")
            recommendations.append("Critical: Implement proper error handling and logging")
            recommendations.append("Critical: Add authentication and security middleware")
        elif overall_score < 8.0:
            recommendations.append("Important: Add comprehensive testing suite")
            recommendations.append("Important: Implement monitoring and health checks")
            recommendations.append("Important: Add CI/CD configuration")
        else:
            recommendations.append("Enhancement: Consider adding advanced monitoring and analytics")
            recommendations.append("Enhancement: Implement performance optimization")
        
        return recommendations
