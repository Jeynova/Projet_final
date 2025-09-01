#!/usr/bin/env python3
"""
REAL TEST: Call the LLM directly to verify multi-language generation
"""
import sys
import os
from pathlib import Path
import tempfile
import json

# Add paths
sys.path.append('.')
sys.path.append('./orchestrator_v2')

from core.llm_client import LLMClient
from dotenv import load_dotenv

# Load environment
load_dotenv()

def test_llm_multilang_directly():
    """Test LLM directly with our new multi-language prompts"""
    
    print("🧪 TESTING LLM MULTI-LANGUAGE GENERATION")
    print("=" * 60)
    
    client = LLMClient()
    
    # Test cases with different target languages
    test_cases = [
        {
            'file': 'src/App.tsx',
            'target_lang': 'TypeScript React',
            'purpose': 'Main React application component',
            'expected': ['import React', 'const App', 'export default']
        },
        {
            'file': 'src/Controller/UserController.php',
            'target_lang': 'PHP',
            'purpose': 'Symfony user controller',
            'expected': ['<?php', 'namespace', 'class UserController']
        },
        {
            'file': 'src/main/java/Application.java',
            'target_lang': 'Java',
            'purpose': 'Spring Boot application',
            'expected': ['package com', '@SpringBootApplication', 'public class']
        },
        {
            'file': 'main.go',
            'target_lang': 'Go',
            'purpose': 'Go web server',
            'expected': ['package main', 'func main', 'gin.Default']
        },
        {
            'file': 'app/main.py',
            'target_lang': 'Python',
            'purpose': 'FastAPI application',
            'expected': ['from fastapi', 'FastAPI()', '@app.get']
        }
    ]
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n🔍 Test {i}: {test['target_lang']} ({test['file']})")
        print("-" * 40)
        
        # Create the same prompt that our enhanced CodeGenAgent now uses
        prompt = f"""
You are a Code Generation Agent that writes production-quality {test['target_lang']} code.

Project request: "Create a blog platform"
Tech stack detected: ['React', 'TypeScript', 'PHP', 'Symfony', 'PostgreSQL']
Target language: {test['target_lang']} (based on file extension)

Generate complete, working {test['target_lang']} code for:
File: {test['file']}
Purpose: {test['purpose']}

Requirements:
- Write COMPLETE, FUNCTIONAL {test['target_lang']} code - not templates or placeholders
- Follow best practices for the {test['target_lang']} language and chosen frameworks
- Include proper imports and dependencies for {test['target_lang']}
- Make it production-ready

CRITICAL: Return JSON with ONLY this structure:
{{
    "code": "complete file content as a single string"
}}

Generate REAL working {test['target_lang']} code, not placeholder comments.
"""
        
        fallback = {'code': f'// Generated {test["target_lang"]} placeholder for {test["file"]}'}
        
        try:
            print(f"📡 Calling LLM for {test['target_lang']} code generation...")
            
            result = client.extract_json(
                f'You are a senior {test["target_lang"]} developer. Write production-quality {test["target_lang"]} code.',
                prompt
            )
            
            if result and 'code' in result:
                code = result['code']
                print(f"✅ LLM responded with {len(code)} characters")
                
                # Check if it contains expected language markers
                found_markers = []
                for marker in test['expected']:
                    if marker.lower() in code.lower():
                        found_markers.append(marker)
                
                print(f"🔍 Language markers found: {found_markers}")
                
                # Show first few lines
                lines = code.split('\n')[:5]
                print("📄 First 5 lines:")
                for line in lines:
                    print(f"   {line}")
                
                if found_markers:
                    print(f"🎉 SUCCESS: LLM generated proper {test['target_lang']} code!")
                else:
                    print(f"⚠️  WARNING: Code doesn't look like {test['target_lang']}")
                    
            else:
                print("❌ No code in LLM response or LLM returned None")
                print(f"Raw response: {result}")
                print("🔄 Using fallback code instead...")
                # Use the fallback to show what should happen
                print(f"📄 Fallback {test['target_lang']} code would be appropriate here")
                
        except Exception as e:
            print(f"❌ LLM call failed: {e}")
            print("Using fallback...")
    
    print("\n" + "=" * 60)
    print("🎯 CONCLUSION:")
    print("If LLM generated language-appropriate code above,")
    print("then your vision is WORKING and the LLM can code freely!")
    print("If it only generated Python, we need to debug the LLM calls.")

if __name__ == '__main__':
    test_llm_multilang_directly()
