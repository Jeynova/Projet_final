#!/usr/bin/env python3
"""
📊 ENHANCED EVALUATION AGENT
Comprehensive project evaluation with production readiness assessment
"""

from typing import Dict, Any

from core.base import LLMBackedMixin, track_llm_call
from core.enhanced_metrics import ProductionQualityMetrics


# ──────────────────────────────────────────────────────────────────────────────
# 📊 ENHANCED EVALUATION AGENT
# ──────────────────────────────────────────────────────────────────────────────
class EvaluationAgent(LLMBackedMixin):
    id = "evaluation"
    
    def __init__(self):
        super().__init__()
        self.metrics = ProductionQualityMetrics()
    
    def can_run(self, state: Dict[str, Any]) -> bool:
        return ('validation' in state) and state.get('goal_reached', False) and ('evaluation' not in state)
    
    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        track_llm_call("📊 EvaluationAgent", "comprehensive project evaluation")
        
        prompt = state.get('prompt', '')
        tech_stack = state.get('tech_stack', [])
        validation = state.get('validation', {})
        architecture = state.get('architecture', {})
        generated_code = state.get('generated_code', {})
        contract = state.get('contract', {})
        
        # Use enhanced metrics for detailed analysis
        quality_metrics = self.metrics.assess_project_quality(generated_code, contract)
        
        # LLM-based holistic evaluation
        sys_p = """You are a SENIOR PROJECT EVALUATOR assessing a complete software project.

Evaluate the project on multiple dimensions:

**TECHNOLOGY FIT**: How well do the chosen technologies match the project requirements?
**ARCHITECTURE QUALITY**: Is the project structure scalable, maintainable, and well-organized?
**CODE QUALITY**: Based on validation scores, is the code production-ready?
**PRODUCTION READINESS**: Can this be deployed immediately to production?
**DEVELOPER EXPERIENCE**: How easy is it for a team to work with this codebase?
**BUSINESS VALUE**: Does this solve the original problem effectively?

Consider the comprehensive metrics provided and give a holistic assessment.

Return STRICT JSON:
{{
  "overall_score": 0-10,
  "technology_fit": 0-10,
  "architecture_quality": 0-10,
  "code_quality": 0-10,
  "production_readiness": 0-10,
  "developer_experience": 0-10,
  "business_value": 0-10,
  "key_strengths": ["specific strengths identified"],
  "critical_issues": ["issues that prevent production deployment"],
  "improvement_areas": ["areas for enhancement"],
  "deployment_readiness": "ready|needs_work|not_ready",
  "recommendation": "deploy|improve|rebuild",
  "feedback": "comprehensive evaluation summary"
}}

Be honest and thorough in your assessment."""
        
        # Comprehensive context for evaluation
        user_p = f"""PROJECT EVALUATION CONTEXT:

**Original Request**: {prompt}

**Technology Stack Decision**:
{chr(10).join([f"- {t.get('role')}: {t.get('name')} (Reasoning: {t.get('reasoning','')})" for t in tech_stack])}

**Validation Results**: {validation.get('status','unknown')} (Score: {validation.get('score',0)}/10)
- Technical Score: {validation.get('technical_score', 0)}/10
- Security Score: {validation.get('security_score', 0)}/10
- Architecture Score: {validation.get('architecture_score', 0)}/10

**Architecture Analysis**:
- Components: {len(architecture.get('key_components',[]))}
- Required Files: {len(architecture.get('required_files', []))}
- Data Flow: {architecture.get('data_flow', 'Not specified')}

**Generated Implementation**:
- Files Created: {quality_metrics['file_count']}
- Overall Quality Score: {quality_metrics['overall_score']}/10
- Production Ready: {quality_metrics['production_ready']}

**Quality Metrics Breakdown**:
- Baseline Requirements: {quality_metrics['baseline_score']}/10
- Architecture Quality: {quality_metrics['architecture_score']}/10
- Security Implementation: {quality_metrics['security_score']}/10
- Production Readiness: {quality_metrics['production_score']}/10
- Contract Compliance: {quality_metrics['contract_score']}/10

**Recommendations from Metrics**: {', '.join(quality_metrics['recommendations'][:3])}"""
        
        fallback = {
            "overall_score": max(quality_metrics['overall_score'], validation.get('score', 7)),
            "technology_fit": 7,
            "architecture_quality": quality_metrics['architecture_score'],
            "code_quality": validation.get('score', 7),
            "production_readiness": quality_metrics['production_score'],
            "developer_experience": 7,
            "business_value": 7,
            "key_strengths": ["Functional implementation", "Basic project structure"],
            "critical_issues": [],
            "improvement_areas": ["Testing coverage", "Documentation"],
            "deployment_readiness": "needs_work" if quality_metrics['overall_score'] < 8 else "ready",
            "recommendation": "improve" if quality_metrics['overall_score'] < 8 else "deploy",
            "feedback": "Solid implementation with room for improvement"
        }
        
        result = self.llm_json(sys_p, user_p, fallback)
        
        # Merge enhanced metrics into result
        result['quality_metrics'] = quality_metrics
        result['files_generated'] = quality_metrics['file_count']
        
        print("\n📊 COMPREHENSIVE PROJECT EVALUATION:")
        print(f"   🎯 Overall: {result.get('overall_score',0)}/10")
        print(f"   🔧 Tech Fit: {result.get('technology_fit',0)}/10")
        print(f"   🏗️ Architecture: {result.get('architecture_quality',0)}/10")
        print(f"   ✨ Code Quality: {result.get('code_quality',0)}/10")
        print(f"   🚀 Production Ready: {result.get('production_readiness',0)}/10")
        print(f"   👥 Dev Experience: {result.get('developer_experience',0)}/10")
        print(f"   💼 Business Value: {result.get('business_value',0)}/10")
        print(f"   📄 Files Generated: {quality_metrics['file_count']}")
        print(f"   🎭 Recommendation: {result.get('recommendation', 'improve').upper()}")
        
        if result.get('deployment_readiness') == 'ready':
            print("   ✅ READY FOR PRODUCTION DEPLOYMENT")
        else:
            print("   ⚠️ NEEDS IMPROVEMENT BEFORE PRODUCTION")
        
        return {'evaluation': result}
