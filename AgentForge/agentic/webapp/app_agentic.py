"""
Flask Web Application for AgentForge - Clean Agentic Edition
"""

import os
import sys
import json
import threading
import time
import shutil
import zipfile
import random
from pathlib import Path
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for
from flask_socketio import SocketIO, emit, join_room
import uuid

# Add the project root to the path  
ROOT = Path(__file__).resolve().parents[2]  # Go up 2 levels: webapp -> agentic -> AgentForge
sys.path.append(str(ROOT))

# Import our clean agentic system
from agentic.simple_agentic_graph import SimpleAgenticGraph

app = Flask(__name__)
app.config['SECRET_KEY'] = 'agentic-secret-key-2025'
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
        self.start_time = datetime.now()
        self.files_created = 0
        self.total_lines = 0
        self.key_decisions = []
        self.critical_reviews = []
    
    def log_event(self, event_type, message, agent_name=None, extra_data=None):
        """Log an event and broadcast to frontend"""
        event = {
            'type': event_type,
            'message': message,
            'agent_name': agent_name,
            'timestamp': datetime.now().isoformat(),
            'extra_data': extra_data or {}
        }
        
        self.events.append(event)
        
        # Broadcast to frontend
        socketio.emit('agent_activity', event, room=self.session_id)
        
        # Update stats if it's an agent action
        if agent_name and agent_name != 'System':
            if agent_name not in self.agents_stats:
                self.agents_stats[agent_name] = {
                    'decisions': 0,
                    'reviews': 0,
                    'files_generated': 0,
                    'last_activity': None
                }
            
            if event_type == 'decision':
                self.agents_stats[agent_name]['decisions'] += 1
            elif event_type == 'review':
                self.agents_stats[agent_name]['reviews'] += 1
            elif event_type == 'file_generated':
                self.agents_stats[agent_name]['files_generated'] += 1
                self.files_created += 1
            
            self.agents_stats[agent_name]['last_activity'] = datetime.now().isoformat()
            
            # Broadcast updated stats
            socketio.emit('agent_stats_update', {
                'agents': self.agents_stats,
                'total_files': self.files_created,
                'total_events': len(self.events)
            }, room=self.session_id)


class MonitoredAgenticGraph(SimpleAgenticGraph):
    """Agentic Graph with monitoring capabilities for web interface"""
    
    def __init__(self, session_id, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.monitor = AgentMonitor(session_id)
        self.session_id = session_id
    
    def run_agentic_pipeline(self, prompt: str, project_name: str = "agentic_project"):
        """Run pipeline with monitoring"""
        
        self.monitor.log_event('system', f"🚀 Starting agentic pipeline: {prompt[:50]}...", 'System')
        
        try:
            # Memory check
            self.monitor.log_event('system', "🧠 Checking memory for similar projects...", 'MemoryAgent')
            memory_result = self.memory_agent.find_similar_projects(prompt)
            
            if memory_result.get('found'):
                confidence = memory_result.get('confidence', 0)
                self.monitor.log_event('memory_found', 
                                     f"Found similar pattern (confidence: {confidence:.2f})", 
                                     'MemoryAgent')
            
            # Tech decisions
            self.monitor.log_event('system', "🎯 Agents making tech stack decisions...", 'System')
            tech_stack = self._monitored_tech_decisions(prompt, memory_result)
            
            # Architecture decisions
            self.monitor.log_event('system', "🏗️ Agents deciding project architecture...", 'System')
            file_structure = self._monitored_architecture_decisions(prompt, tech_stack, memory_result)
            
            # Code generation
            self.monitor.log_event('system', "⚡ Agents generating code...", 'System')
            generated_files = self._monitored_code_generation({
                'prompt': prompt,
                'tech_stack': tech_stack,
                'file_structure': file_structure
            })
            
            # Peer review
            self.monitor.log_event('system', "📝 Agents reviewing each other's code...", 'System')
            reviews = self._monitored_peer_review(generated_files)
            
            # Self-correction
            self.monitor.log_event('system', "✨ Agents applying self-corrections...", 'System')
            final_files = self._agent_self_correction(generated_files, reviews)
            
            # Save files
            self.monitor.log_event('system', "💾 Saving project files...", 'System')
            saved_files = self._monitored_save_files(final_files, project_name)
            
            # Store in memory
            overall_score = self._calculate_project_score(reviews)
            self.memory_agent.store_project_pattern(
                prompt, tech_stack, list(final_files.keys()), overall_score
            )
            
            self.monitor.log_event('complete', 
                                 f"🎉 Pipeline complete! Score: {overall_score}/10", 
                                 'System', 
                                 {'score': overall_score, 'files_count': len(saved_files)})
            
            return {
                'success': True,
                'project_name': project_name,
                'files_generated': len(saved_files),
                'files_saved': len(saved_files),
                'reviews': len(reviews),
                'overall_score': overall_score,
                'tech_stack': tech_stack,
                'saved_files': saved_files
            }
            
        except Exception as e:
            self.monitor.log_event('error', f"❌ Pipeline failed: {str(e)}", 'System')
            raise
    
    def _monitored_tech_decisions(self, prompt, memory_result):
        """Tech decisions with monitoring"""
        for agent in self.agents:
            # Simulate decision process
            self.monitor.log_event('decision', 
                                 f"Making tech stack decision for: {prompt[:30]}...", 
                                 agent.name)
        
        result = self._agent_tech_decisions(prompt, memory_result)
        
        self.monitor.log_event('decision_complete', 
                             f"Consensus: {result.get('framework', 'Unknown')} + {result.get('database', 'Unknown')}", 
                             'System')
        return result
    
    def _monitored_architecture_decisions(self, prompt, tech_stack, memory_result):
        """Architecture decisions with monitoring"""
        result = self._agent_architecture_decisions(prompt, tech_stack, memory_result)
        
        self.monitor.log_event('architecture', 
                             f"Decided on {len(result)} files: {', '.join(result[:3])}...", 
                             'System')
        return result
    
    def _monitored_code_generation(self, context):
        """Code generation with monitoring"""
        generated_files = {}
        file_structure = context['file_structure']
        
        for i, filename in enumerate(file_structure):
            agent = self.agents[i % len(self.agents)]
            
            self.monitor.log_event('file_generation', 
                                 f"Generating {filename}...", 
                                 agent.name)
            
            try:
                code = self._generate_file_content(agent, filename, context)
                generated_files[filename] = code
                
                lines = len(code.split('\n'))
                self.monitor.log_event('file_generated', 
                                     f"Generated {filename} ({lines} lines)", 
                                     agent.name,
                                     {'filename': filename, 'lines': lines})
                
            except Exception as e:
                self.monitor.log_event('error', 
                                     f"Failed to generate {filename}: {str(e)}", 
                                     agent.name)
                generated_files[filename] = self._simple_fallback(filename, context)
        
        return generated_files
    
    def _monitored_peer_review(self, files):
        """Peer review with monitoring"""
        reviews = []
        file_items = list(files.items())
        
        for filename, code in file_items[:5]:
            reviewers = random.sample(self.agents, min(2, len(self.agents)))
            
            for agent in reviewers:
                review = agent.review_code(filename, code)
                reviews.append(review)
                
                self.monitor.log_event('review', 
                                     f"Reviewed {filename}: score {review.get('score', 0)}/10", 
                                     agent.name,
                                     {'filename': filename, 'score': review.get('score', 0)})
        
        return reviews
    
    def _monitored_save_files(self, files, project_name):
        """Save files with monitoring"""
        saved_files = self._save_project_files(files, project_name)
        
        for filename in files.keys():
            self.monitor.log_event('file_saved', 
                                 f"Saved {filename}", 
                                 'System')
        
        return saved_files


@app.route('/')
def index():
    """Main landing page"""
    return render_template('index.html')

@app.route('/agentic')
def agentic():
    """Agentic generation page"""
    return render_template('index_agentic.html')

@app.route('/generate', methods=['POST'])
def generate_project():
    """Generate project endpoint"""
    
    data = request.json
    prompt = data.get('prompt', '').strip()
    project_name = data.get('project_name', '').strip() or 'agentic_project'
    
    if not prompt:
        return jsonify({'error': 'Prompt is required'}), 400
    
    # Create session
    session_id = str(uuid.uuid4())
    
    # Start generation in background
    thread = threading.Thread(
        target=run_generation_pipeline,
        args=(session_id, prompt, project_name)
    )
    thread.daemon = True
    thread.start()
    
    return jsonify({
        'session_id': session_id,
        'status': 'started',
        'message': 'Generation pipeline started'
    })

@socketio.on('join_session')
def handle_join_session(data):
    """Handle client joining a session"""
    # Handle both string and dictionary formats
    if isinstance(data, str):
        session_id = data
    else:
        session_id = data.get('session_id') if data else None
    
    if session_id:
        join_room(session_id)
        emit('joined', {'session_id': session_id})

def run_generation_pipeline(session_id, prompt, project_name):
    """Run the generation pipeline in background"""
    
    try:
        # Create monitored agentic graph
        agentic_graph = MonitoredAgenticGraph(
            session_id, 
            project_folder="local_output",
            target_score=6.0
        )
        
        # Store session
        active_sessions[session_id] = agentic_graph
        
        # Run pipeline
        result = agentic_graph.run_agentic_pipeline(prompt, project_name)
        
        # Store result
        session_outputs[session_id] = {
            'result': result,
            'project_name': project_name,
            'completed_at': datetime.now().isoformat()
        }
        
        # Notify completion
        socketio.emit('generation_complete', {
            'session_id': session_id,
            'result': result
        }, room=session_id)
        
    except Exception as e:
        # Notify error
        socketio.emit('generation_error', {
            'session_id': session_id,
            'error': str(e)
        }, room=session_id)

@app.route('/download/<session_id>')
def download_project(session_id):
    """Download generated project as ZIP"""
    
    if session_id not in session_outputs:
        return jsonify({'error': 'Session not found or not completed'}), 404
    
    output = session_outputs[session_id]
    project_name = output['project_name']
    
    # Create ZIP
    zip_path = Path("local_output") / f"{project_name}.zip"
    project_path = Path("local_output") / project_name
    
    if not project_path.exists():
        return jsonify({'error': 'Project files not found'}), 404
    
    try:
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file_path in project_path.rglob('*'):
                if file_path.is_file():
                    arcname = file_path.relative_to(project_path)
                    zipf.write(file_path, arcname)
        
        return send_file(
            zip_path,
            as_attachment=True,
            download_name=f"{project_name}.zip",
            mimetype='application/zip'
        )
        
    except Exception as e:
        return jsonify({'error': f'Failed to create ZIP: {str(e)}'}), 500

@app.route('/api/session/<session_id>/status')
def get_session_status(session_id):
    """Get session status"""
    
    status = {
        'session_id': session_id,
        'active': session_id in active_sessions,
        'completed': session_id in session_outputs
    }
    
    if session_id in active_sessions:
        agentic_graph = active_sessions[session_id]
        status['agents_stats'] = agentic_graph.monitor.agents_stats
        status['events_count'] = len(agentic_graph.monitor.events)
    
    if session_id in session_outputs:
        status['result'] = session_outputs[session_id]['result']
    
    return jsonify(status)


if __name__ == '__main__':
    print("🚀 Starting AgentForge - Clean Agentic Edition")
    print("🌐 Web Interface: http://localhost:5001")
    print("📊 Real-time monitoring with SocketIO")
    print("🤖 Multi-agent collaboration system")
    
    # Make sure output directory exists
    Path("local_output").mkdir(exist_ok=True)
    
    socketio.run(app, debug=True, host='0.0.0.0', port=5001)
