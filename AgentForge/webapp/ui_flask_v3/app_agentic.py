"""
Flask Frontend for AgentForge - SIMPLE AGENTIC EDITION
Features:
- Simple Agentic Graph with 3 real agents
- Real-time agent decision monitoring
- Agent peer review system
- Live workflow visualization
- ZIP download of generated projects
"""
import os
import sys
import json
import threading
import time
import shutil
import zipfile
from pathlib import Path
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for
from flask_socketio import SocketIO, emit
import uuid

# Add the project root to the path  
ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(ROOT))

# Import our SIMPLE AGENTIC GRAPH
from simple_agentic_graph import SimpleAgenticGraph, SimpleAgent

app = Flask(__name__)
app.config['SECRET_KEY'] = 'simple-agentic-secret-key'
socketio = SocketIO(app, cors_allowed_origins="*")

# Global storage for active sessions
active_sessions = {}
session_outputs = {}


class AgentMonitor:
    """Monitor agent activities and broadcast to frontend"""
    
    def __init__(self, session_id):
        self.session_id = session_id
        self.events = []
        self.agents_stats = {}
    
    def log_event(self, event_type, message, agent_name=None):
        """Log an event and broadcast to frontend"""
        event = {
            'type': event_type,
            'message': message,
            'agent': agent_name,
            'timestamp': datetime.now().isoformat()
        }
        self.events.append(event)
        
        # Broadcast to frontend
        socketio.emit('agent_event', event, room=self.session_id)
        
        # Update agent stats
        if agent_name and agent_name not in self.agents_stats:
            self.agents_stats[agent_name] = {
                'decisions': 0,
                'reviews': 0,
                'improvements': 0
            }
    
    def log_decision(self, agent_name, decision):
        """Log agent decision"""
        self.agents_stats[agent_name]['decisions'] += 1
        self.log_event('decision', f"{agent_name} chose: {decision}", agent_name)
    
    def log_review(self, agent_name, filename, score):
        """Log agent review"""
        self.agents_stats[agent_name]['reviews'] += 1
        self.log_event('review', f"{agent_name} reviewed {filename} -> {score}/5", agent_name)
    
    def log_improvement(self, agent_name, filename, improvement):
        """Log agent improvement"""
        self.agents_stats[agent_name]['improvements'] += 1
        self.log_event('improvement', f"{agent_name} improved {filename}: {improvement}", agent_name)


class MonitoredAgenticGraph(SimpleAgenticGraph):
    """Agentic Graph with monitoring for Flask"""
    
    def __init__(self, session_id, save_folder="webapp_generated"):
        self.monitor = AgentMonitor(session_id)
        super().__init__(save_folder)
        
        # Replace agent methods with monitored versions
        for agent in self.agents:
            agent.original_make_decision = agent.make_decision
            agent.original_review_code = agent.review_code
            agent.original_improve_code = agent.improve_code
            
            agent.make_decision = lambda ctx, opts, a=agent: self._monitored_decision(a, ctx, opts)
            agent.review_code = lambda f, c, a=agent: self._monitored_review(a, f, c)
            agent.improve_code = lambda f, c, r, a=agent: self._monitored_improve(a, f, c, r)
    
    def _monitored_decision(self, agent, context, options):
        """Monitored version of make_decision"""
        self.monitor.log_event('thinking', f"{agent.name} is making a decision...", agent.name)
        decision = agent.original_make_decision(context, options)
        self.monitor.log_decision(agent.name, decision)
        return decision
    
    def _monitored_review(self, agent, filename, code):
        """Monitored version of review_code"""
        self.monitor.log_event('reviewing', f"{agent.name} is reviewing {filename}...", agent.name)
        review = agent.original_review_code(filename, code)
        self.monitor.log_review(agent.name, filename, review.get('score', 0))
        return review
    
    def _monitored_improve(self, agent, filename, code, reviews):
        """Monitored version of improve_code"""
        if reviews:
            self.monitor.log_event('improving', f"{agent.name} is improving {filename}...", agent.name)
            improved = agent.original_improve_code(filename, code, reviews)
            if len(improved) > len(code):
                self.monitor.log_improvement(agent.name, filename, f"+{len(improved) - len(code)} chars")
            return improved
        return code
    
    def run_agentic_monitored(self, prompt: str, project_name: str = "WebProject"):
        """Run agentic pipeline with monitoring"""
        self.monitor.log_event('start', f"🚀 Starting Agentic Generation: {prompt}")
        
        try:
            # Call parent method
            result = self.run_agentic(prompt, project_name)
            
            if result['success']:
                self.monitor.log_event('complete', f"✅ Generation Complete! {result['files_count']} files created")
                
                # Store final stats
                result['agent_stats'] = self.monitor.agents_stats
                result['events'] = self.monitor.events
            else:
                self.monitor.log_event('error', f"❌ Generation Failed: {result.get('error', 'Unknown error')}")
            
            return result
            
        except Exception as e:
            self.monitor.log_event('error', f"❌ Critical Error: {str(e)}")
            return {'success': False, 'error': str(e)}


@app.route('/')
def index():
    """Home page with project creation"""
    return render_template('index.html')


@app.route('/agentic')
def agentic_dashboard():
    """Agentic Generation Dashboard"""
    return render_template('agentic.html')


@app.route('/api/generate', methods=['POST'])
def generate_project():
    """Generate project using Simple Agentic Graph"""
    data = request.json
    prompt = data.get('prompt', '')
    project_name = data.get('project_name', 'WebProject')
    
    if not prompt:
        return jsonify({'error': 'Prompt is required'}), 400
    
    # Create session
    session_id = str(uuid.uuid4())
    
    # Start generation in background thread
    def generate():
        try:
            agentic = MonitoredAgenticGraph(session_id, f"webapp/ui_flask_v3/generated/{session_id}")
            result = agentic.run_agentic_monitored(prompt, project_name)
            
            # Store result
            active_sessions[session_id] = result
            session_outputs[session_id] = {
                'path': f"webapp/ui_flask_v3/generated/{session_id}/{project_name}",
                'files': result.get('files', {}),
                'project_name': project_name
            }
            
            # Notify completion
            socketio.emit('generation_complete', result, room=session_id)
            
        except Exception as e:
            error_result = {'success': False, 'error': str(e)}
            active_sessions[session_id] = error_result
            socketio.emit('generation_error', error_result, room=session_id)
    
    # Start background thread
    thread = threading.Thread(target=generate)
    thread.daemon = True
    thread.start()
    
    return jsonify({'session_id': session_id, 'status': 'started'})


@app.route('/api/download/<session_id>')
def download_project(session_id):
    """Download generated project as ZIP"""
    if session_id not in session_outputs:
        return jsonify({'error': 'Session not found'}), 404
    
    output_info = session_outputs[session_id]
    project_path = Path(ROOT) / output_info['path']
    project_name = output_info['project_name']
    
    if not project_path.exists():
        return jsonify({'error': 'Project files not found'}), 404
    
    # Create ZIP file
    zip_path = Path(ROOT) / f"webapp/ui_flask_v3/downloads/{session_id}_{project_name}.zip"
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for file_path in project_path.rglob('*'):
            if file_path.is_file():
                arcname = file_path.relative_to(project_path)
                zipf.write(file_path, arcname)
    
    return send_file(zip_path, as_attachment=True, download_name=f"{project_name}.zip")


@app.route('/api/status/<session_id>')
def get_session_status(session_id):
    """Get session status"""
    if session_id in active_sessions:
        return jsonify(active_sessions[session_id])
    return jsonify({'status': 'running'})


@socketio.on('connect')
def handle_connect():
    print(f'Client connected')


@socketio.on('disconnect')  
def handle_disconnect():
    print(f'Client disconnected')


@socketio.on('join_session')
def handle_join_session(data):
    session_id = data['session_id']
    # Join the session room for updates
    print(f'Client joined session: {session_id}')


if __name__ == '__main__':
    # Create necessary directories
    (ROOT / "webapp/ui_flask_v3/generated").mkdir(parents=True, exist_ok=True)
    (ROOT / "webapp/ui_flask_v3/downloads").mkdir(parents=True, exist_ok=True)
    
    print("🚀 Starting Simple Agentic Flask App...")
    print("🤖 3 Agents: DevAgent, ArchAgent, QAAgent")
    print("📊 Real-time monitoring enabled")
    print("🔥 Ready at: http://localhost:5001")
    
    socketio.run(app, host='0.0.0.0', port=5001, debug=True)
