#!/usr/bin/env python3
"""
🎭 DYNAMIC ORGANIC INTELLIGENCE UI
Live agent progress with team debate visualization + downloadable results
"""
import sys
import os
import json
import time
import tempfile
from pathlib import Path
from datetime import datetime
from typing import Dict, Any
from flask import Flask, render_template, request, jsonify, send_file
from flask_socketio import SocketIO, emit
import zipfile

sys.path.append('.')
from phase2_pure_intelligence import PureIntelligenceOrchestrator

app = Flask(__name__)
app.config['SECRET_KEY'] = 'organic-intelligence-ui'
socketio = SocketIO(app, cors_allowed_origins="*")

# Global state for tracking progress
current_session = {
    'active': False,
    'current_agent': None,
    'agent_log': [],
    'stats': {'tech_choices': 0, 'files_generated': 0, 'llm_calls': 0},
    'final_state': {},
    'project_path': None
}

class UIAwareOrchestrator(PureIntelligenceOrchestrator):
    """Orchestrator that emits real-time updates to the UI"""
    
    def __init__(self):
        super().__init__()
        self.session_id = None
    
    def run_pipeline_with_ui(self, prompt: str, session_id: str) -> Dict[str, Any]:
        """Run pipeline with real-time UI updates"""
        self.session_id = session_id
        
        # Initialize session
        current_session['active'] = True
        current_session['agent_log'] = []
        current_session['stats'] = {'tech_choices': 0, 'files_generated': 0, 'llm_calls': 0}
        
        socketio.emit('pipeline_started', {
            'prompt': prompt,
            'total_agents': len(self.agents)
        }, room=session_id)
        
        state = {'prompt': prompt}
        
        # Run agents with UI updates
        for i, agent in enumerate(self.agents, 1):
            agent_name = agent.__class__.__name__
            
            try:
                if agent.can_run(state):
                    # Update current agent
                    current_session['current_agent'] = {
                        'name': agent_name,
                        'step': i,
                        'total': len(self.agents),
                        'status': 'running'
                    }
                    
                    socketio.emit('agent_started', {
                        'agent': agent_name,
                        'step': i,
                        'total': len(self.agents)
                    }, room=session_id)
                    
                    # Run agent with progress tracking
                    result = self._run_agent_with_tracking(agent, state)
                    state.update(result)
                    
                    # Add to log
                    current_session['agent_log'].append({
                        'name': agent_name,
                        'status': 'completed',
                        'result_summary': self._summarize_result(agent_name, result)
                    })
                    
                    socketio.emit('agent_completed', {
                        'agent': agent_name,
                        'result': self._summarize_result(agent_name, result),
                        'log': current_session['agent_log']
                    }, room=session_id)
                    
                else:
                    # Agent skipped
                    current_session['agent_log'].append({
                        'name': agent_name,
                        'status': 'skipped',
                        'result_summary': 'Conditions not met'
                    })
                    
                    socketio.emit('agent_skipped', {
                        'agent': agent_name,
                        'reason': 'Conditions not met'
                    }, room=session_id)
                
            except Exception as e:
                # Agent failed
                current_session['agent_log'].append({
                    'name': agent_name,
                    'status': 'failed',
                    'result_summary': f'Error: {str(e)}'
                })
                
                socketio.emit('agent_failed', {
                    'agent': agent_name,
                    'error': str(e)
                }, room=session_id)
        
        # Save generated project
        if 'generated_code' in state:
            project_path = self._save_project_to_disk(state, prompt)
            current_session['project_path'] = project_path
        
        # Final results
        current_session['final_state'] = state
        current_session['active'] = False
        
        socketio.emit('pipeline_completed', {
            'tech_stack': state.get('tech_stack', []),
            'evaluation': state.get('evaluation', {}),
            'stats': current_session['stats'],
            'download_ready': current_session['project_path'] is not None
        }, room=session_id)
        
        return state
    
    def _run_agent_with_tracking(self, agent, state):
        """Run agent with progress tracking"""
        agent_name = agent.__class__.__name__
        
        # Track LLM calls for this agent
        original_llm_json = agent.llm_json if hasattr(agent, 'llm_json') else None
        
        def tracked_llm_json(system_prompt, user_prompt, fallback):
            current_session['stats']['llm_calls'] += 1
            
            socketio.emit('llm_call', {
                'agent': agent_name,
                'operation': 'LLM reasoning...',
                'total_calls': current_session['stats']['llm_calls']
            }, room=self.session_id)
            
            if original_llm_json:
                return original_llm_json(system_prompt, user_prompt, fallback)
            return fallback
        
        # Temporarily replace LLM method
        if hasattr(agent, 'llm_json'):
            agent.llm_json = tracked_llm_json
        
        # Run the agent
        result = agent.run(state)
        
        # Restore original method
        if original_llm_json:
            agent.llm_json = original_llm_json
        
        # Update stats based on result
        if agent_name == 'MultiPerspectiveTechAgent' and 'tech_stack' in result:
            current_session['stats']['tech_choices'] = len(result['tech_stack'])
        
        if agent_name == 'CodeGenAgent' and 'generated_code' in result:
            files = result['generated_code'].get('files', {})
            current_session['stats']['files_generated'] = len(files)
        
        return result
    
    def _summarize_result(self, agent_name: str, result: Dict) -> str:
        """Create summary of agent result for UI"""
        if agent_name == 'LearningMemoryAgent':
            domain = result.get('domain', 'Unknown')
            hints = result.get('experience_hints', [])
            return f"Domain: {domain}, Experience hints: {len(hints)}"
        
        elif agent_name == 'MultiPerspectiveTechAgent':
            tech_stack = result.get('tech_stack', [])
            if tech_stack:
                backend = next((t for t in tech_stack if t.get('role') == 'backend'), {})
                return f"Team chose: {backend.get('name', 'Unknown')} + {len(tech_stack)} technologies"
            return "Team discussion completed"
        
        elif agent_name == 'CodeGenAgent':
            files = result.get('generated_code', {}).get('files', {})
            return f"Generated {len(files)} files"
        
        elif agent_name == 'EvaluationAgent':
            score = result.get('evaluation', {}).get('overall_score', 0)
            return f"Project score: {score}/10"
        
        else:
            return "Completed successfully"
    
    def _save_project_to_disk(self, state: Dict, prompt: str) -> str:
        """Save project and return path"""
        generated_code = state.get('generated_code', {})
        files = generated_code.get('files', {})
        
        if not files:
            return None
        
        # Create timestamped project directory
        timestamp = int(time.time())
        project_name = f"organic-project-{timestamp}"
        output_dir = Path("generated") / project_name
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Save files
        for filename, content in files.items():
            file_path = output_dir / filename
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content, encoding='utf-8')
        
        # Create project summary
        tech_stack = state.get('tech_stack', [])
        summary_content = f"""# Organic Intelligence Project

## Original Request
{prompt}

## Team's Technology Choices
{chr(10).join([f"- **{tech.get('role', 'unknown').title()}**: {tech.get('name', 'Unknown')}" for tech in tech_stack])}

## Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Files
{chr(10).join([f"- {filename}" for filename in files.keys()])}
"""
        
        (output_dir / "PROJECT_SUMMARY.md").write_text(summary_content, encoding='utf-8')
        
        return str(output_dir)

# Global orchestrator instance
orchestrator = UIAwareOrchestrator()

@app.route('/')
def index():
    return render_template('organic_intelligence.html')

@socketio.on('start_pipeline')
def handle_pipeline_start(data):
    """Handle pipeline start request"""
    prompt = data.get('prompt', '')
    session_id = request.sid
    
    if not prompt:
        emit('error', {'message': 'Please provide a project prompt'})
        return
    
    try:
        # Run pipeline in background with UI updates
        result = orchestrator.run_pipeline_with_ui(prompt, session_id)
        
    except Exception as e:
        emit('error', {'message': f'Pipeline failed: {str(e)}'})

@app.route('/download_project')
def download_project():
    """Download generated project as ZIP"""
    project_path = current_session.get('project_path')
    
    if not project_path or not os.path.exists(project_path):
        return jsonify({'error': 'No project available for download'}), 404
    
    # Create ZIP file
    zip_path = f"{project_path}.zip"
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(project_path):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, project_path)
                zipf.write(file_path, arcname)
    
    return send_file(zip_path, as_attachment=True, download_name=f"{Path(project_path).name}.zip")

@app.route('/api/status')
def get_status():
    """Get current pipeline status"""
    return jsonify({
        'active': current_session['active'],
        'current_agent': current_session['current_agent'],
        'stats': current_session['stats'],
        'log': current_session['agent_log']
    })

if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)
