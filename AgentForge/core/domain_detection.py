#!/usr/bin/env python3
"""
🔎 DOMAIN DETECTION
Light context analysis (guidance only, not prescriptive)
"""

from typing import Dict, Any


class IntelligentDomainDetector:
    """Analyzes project prompts to detect domain, complexity, and performance needs"""
    
    DOMAIN_PATTERNS = {
        'blog': ['blog', 'cms', 'content', 'article', 'post'],
        'ecommerce': ['shop', 'store', 'ecommerce', 'payment', 'cart'],
        'social': ['chat', 'social', 'message', 'real-time', 'live'],
        'enterprise': ['enterprise', 'corporate', 'business', 'document'],
        'analytics': ['analytics', 'data', 'dashboard', 'reporting'],
        'api': ['api', 'rest', 'endpoint', 'microservice', 'service'],
        'productivity': ['task', 'tasks', 'project', 'projects', 'kanban', 'scrum', 'team', 'teams', 'collaboration', 'assign', 'deadline']
    }
    
    def analyze_project(self, prompt: str) -> Dict[str, Any]:
        """Analyze project prompt to determine domain, complexity, and performance needs"""
        p = (prompt or "").lower()
        scores = {d: sum(3 for w in ws if w in p) for d, ws in self.DOMAIN_PATTERNS.items()}
        best = max(scores.items(), key=lambda x: x[1]) if scores else ('general', 0)
        domain = best[0] if best[1] > 0 else 'general'
        
        complexity = 'simple' if any(w in p for w in ['simple','basic']) else 'moderate'
        if any(w in p for w in ['enterprise','complex','advanced']): 
            complexity = 'complex'
            
        perf = 'low' if 'simple' in p else 'medium'
        if any(w in p for w in ['high-performance','fast','real-time']): 
            perf = 'high'
            
        return {
            'domain': domain, 
            'complexity': complexity, 
            'performance_needs': perf, 
            'confidence': min(1.0, best[1]/10.0)
        }
