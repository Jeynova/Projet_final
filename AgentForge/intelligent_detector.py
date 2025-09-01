#!/usr/bin/env python3
"""
🧠 INTELLIGENT DOMAIN DETECTION
Smart rule-based domain analysis that actually works
"""
import re
from typing import Dict, List, Tuple

class IntelligentDomainDetector:
    """Smart domain detection using pattern analysis"""
    
    DOMAIN_PATTERNS = {
        'blog': {
            'keywords': ['blog', 'cms', 'content', 'article', 'post', 'publishing', 'editorial', 'news', 'magazine'],
            'features': ['admin dashboard', 'content management', 'seo', 'comments', 'categories', 'tags'],
            'tech_hints': ['content api', 'markdown', 'rich editor']
        },
        'ecommerce': {
            'keywords': ['shop', 'store', 'ecommerce', 'payment', 'cart', 'product', 'order', 'commerce', 'marketplace', 'checkout'],
            'features': ['payment processing', 'inventory', 'shopping cart', 'product catalog', 'order management'],
            'tech_hints': ['payment gateway', 'stripe', 'paypal', 'inventory tracking']
        },
        'social': {
            'keywords': ['chat', 'social', 'message', 'real-time', 'live', 'notification', 'feed', 'follow', 'like', 'comment'],
            'features': ['real-time', 'notifications', 'user profiles', 'messaging', 'activity feed'],
            'tech_hints': ['websocket', 'socket.io', 'real-time updates', 'push notifications']
        },
        'task-mgmt': {
            'keywords': ['task', 'todo', 'project', 'management', 'team', 'collaborate', 'workflow', 'assignment', 'deadline'],
            'features': ['task assignment', 'team collaboration', 'project tracking', 'deadlines', 'progress'],
            'tech_hints': ['project planning', 'gantt', 'kanban', 'collaboration']
        },
        'api': {
            'keywords': ['api', 'rest', 'endpoint', 'microservice', 'service', 'backend', 'data', 'analytics'],
            'features': ['rest api', 'data processing', 'microservices', 'api endpoints', 'data analytics'],
            'tech_hints': ['rest api', 'graphql', 'data processing', 'analytics']
        },
        'enterprise': {
            'keywords': ['enterprise', 'corporate', 'business', 'erp', 'crm', 'document', 'workflow', 'compliance'],
            'features': ['user management', 'role-based access', 'audit', 'reporting', 'compliance'],
            'tech_hints': ['authentication', 'authorization', 'audit trail', 'reporting']
        }
    }
    
    def analyze_project(self, prompt: str) -> Dict[str, any]:
        """Intelligent project analysis"""
        prompt_lower = prompt.lower()
        
        # Score each domain
        domain_scores = {}
        for domain, patterns in self.DOMAIN_PATTERNS.items():
            score = 0
            
            # Keyword matching
            for keyword in patterns['keywords']:
                if keyword in prompt_lower:
                    score += 3
            
            # Feature matching  
            for feature in patterns['features']:
                if feature in prompt_lower:
                    score += 2
            
            # Tech hint matching
            for hint in patterns['tech_hints']:
                if hint in prompt_lower:
                    score += 1
            
            domain_scores[domain] = score
        
        # Find best domain
        best_domain = max(domain_scores.items(), key=lambda x: x[1])
        detected_domain = best_domain[0] if best_domain[1] > 0 else 'general'
        confidence = min(1.0, best_domain[1] / 10.0)
        
        # Complexity analysis
        complexity_indicators = {
            'simple': ['simple', 'basic', 'minimal', 'quick', 'prototype'],
            'moderate': ['dashboard', 'admin', 'management', 'api', 'database'],
            'complex': ['enterprise', 'scalable', 'high-performance', 'real-time', 'analytics', 'ml', 'ai']
        }
        
        complexity = 'moderate'  # default
        for level, indicators in complexity_indicators.items():
            if any(indicator in prompt_lower for indicator in indicators):
                complexity = level
                break
        
        # Performance needs
        performance = 'medium'
        if any(word in prompt_lower for word in ['high-performance', 'fast', 'speed', 'real-time', 'analytics']):
            performance = 'high'
        elif any(word in prompt_lower for word in ['simple', 'basic', 'prototype']):
            performance = 'low'
        
        # Scale expectations
        scale = 'medium'
        if any(word in prompt_lower for word in ['enterprise', 'large-scale', 'scalable']):
            scale = 'large'
        elif any(word in prompt_lower for word in ['simple', 'small', 'prototype']):
            scale = 'small'
        
        # Extract key features
        features = []
        for domain_data in self.DOMAIN_PATTERNS.values():
            for feature in domain_data['features']:
                if feature in prompt_lower:
                    features.append(feature)
        
        return {
            'domain': detected_domain,
            'complexity': complexity,
            'performance_needs': performance,
            'scale_expectations': scale,
            'key_features': features[:5],  # Top 5 features
            'confidence': confidence,
            'domain_scores': domain_scores
        }

def test_intelligent_detection():
    """Test the intelligent domain detector"""
    print("🧠 TESTING INTELLIGENT DOMAIN DETECTION")
    print("="*50)
    
    detector = IntelligentDomainDetector()
    
    test_cases = [
        "Create a modern blog platform with admin dashboard and SEO",
        "Build an ecommerce store with payment processing and inventory",
        "Develop a real-time chat application with notifications",
        "Create a task management system for teams with deadlines",
        "Build a high-performance REST API for data analytics",
        "Design an enterprise document management system"
    ]
    
    for prompt in test_cases:
        print(f"\n🎯 Prompt: {prompt}")
        
        analysis = detector.analyze_project(prompt)
        
        print(f"   🎯 Domain: {analysis['domain']} (confidence: {analysis['confidence']:.1%})")
        print(f"   📊 Complexity: {analysis['complexity']}")
        print(f"   ⚡ Performance: {analysis['performance_needs']}")
        print(f"   📈 Scale: {analysis['scale_expectations']}")
        print(f"   🔥 Features: {analysis['key_features'][:2]}")
        
        # Show domain scores for debugging
        top_domains = sorted(analysis['domain_scores'].items(), key=lambda x: x[1], reverse=True)[:3]
        print(f"   📊 Scores: {dict(top_domains)}")

if __name__ == '__main__':
    test_intelligent_detection()
