"""
Monitored Orchestrator v2 - Integrates with Flask UI for real-time monitoring
Sends agent execution updates via HTTP to the Flask socketio server
"""
from __future__ import annotations
import os
import json
import time
import requests
from typing import Dict, Any
from pathlib import Path

# Load environment variables
from dotenv import load_dotenv
env_file = Path(__file__).parent.parent / ".env"
if env_file.exists():
    load_dotenv(env_file)

# Set Ollama as default
os.environ['AGENTFORGE_LLM'] = 'ollama'

from .logged_orchestrator import LoggedDynamicOrchestrator

class MonitoredOrchestrator(LoggedDynamicOrchestrator):
    """Enhanced orchestrator that sends real-time updates to Flask UI"""
    
    def __init__(self, project_root: Path, flask_host: str = "localhost", flask_port: int = 5001):
        super().__init__(project_root)
        self.flask_base = f"http://{flask_host}:{flask_port}"
        self.session_id = None
        
    def send_update(self, event_type: str, data: dict):
        """Send update to Flask UI via HTTP"""
        try:
            requests.post(
                f"{self.flask_base}/api/monitor_update",
                json={'event': event_type, 'data': data},
                timeout=1
            )
        except:
            pass  # Fail silently if UI not running
            
    def _log_agent_start(self, agent_id: str, agent_class: str, score: float, competitors: int, state_keys: list):
        """Enhanced logging with UI updates"""
        super()._log_agent_start(agent_id, agent_class, score, competitors, state_keys)
        
        # Send to UI
        self.send_update('agent_start', {
            'id': agent_id,
            'class': agent_class,
            'score': score,
            'competitors': competitors,
            'state_keys': state_keys
        })
        
    def _log_agent_success(self, agent_id: str, duration: float, result: dict):
        """Enhanced logging with UI updates"""
        super()._log_agent_success(agent_id, duration, result)
        
        # Send to UI
        self.send_update('agent_complete', {
            'id': agent_id,
            'duration': duration,
            'result': str(result)[:200],  # Truncate for UI
            'success': True
        })
        
    def generate(self, prompt: str, **kwargs) -> tuple[Path, dict]:
        """Generate project with UI monitoring"""
        
        # Start session
        self.send_update('session_start', {
            'prompt': prompt,
            'start_time': time.time()
        })
        
        try:
            # Run normal generation
            project_dir, results = super().generate(prompt, **kwargs)
            
            # Send completion
            self.send_update('session_complete', {
                'success': True,
                'project_dir': str(project_dir),
                'results': results
            })
            
            return project_dir, results
            
        except Exception as e:
            # Send error
            self.send_update('session_complete', {
                'success': False,
                'error': str(e)
            })
            raise

def main():
    """CLI entry point for monitored orchestrator"""
    if len(sys.argv) < 2:
        print("Usage: python -m orchestrator_v2.monitored_orchestrator \"Your prompt here\"")
        return
        
    prompt = " ".join(sys.argv[1:])
    
    # Setup
    project_root = Path(__file__).parent.parent / "generated"
    project_root.mkdir(parents=True, exist_ok=True)
    
    # Create monitored orchestrator
    orchestrator = MonitoredOrchestrator(project_root)
    
    print(f"🚀 Starting monitored orchestration")
    print(f"📝 Prompt: {prompt}")
    print(f"🔗 UI updates: {orchestrator.flask_base}")
    print("=" * 60)
    
    try:
        project_dir, results = orchestrator.generate(prompt)
        
        print(f"\\n🎉 Project generated successfully!")
        print(f"📂 Location: {project_dir}")
        print(f"📊 Results: {results}")
        
    except Exception as e:
        print(f"❌ Generation failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    import sys
    main()
