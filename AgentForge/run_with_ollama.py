#!/usr/bin/env python3
"""
Simple wrapper to run orchestrator_v2 with Ollama LLM enabled
Usage: python run_with_ollama.py "Your project prompt here"
"""
import os
import sys
import subprocess

def main():
    if len(sys.argv) < 2:
        print("Usage: python run_with_ollama.py \"Your project prompt here\"")
        return
    
    # Set environment variables
    os.environ['AGENTFORGE_LLM'] = 'ollama'
    os.environ['OLLAMA_BASE_URL'] = 'http://127.0.0.1:11434'
    os.environ['OLLAMA_MODEL'] = 'llama3.1:latest'
    
    prompt = " ".join(sys.argv[1:])
    
    print(f"🚀 Running orchestrator_v2 with Ollama LLM")
    print(f"📝 Prompt: {prompt}")
    print(f"🔧 LLM Provider: {os.environ['AGENTFORGE_LLM']}")
    print("=" * 60)
    
    # Run the orchestrator
    cmd = [sys.executable, "-m", "orchestrator_v2.logged_orchestrator", prompt]
    subprocess.run(cmd)

if __name__ == "__main__":
    main()
