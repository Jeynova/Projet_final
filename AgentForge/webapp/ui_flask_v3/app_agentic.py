"""
Flask Frontend for AgentForge - SIMPLE AGENTIC EDITION

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
            'agent': agent_name,
            'timestamp': datetime.now().isoformat(),
            'extra_data': extra_data or {}
        }
        self.events.append(event)
        
        # Broadcast to frontend with session room
        socketio.emit('agent_event', event, room=self.session_id)
        print(f"📡 Broadcasting to session {self.session_id}: {event_type} - {message}")
        
        # Update agent stats
        if agent_name and agent_name not in self.agents_stats:
            self.agents_stats[agent_name] = {
                'decisions': 0,
                'reviews': 0,
                'improvements': 0,
                'files_created': 0,
                'lines_written': 0
            }
    
    def log_decision(self, agent_name, decision):
        """Log agent decision"""
        if agent_name not in self.agents_stats:
            self.agents_stats[agent_name] = {'decisions': 0, 'reviews': 0, 'improvements': 0, 'files_created': 0, 'lines_written': 0}
        
        self.agents_stats[agent_name]['decisions'] += 1
        self.key_decisions.append({'agent': agent_name, 'decision': decision, 'time': datetime.now()})
        self.log_event('decision', f"🤔 {agent_name} chose: {decision}", agent_name)
    
    def log_review(self, agent_name, filename, score):
        """Log agent review"""
        if agent_name not in self.agents_stats:
            self.agents_stats[agent_name] = {'decisions': 0, 'reviews': 0, 'improvements': 0, 'files_created': 0, 'lines_written': 0}
            
        self.agents_stats[agent_name]['reviews'] += 1
        if score <= 3:  # Critical review
            self.critical_reviews.append({'agent': agent_name, 'file': filename, 'score': score, 'time': datetime.now()})
        
        self.log_event('review', f"🔍 {agent_name} reviewed {filename} → {score}/5", agent_name)
    
    def log_improvement(self, agent_name, filename, improvement):
        """Log agent improvement"""
        if agent_name not in self.agents_stats:
            self.agents_stats[agent_name] = {'decisions': 0, 'reviews': 0, 'improvements': 0, 'files_created': 0, 'lines_written': 0}
            
        self.agents_stats[agent_name]['improvements'] += 1
        self.log_event('improvement', f"⚡ {agent_name} improved {filename}: {improvement}", agent_name)
    
    def log_file_creation(self, agent_name, filename, lines_count):
        """Log file creation"""
        if agent_name not in self.agents_stats:
            self.agents_stats[agent_name] = {'decisions': 0, 'reviews': 0, 'improvements': 0, 'files_created': 0, 'lines_written': 0}
            
        self.agents_stats[agent_name]['files_created'] += 1
        self.agents_stats[agent_name]['lines_written'] += lines_count
        self.files_created += 1
        self.total_lines += lines_count
        self.log_event('file_created', f"📄 {agent_name} created {filename} ({lines_count} lines)", agent_name)
        
        # Emit real-time stats update
        socketio.emit('agent_stats_update', {
            'agent_name': agent_name,
            'stats': self.agents_stats[agent_name],
            'total_files': self.files_created,
            'total_lines': self.total_lines
        }, room=self.session_id)
    
    def log_memory_activity(self, activity_type, details):
        """Log MemoryAgent specific activities"""
        if 'MemoryAgent' not in self.agents_stats:
            self.agents_stats['MemoryAgent'] = {
                'patterns_learned': 0,
                'patterns_reused': 0, 
                'similarity_matches': 0,
                'embeddings_created': 0,
                'cache_hits': 0
            }
        
        if activity_type == 'pattern_stored':
            self.agents_stats['MemoryAgent']['patterns_learned'] += 1
            self.log_event('memory', f"🧠 MemoryAgent learned new pattern (score: {details.get('score', 0)})", 'MemoryAgent')
            
        elif activity_type == 'pattern_reused':
            self.agents_stats['MemoryAgent']['patterns_reused'] += 1
            confidence = details.get('confidence', 0)
            self.log_event('memory', f"🧠 MemoryAgent reused pattern (confidence: {confidence:.2f})", 'MemoryAgent')
            
        elif activity_type == 'similarity_found':
            self.agents_stats['MemoryAgent']['similarity_matches'] += 1
            
        elif activity_type == 'embedding_created':
            self.agents_stats['MemoryAgent']['embeddings_created'] += 1
    
    def get_summary_stats(self):
        """Get comprehensive summary statistics"""
        duration = datetime.now() - self.start_time
        
        return {
            'duration_seconds': duration.total_seconds(),
            'duration_formatted': str(duration).split('.')[0],  # Remove microseconds
            'total_events': len(self.events),
            'files_created': self.files_created,
            'total_lines': self.total_lines,
            'agents_stats': self.agents_stats,
            'key_decisions': [
                {
                    'agent': kd['agent'], 
                    'decision': kd['decision'][:50] + ('...' if len(kd['decision']) > 50 else ''),
                    'time': kd['time'].strftime('%H:%M:%S')
                } 
                for kd in self.key_decisions[-5:]  # Last 5 decisions
            ],
            'critical_reviews': [
                {
                    'agent': cr['agent'],
                    'file': cr['file'],
                    'score': cr['score'],
                    'time': cr['time'].strftime('%H:%M:%S')
                }
                for cr in self.critical_reviews[-3:]  # Last 3 critical reviews
            ]
        }


class MonitoredAgenticGraph(SimpleAgenticGraph):
    """Agentic Graph with monitoring for Flask"""
    
    def __init__(self, session_id, save_folder="local_output"):
        self.monitor = AgentMonitor(session_id)
        # Create timestamped folder for this session
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        full_save_path = f"{save_folder}/webapp_{timestamp}_{session_id[:8]}"
        super().__init__(full_save_path)
        
        # Inject monitor into parent for real-time updates
        self.monitor = self.monitor  # Make sure it's accessible
        
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
        score = review.get('score', 0) if isinstance(review, dict) else 3
        self.monitor.log_review(agent.name, filename, score)
        return review
    
    def _monitored_improve(self, agent, filename, code, reviews):
        """Monitored version of improve_code"""
        if reviews:
            self.monitor.log_event('improving', f"{agent.name} is improving {filename}...", agent.name)
            improved = agent.original_improve_code(filename, code, reviews)
            if improved and len(improved) > len(code):
                improvement_desc = f"+{len(improved) - len(code)} chars"
                self.monitor.log_improvement(agent.name, filename, improvement_desc)
            return improved
        return code
    
    def run_agentic_monitored(self, prompt: str, project_name: str = "WebProject"):
        """Run agentic pipeline with monitoring"""
        self.monitor.log_event('start', f"🚀 Starting Agentic Generation: {prompt}")
        
        try:
            # Call parent method
            result = self.run_agentic(prompt, project_name)
            
            if result['success']:
                # Log file creation stats
                for filename, content in result.get('files', {}).items():
                    lines_count = len(content.splitlines()) if content else 0
                    # Determine which agent likely created this file
                    if 'test' in filename.lower():
                        agent = 'QAAgent'
                    elif any(ext in filename for ext in ['.py', '.js', '.ts']):
                        agent = 'DevAgent' 
                    else:
                        agent = 'ArchAgent'
                    
                    self.monitor.log_file_creation(agent, filename, lines_count)
                
                self.monitor.log_event('complete', f"✅ Generation Complete! {result['files_count']} files created")
                
                # Store final stats including summary
                result['agent_stats'] = self.monitor.agents_stats
                result['events'] = self.monitor.events
                result['summary_stats'] = self.monitor.get_summary_stats()
                
                # Broadcast final summary
                socketio.emit('generation_summary', result['summary_stats'], room=self.monitor.session_id)
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
            agentic = MonitoredAgenticGraph(session_id, "local_output")
            result = agentic.run_agentic_monitored(prompt, project_name)
            
            # Store result with local path
            active_sessions[session_id] = result
            session_outputs[session_id] = {
                'path': agentic.save_folder,
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
    project_name = output_info['project_name']
    
    # Build absolute path to project files
    # The path is: ROOT/local_output/webapp_TIMESTAMP_SESSIONID/PROJECT_NAME/
    project_path = Path(ROOT) / output_info['path'] / project_name
    
    print(f"🔍 Looking for project at: {project_path}")
    print(f"📂 Directory exists: {project_path.exists()}")
    if project_path.exists():
        files = list(project_path.rglob('*'))
        print(f"📁 Found {len(files)} files/directories")
    
    if not project_path.exists():
        # Try alternative paths
        alt_paths = [
            Path(ROOT) / output_info['path'],  # Without project name
            Path(ROOT) / "local_output" / project_name,  # Direct in local_output
            Path("local_output") / project_name  # Relative path
        ]
        
        for alt_path in alt_paths:
            print(f"🔍 Trying alternative: {alt_path}")
            if alt_path.exists():
                project_path = alt_path
                break
        else:
            print(f"❌ Project files not found on disk")
            print(f"   Expected: {Path(ROOT) / output_info['path'] / project_name}")
            print(f"   Output info: {output_info}")
            
            # Fallback: create ZIP from files in memory
            if 'files' in output_info and output_info['files']:
                print(f"💾 Creating ZIP from in-memory files ({len(output_info['files'])} files)")
                
                zip_folder = Path(ROOT) / "local_output" / "downloads"
                zip_folder.mkdir(parents=True, exist_ok=True)
                zip_path = zip_folder / f"{session_id[:8]}_{project_name}.zip"
                
                try:
                    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                        for filename, content in output_info['files'].items():
                            zipf.writestr(filename, content)
                            print(f"   📄 Added from memory: {filename}")
                    
                    print(f"✅ ZIP created from memory: {zip_path}")
                    return send_file(zip_path, as_attachment=True, download_name=f"{project_name}.zip")
                    
                except Exception as e:
                    print(f"❌ Memory ZIP creation failed: {e}")
                    return jsonify({'error': f'ZIP creation failed: {str(e)}'}), 500
            else:
                return jsonify({'error': f'No files found in memory either'}), 404
    
    # Create ZIP file
    zip_folder = Path(ROOT) / "local_output" / "downloads"
    zip_folder.mkdir(parents=True, exist_ok=True)
    zip_path = zip_folder / f"{session_id[:8]}_{project_name}.zip"
    
    print(f"📦 Creating ZIP: {zip_path}")
    
    try:
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            file_count = 0
            for file_path in project_path.rglob('*'):
                if file_path.is_file() and not file_path.name.startswith('.'):
                    arcname = file_path.relative_to(project_path)
                    zipf.write(file_path, arcname)
                    print(f"   📄 Added: {arcname}")
                    file_count += 1
        
        print(f"✅ ZIP created successfully: {zip_path} ({file_count} files)")
        print(f"📥 ZIP size: {zip_path.stat().st_size / 1024:.1f} KB")
        
        return send_file(zip_path, as_attachment=True, download_name=f"{project_name}.zip")
        
    except Exception as e:
        print(f"❌ ZIP creation failed: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'ZIP creation failed: {str(e)}'}), 500


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
    """Handle client joining a session room"""
    from flask_socketio import join_room
    session_id = data['session_id']
    join_room(session_id)
    print(f'✅ Client joined session room: {session_id}')
    emit('session_joined', {'session_id': session_id})


if __name__ == '__main__':
    # Create necessary local directories
    (ROOT / "local_output").mkdir(parents=True, exist_ok=True)
    (ROOT / "local_output" / "downloads").mkdir(parents=True, exist_ok=True)
    
    print("🚀 Starting Simple Agentic Flask App...")
    print("🤖 4 Agents: DevAgent, ArchAgent, QAAgent + MemoryAgent")
    print("🧠 MemoryAgent: RAG with vector embeddings for pattern learning")
    print("📊 Real-time monitoring enabled")
    print("📁 Local output: local_output/ (gitignored)")
    print("🔥 Ready at: http://localhost:5001")
    
    socketio.run(app, host='0.0.0.0', port=5001, debug=True)
