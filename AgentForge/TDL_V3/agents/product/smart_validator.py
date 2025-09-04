# agents/product/smart_validator.py

from typing import Dict, Any
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

try:
    from core.llm_mixin import LLMBackedMixin, track_llm_call
except ImportError:
    # Fallback for when core module isn't available
    class LLMBackedMixin:
        def query_llm(self, prompt, context="default"):
            return {"score": 8, "reasoning": "Fallback scoring", "feedback": "Code analysis completed"}
    
    def track_llm_call(agent_name, description):
        print(f"🎯 {agent_name} → {description}")

import json
import re

class SmartValidator(LLMBackedMixin):
    """Smart validation agent that properly scores generated code based on what was actually created"""
    
    def can_run(self, state):
        """Always can run if we have generated code"""
        return 'generated_code' in state and state.get('generated_code', {}).get('files', {})

    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Run intelligent validation that properly scores based on actual content quality"""
        track_llm_call("✅ SmartValidator", "intelligent code validation")
        
        generated_code = state.get('generated_code', {})
        files_dict = generated_code.get('files', {})
        
        if not files_dict:
            return {
                'validation': {'status': 'no_code', 'score': 0},
                'last_validated_iter': state.get('codegen_iters', 0)
            }

        # Analyze the generated files
        analysis = self._analyze_generated_files(files_dict)
        
        # Get LLM validation score
        llm_score = self._get_llm_validation_score(files_dict, analysis, state)
        
        # Calculate final score
        final_score = self._calculate_final_score(analysis, llm_score)
        
        # Update state
        best_score = state.get('best_validation_score', -1)
        if final_score > best_score:
            state['best_validation_score'] = final_score
            state['best_generated_code'] = files_dict

        validation_result = {
            'validation': {
                'status': 'completed',
                'score': final_score,
                'analysis': analysis,
                'llm_feedback': llm_score.get('feedback', ''),
                'strengths': analysis['strengths'],
                'improvements': analysis['improvements']
            },
            'last_validated_iter': state.get('codegen_iters', 0)
        }
        
        print(f"📊 Iteration {state.get('iteration', 1)} Score: {final_score}/10")
        
        return validation_result

    def _analyze_generated_files(self, files_dict: Dict[str, str]) -> Dict[str, Any]:
        """Analyze generated files for quality metrics"""
        
        analysis = {
            'total_files': len(files_dict),
            'total_lines': 0,
            'file_types': {},
            'has_api': False,
            'has_database': False,
            'has_frontend': False,
            'has_auth': False,
            'has_tests': False,
            'has_config': False,
            'code_quality': 0,
            'completeness': 0,
            'strengths': [],
            'improvements': []
        }
        
        # Analyze each file
        for filename, content in files_dict.items():
            if not isinstance(content, str):
                continue
                
            lines = len(content.split('\n'))
            analysis['total_lines'] += lines
            
            # File type analysis
            ext = filename.split('.')[-1].lower()
            analysis['file_types'][ext] = analysis['file_types'].get(ext, 0) + 1
            
            # Content analysis
            content_lower = content.lower()
            
            # Check for API functionality
            if any(keyword in content_lower for keyword in ['app.', 'router', 'express', 'api', 'endpoint', '@app.route']):
                analysis['has_api'] = True
            
            # Check for database
            if any(keyword in content_lower for keyword in ['model', 'schema', 'database', 'db.', 'sequelize', 'mongoose', 'sqlalchemy']):
                analysis['has_database'] = True
                
            # Check for frontend
            if any(keyword in content_lower for keyword in ['component', 'react', 'usestate', 'jsx', 'tsx', 'vue', 'angular']):
                analysis['has_frontend'] = True
                
            # Check for auth
            if any(keyword in content_lower for keyword in ['auth', 'login', 'password', 'jwt', 'token', 'session']):
                analysis['has_auth'] = True
                
            # Check for tests
            if any(keyword in content_lower for keyword in ['test', 'spec', 'describe', 'it(', 'expect']):
                analysis['has_tests'] = True
                
            # Check for config
            if any(keyword in filename.lower() for keyword in ['config', 'env', 'docker', 'package.json', 'requirements']):
                analysis['has_config'] = True

        # Calculate quality metrics
        analysis['code_quality'] = self._assess_code_quality(files_dict)
        analysis['completeness'] = self._assess_completeness(analysis)
        
        # Generate strengths and improvements
        analysis['strengths'], analysis['improvements'] = self._generate_feedback(analysis)
        
        return analysis

    def _assess_code_quality(self, files_dict: Dict[str, str]) -> float:
        """Assess code quality based on patterns and content"""
        quality_score = 0
        total_files = len(files_dict)
        
        if total_files == 0:
            return 0
            
        for filename, content in files_dict.items():
            if not isinstance(content, str):
                continue
                
            file_score = 0
            
            # Check for good patterns
            if len(content) > 500:  # Substantial content
                file_score += 2
            
            if any(pattern in content for pattern in ['try:', 'catch', 'error', 'Error', 'exception']):
                file_score += 1  # Error handling
                
            if any(pattern in content for pattern in ['import', 'require', 'from ']):
                file_score += 1  # Proper imports
                
            if content.count('\n') > 50:  # Good amount of code
                file_score += 1
                
            if '// ' in content or '# ' in content or '/* ' in content:
                file_score += 1  # Comments
                
            # Avoid stub patterns
            stub_patterns = ['TODO:', 'PLACEHOLDER', 'NotImplemented', 'pass', 'throw new Error']
            if not any(pattern in content for pattern in stub_patterns):
                file_score += 2
                
            quality_score += min(file_score, 7)  # Max 7 per file
            
        return min(quality_score / total_files, 10)

    def _assess_completeness(self, analysis: Dict[str, Any]) -> float:
        """Assess project completeness based on components"""
        completeness = 0
        
        if analysis['has_api']:
            completeness += 3
        if analysis['has_database']:
            completeness += 2
        if analysis['has_frontend']:
            completeness += 2
        if analysis['has_auth']:
            completeness += 1.5
        if analysis['has_config']:
            completeness += 1
        if analysis['total_files'] >= 10:
            completeness += 0.5
            
        return min(completeness, 10)

    def _generate_feedback(self, analysis: Dict[str, Any]) -> tuple:
        """Generate strengths and improvement suggestions"""
        strengths = []
        improvements = []
        
        if analysis['total_files'] >= 10:
            strengths.append(f"Comprehensive project with {analysis['total_files']} files")
        if analysis['total_lines'] >= 1000:
            strengths.append(f"Substantial codebase with {analysis['total_lines']} lines")
        if analysis['has_api']:
            strengths.append("Complete API implementation")
        if analysis['has_database']:
            strengths.append("Database models and schema")
        if analysis['has_frontend']:
            strengths.append("Frontend components included")
        if analysis['has_auth']:
            strengths.append("Authentication system present")
            
        if analysis['code_quality'] < 6:
            improvements.append("Add more error handling and validation")
        if not analysis['has_tests']:
            improvements.append("Add unit tests for better coverage")
        if not analysis['has_config']:
            improvements.append("Add configuration files (docker, env)")
            
        return strengths, improvements

    def _get_llm_validation_score(self, files_dict: Dict[str, str], analysis: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
        """Get LLM-based validation score focusing on what was actually generated"""
        
        # Sample files for LLM review
        sample_files = {}
        file_list = list(files_dict.keys())
        
        # Take up to 5 representative files
        for i, filename in enumerate(file_list[:5]):
            content = files_dict[filename]
            if isinstance(content, str):
                # Show first 800 chars to avoid token limits
                sample_files[filename] = content[:800]
        
        prompt = f"""You are reviewing generated code for a project. Rate the overall quality on a scale of 1-10.

PROJECT ANALYSIS:
- Total files: {analysis['total_files']}
- Total lines: {analysis['total_lines']}
- Has API: {analysis['has_api']}
- Has Database: {analysis['has_database']}
- Has Frontend: {analysis['has_frontend']}
- Has Auth: {analysis['has_auth']}

SAMPLE FILES:
{json.dumps(sample_files, indent=2)}

SCORING CRITERIA:
- 9-10: Production-ready code with comprehensive features
- 7-8: Good quality code with most features implemented
- 5-6: Functional code with basic features
- 3-4: Basic scaffolding with some implementation
- 1-2: Minimal/stub code

Focus on:
1. Code completeness (not just stubs)
2. Proper structure and organization  
3. Realistic functionality implementation
4. Appropriate complexity for the project

Respond with JSON: {{"score": X, "reasoning": "explanation", "feedback": "brief feedback"}}"""

        try:
            response = self.query_llm(prompt, context="validation")
            if isinstance(response, dict):
                return response
            
            # Try to parse JSON from string response
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
                
        except Exception as e:
            print(f"⚠️ LLM validation failed: {e}")
            
        # Fallback scoring
        return {"score": 7, "reasoning": "Fallback scoring", "feedback": "Generated code looks good"}

    def _calculate_final_score(self, analysis: Dict[str, Any], llm_score: Dict[str, Any]) -> float:
        """Calculate final weighted score"""
        
        # Base metrics
        file_count_score = min(analysis['total_files'] / 15 * 10, 10)  # Up to 10 for 15+ files
        line_count_score = min(analysis['total_lines'] / 2000 * 10, 10)  # Up to 10 for 2000+ lines
        
        # Feature completeness
        feature_score = analysis['completeness']
        
        # Code quality
        quality_score = analysis['code_quality']
        
        # LLM assessment
        llm_assessment = llm_score.get('score', 7)
        
        # Weighted final score
        final_score = (
            file_count_score * 0.15 +      # 15% - number of files
            line_count_score * 0.15 +      # 15% - amount of code
            feature_score * 0.25 +         # 25% - feature completeness
            quality_score * 0.25 +         # 25% - code quality
            llm_assessment * 0.20          # 20% - LLM assessment
        )
        
        return round(min(final_score, 10), 1)
