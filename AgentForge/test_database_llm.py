#!/usr/bin/env python3
"""
Demonstrate the FULL LLM Database Design Capabilities
"""
import sys
sys.path.append('.')
import requests
import json
from pathlib import Path
import tempfile

class WorkingDatabaseAgent:
    def __init__(self):
        self.ollama_base = 'http://127.0.0.1:11434'
        self.model = 'qwen2.5-coder:7b'
    
    def llm_database_design(self, prompt, tech_stack, db_type):
        '''Demonstrate the FULL LLM database design capabilities'''
        
        design_prompt = f'''You are an expert database architect. Analyze this project and design a comprehensive database schema.

PROJECT REQUEST: "{prompt}"
TECHNOLOGY STACK: {tech_stack}
DATABASE TYPE: {db_type}

CRITICAL REQUIREMENTS:
1. Analyze what type of system this is (blog, ecommerce, task management, inventory, social media, etc.)
2. Identify the CORE ENTITIES needed for this specific project
3. Design appropriate relationships between entities
4. Include proper constraints, indexes, and foreign keys
5. Think about real-world usage patterns

DO NOT use generic User/Product templates. Design entities that make sense for THIS project.

EXAMPLE ANALYSIS:
- Blog Platform → User, Post, Comment, Category, Tag, PostTag
- E-commerce → User, Product, Category, Order, OrderItem, Cart, CartItem, Payment
- Task Manager → User, Team, Project, Task, TaskStatus, Assignment, Comment
- Inventory System → Supplier, Warehouse, Product, ProductVariant, Stock, StockMovement, PurchaseOrder
- Social Platform → User, Post, Like, Follow, Message, Notification
- Learning Platform → User, Course, Module, Lesson, Enrollment, Progress, Quiz, QuizAttempt

Return JSON with this exact structure:
{{
    "project_type": "type of system identified",
    "core_entities": ["Entity1", "Entity2", "Entity3"],
    "relationships": [
        "Entity1 has many Entity2",
        "Entity2 belongs to Entity1",
        "Entity3 has and belongs to many Entity1"
    ],
    "schema_sql": "Complete CREATE TABLE statements with constraints and indexes",
    "reasoning": "Detailed explanation of why these entities were chosen for this specific project type"
}}

Analyze the project and design an appropriate schema.'''

        try:
            payload = {
                'model': self.model,
                'prompt': design_prompt,
                'format': 'json',
                'stream': False
            }
            
            print(f'🤖 Calling LLM for database design: {prompt[:50]}...')
            response = requests.post(f'{self.ollama_base}/api/generate', json=payload, timeout=120)
            
            if response.status_code == 200:
                data = response.json()
                json_response = data.get('response', '{}')
                
                try:
                    result = json.loads(json_response)
                    print('✅ LLM Database Design Successful!')
                    return result
                except json.JSONDecodeError as e:
                    print(f'❌ JSON Parse Error: {e}')
                    print(f'Raw response: {json_response[:200]}...')
                    return None
            else:
                print(f'❌ HTTP Error: {response.status_code}')
                return None
                
        except Exception as e:
            print(f'❌ LLM Error: {e}')
            return None

def main():
    # Test the full LLM database design capabilities
    agent = WorkingDatabaseAgent()

    test_cases = [
        {
            'name': 'Advanced E-commerce Platform',
            'prompt': 'Create a comprehensive e-commerce platform with product variants, inventory tracking, order management, payment processing, customer reviews, wishlists, and promotional campaigns.',
            'tech': ['FastAPI', 'PostgreSQL', 'Redis'],
            'db': 'postgresql'
        },
        {
            'name': 'Task Management with Teams',
            'prompt': 'Build a collaborative task management system with team workspaces, project hierarchies, task dependencies, time tracking, and reporting dashboards.',
            'tech': ['Django', 'PostgreSQL', 'Celery'],
            'db': 'postgresql'
        },
        {
            'name': 'Learning Management System',
            'prompt': 'Create an online learning platform with courses, lessons, quizzes, student progress tracking, certificates, and instructor management.',
            'tech': ['FastAPI', 'MySQL', 'Redis'],
            'db': 'mysql'
        }
    ]

    print("=" * 60)
    print("🚀 DEMONSTRATING FULL LLM DATABASE DESIGN CAPABILITIES")
    print("=" * 60)

    for i, test_case in enumerate(test_cases, 1):
        print(f'\n=== TEST {i}: {test_case["name"]} ===')
        print(f'Prompt: {test_case["prompt"][:100]}...')
        
        result = agent.llm_database_design(
            test_case['prompt'],
            test_case['tech'],
            test_case['db']
        )
        
        if result:
            print(f'📊 Project Type: {result.get("project_type", "Unknown")}')
            print(f'🏗️  Core Entities: {result.get("core_entities", [])}')
            print(f'🔗 Relationships: {len(result.get("relationships", []))} defined')
            print(f'📝 Schema SQL: {"Yes" if result.get("schema_sql") else "No"}')
            
            reasoning = result.get('reasoning', '')
            if reasoning:
                print(f'🧠 LLM Reasoning: {reasoning[:200]}...')
                
            # Show first few relationships
            relationships = result.get('relationships', [])[:3]
            for rel in relationships:
                print(f'   → {rel}')
                
            # Show a sample of the SQL schema
            schema_sql = result.get('schema_sql', '')
            if schema_sql and len(schema_sql) > 100:
                print(f'📄 Schema Preview: {schema_sql[:300]}...')
        else:
            print('❌ LLM call failed - would use intelligent fallback')
            
        print('=' * 50)

if __name__ == '__main__':
    main()
