"""
Enhanced Flask Frontend for AgentForge Orchestrator v2
Features:
- Interactive agent execution visualization
- Real-time progress tracking  
- Game-like UI with agent status
- Project gallery with downloads
- Orchestrator switching (v1 vs v2)
- Charts and analytics
"""
import os
import sys
import json
import asyncio
import subprocess
import threading
import time
import shutil
import zipfile
from pathlib import Path
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for
from flask_socketio import SocketIO, emit
from dotenv import load_dotenv

# Add the project root to the path
ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(ROOT))

# Import existing database models and spec extractor
try:
    from apps.ui_flask.db import Base, engine, SessionLocal
    from apps.ui_flask.models import Project, DockerImage
    from core.spec_extractor import SpecExtractor
    HAS_V1_SYSTEM = True
except ImportError:
    from .db import Base, engine, SessionLocal
    from .models import Project, DockerImage
    HAS_V1_SYSTEM = False

# Import orchestrator systems
try:
    from orchestrator.graph import build_app as build_graph_v1
    V1_AVAILABLE = True
except ImportError:
    V1_AVAILABLE = False

try:
    from orchestrator_v2.monitored_orchestrator import MonitoredOrchestrator
    V2_AVAILABLE = True
except ImportError:
    V2_AVAILABLE = False

# Load environment variables
load_dotenv(ROOT / ".env")

app = Flask(__name__)
app.config['SECRET_KEY'] = 'agentforge-v2-secret'
socketio = SocketIO(app, cors_allowed_origins="*")

# Initialize spec extractor if available
extractor = SpecExtractor() if HAS_V1_SYSTEM else None

GENERATED = ROOT / "generated"
GENERATED.mkdir(parents=True, exist_ok=True)

# Initialize database
Base.metadata.create_all(bind=engine)

class OrchestrationMonitor:
    """Monitors and broadcasts orchestration progress in real-time"""
    
    def __init__(self):
        self.current_session = None
        self.agents_status = {}
        
    def _serialize_datetime(self, obj):
        """Convert datetime objects to ISO format strings"""
        if isinstance(obj, datetime):
            return obj.isoformat()
        return obj
        
    def _prepare_for_emit(self, data):
        """Prepare data for SocketIO emission by converting datetimes"""
        if isinstance(data, dict):
            return {k: self._serialize_datetime(v) for k, v in data.items()}
        return data
        
    def start_session(self, prompt: str, orchestrator_type: str):
        self.current_session = {
            'id': datetime.now().strftime('%Y%m%d_%H%M%S'),
            'prompt': prompt,
            'orchestrator': orchestrator_type,
            'start_time': datetime.now(),
            'agents': [],
            'status': 'running'
        }
        self.agents_status = {}
        socketio.emit('session_start', self._prepare_for_emit(self.current_session))
        
    def agent_start(self, agent_id: str, agent_class: str, score: float, competitors: int):
        agent_info = {
            'id': agent_id,
            'class': agent_class,
            'score': score,
            'competitors': competitors,
            'start_time': datetime.now(),
            'status': 'running'
        }
        self.agents_status[agent_id] = agent_info
        if self.current_session:
            self.current_session['agents'].append(agent_info)
        socketio.emit('agent_start', self._prepare_for_emit(agent_info))
        
    def agent_complete(self, agent_id: str, duration: float, result_summary: str):
        if agent_id in self.agents_status:
            self.agents_status[agent_id].update({
                'status': 'completed',
                'duration': duration,
                'result': result_summary,
                'end_time': datetime.now()
            })
            socketio.emit('agent_complete', self._prepare_for_emit(self.agents_status[agent_id]))
            
    def session_complete(self, results: dict):
        if self.current_session:
            self.current_session.update({
                'status': 'completed',
                'end_time': datetime.now(),
                'results': results
            })
            # Prepare the data manually to handle nested structures
            emit_data = {
                'session_id': self.current_session.get('id'),
                'status': 'completed',
                'end_time': self._serialize_datetime(self.current_session.get('end_time')),
                'results': results  # results should already be serializable
            }
            socketio.emit('session_complete', emit_data)

monitor = OrchestrationMonitor()

# Global file tracking function
def emit_file_created(filename):
    """Emit file creation event for real-time UI updates"""
    try:
        socketio.emit('file_created', {'filename': filename})
        print(f"📄 Emitted file_created: {filename}")
    except Exception as e:
        print(f"❌ Failed to emit file_created for {filename}: {e}")

# Global LLM call tracking function  
def emit_llm_call(agent_class, prompt_type="unknown"):
    """Emit LLM call event for real-time UI updates"""
    try:
        socketio.emit('llm_call', {'agent': agent_class, 'type': prompt_type})
        print(f"🧠 Emitted llm_call: {agent_class} - {prompt_type}")
    except Exception as e:
        print(f"❌ Failed to emit llm_call: {e}")

@app.route('/')
def index():
    """Main dashboard with orchestrator selection and project gallery"""
    db = SessionLocal()
    try:
        projects = db.query(Project).order_by(Project.id.desc()).limit(20).all()
        project_stats = {
            'total': db.query(Project).count(),
            'recent': db.query(Project).filter(Project.id > 0).count()  # placeholder for recent filter
        }
    finally:
        db.close()
    
    return render_template('dashboard.html', 
                         projects=projects, 
                         stats=project_stats)

@app.route('/create')
def create_project():
    """Project creation interface with orchestrator selection"""
    return render_template('create.html')

@app.route('/monitor')
def monitor_page():
    """Real-time orchestration monitoring page"""
    return render_template('monitor.html')

@app.route('/api/orchestrate', methods=['POST'])
def orchestrate():
    """Start orchestration with real-time monitoring"""
    data = request.get_json()
    prompt = data.get('prompt', '').strip()
    name = data.get('name', 'generated-project').strip()
    orchestrator_type = data.get('orchestrator', 'v2')  # v1 or v2
    llm_mode = data.get('llm_mode', 'ollama')
    
    if not prompt:
        return jsonify({'error': 'Prompt is required'}), 400
    
    # Configure LLM mode
    original_llm = os.environ.get("AGENTFORGE_LLM", "mock")
    os.environ["AGENTFORGE_LLM"] = llm_mode
    
    try:
        # Start monitoring session
        monitor.start_session(prompt, orchestrator_type)
        
        def run_orchestration():
            try:
                if orchestrator_type == 'v1' and V1_AVAILABLE and extractor:
                    # Use original orchestrator
                    spec, conf = extractor.extract(prompt)
                    app_graph = build_graph_v1()
                    state = {"prompt": prompt, "name": name, "artifacts_dir": str(GENERATED), "logs": []}
                    final = app_graph.invoke(state)
                    
                elif orchestrator_type == 'v2' and V2_AVAILABLE:
                    # Use enhanced orchestrator v2 with monitoring integration
                    v2_project_dir = GENERATED / name
                    
                    # Import and create orchestrator with monitoring
                    from orchestrator_v2.logged_orchestrator import LoggedDynamicOrchestrator
                    orchestrator = LoggedDynamicOrchestrator(project_root=v2_project_dir)
                    
                    # Set up global tracking functions for agents
                    try:
                        from orchestrator_v2.agents_impl import set_flask_trackers
                        set_flask_trackers(emit_file_created, emit_llm_call)
                        print("📡 Set up Flask tracking functions for agents")
                    except ImportError as e:
                        print(f"⚠️ Could not set up Flask tracking: {e}")
                    
                    # Override logging methods to send UI updates in real-time
                    original_log_start = orchestrator._log_agent_start
                    original_log_success = orchestrator._log_agent_success
                    original_log_error = orchestrator._log_agent_error
                    
                    def enhanced_log_start(agent, candidates_count, score):
                        original_log_start(agent, candidates_count, score)
                        print(f"🔄 UI Update: Agent {agent.__class__.__name__} starting...")
                        monitor.agent_start(agent.id, agent.__class__.__name__, score, candidates_count)
                        socketio.emit('agent_start', {
                            'id': agent.id,
                            'class': agent.__class__.__name__,
                            'score': score,
                            'competitors': candidates_count,
                            'status': 'running'
                        })
                        
                    def enhanced_log_success(agent, result, duration):
                        original_log_success(agent, result, duration)
                        summary = orchestrator._summarize_result(agent.id, result)
                        print(f"✅ UI Update: Agent {agent.__class__.__name__} completed in {duration:.2f}s")
                        monitor.agent_complete(agent.id, duration, summary)
                        
                        # Extract and emit file creation events
                        if isinstance(result, str):
                            import re
                            # Look for file creation patterns in the result
                            file_patterns = [
                                r'Created: ([^\n\r]+)',
                                r'✅ Created: ([^\n\r\(]+)',
                                r'Generated: ([^\n\r]+)',
                                r'wrote ([^\n\r\s]+)',
                                r'File created: ([^\n\r]+)'
                            ]
                            
                            for pattern in file_patterns:
                                matches = re.findall(pattern, result)
                                for match in matches:
                                    filename = match.strip()
                                    if filename and not filename.startswith('('):
                                        emit_file_created(filename)
                        
                        # Emit LLM call tracking for LLM-backed agents
                        if hasattr(agent, 'call_llm') or 'CodeGen' in agent.__class__.__name__ or 'Evaluation' in agent.__class__.__name__:
                            emit_llm_call(agent.__class__.__name__)
                        
                        socketio.emit('agent_complete', {
                            'id': agent.id,
                            'duration': duration,
                            'result': summary,
                            'status': 'completed'
                        })
                        
                    def enhanced_log_error(agent, error, duration):
                        original_log_error(agent, error, duration)
                        error_msg = f"Error: {str(error)}"
                        print(f"❌ UI Update: Agent {agent.__class__.__name__} failed in {duration:.2f}s")
                        monitor.agent_complete(agent.id, duration, error_msg)
                        socketio.emit('agent_complete', {
                            'id': agent.id,
                            'duration': duration,
                            'result': error_msg,
                            'status': 'error'
                        })
                        
                    orchestrator._log_agent_start = enhanced_log_start
                    orchestrator._log_agent_success = enhanced_log_success  
                    orchestrator._log_agent_error = enhanced_log_error
                    
                    # Run orchestration 
                    final = orchestrator.generate(prompt, auto_proceed=True)
                    
                else:
                    raise Exception(f"Orchestrator {orchestrator_type} not available")
                
                # Save project to database
                if orchestrator_type == 'v1':
                    # V1 returns result with project_dir
                    project_dir = Path(final["project_dir"])
                elif orchestrator_type == 'v2':
                    # V2 returns state dict, project_dir is the one we created
                    project_dir = v2_project_dir
                    # Add project_dir to final for consistency
                    final["project_dir"] = str(project_dir)
                
                zip_path = zip_project(project_dir)
                
                db = SessionLocal()
                try:
                    project = Project(
                        name=name,
                        prompt=prompt,
                        status=final.get("status", "completed"),
                        project_path=str(project_dir),
                        zip_path=str(zip_path),
                        logs_path=str(GENERATED / f"{name}_logs.json")
                    )
                    db.add(project)
                    db.commit()
                    project_id = project.id
                finally:
                    db.close()
                
                # Complete monitoring session
                quality_score = 0
                if orchestrator_type == 'v2':
                    # For V2, look for evaluation results in state
                    evaluation_result = final.get('evaluate', {})
                    quality_score = evaluation_result.get('score', 0)
                else:
                    # For V1, check different possible locations
                    quality_score = final.get('quality_score', final.get('score', 0))
                
                # Create safe results dict without datetime objects
                def make_json_safe(obj):
                    """Recursively convert datetime objects to strings"""
                    if isinstance(obj, datetime):
                        return obj.isoformat()
                    elif isinstance(obj, dict):
                        return {k: make_json_safe(v) for k, v in obj.items()}
                    elif isinstance(obj, list):
                        return [make_json_safe(item) for item in obj]
                    else:
                        return obj
                
                safe_logs = make_json_safe(final.get("logs", []))
                
                results = {
                    'project_id': project_id,
                    'project_name': name,
                    'project_dir': str(project_dir),
                    'zip_path': str(zip_path),
                    'status': final.get("status", "completed"),
                    'logs': safe_logs,
                    'quality_score': quality_score,
                    'files_generated': len(list(project_dir.rglob('*'))) if project_dir.exists() else 0
                }
                print(f"📋 Session completion data: project_name={name}, quality_score={quality_score}, zip_path exists={Path(str(zip_path)).exists()}")
                monitor.session_complete(results)
                
            except Exception as e:
                error_msg = str(e)
                print(f"❌ Orchestration error: {error_msg}")
                socketio.emit('orchestration_error', {'error': error_msg})
            finally:
                # Restore original LLM setting
                os.environ["AGENTFORGE_LLM"] = original_llm
        
        # Run orchestration in background thread
        threading.Thread(target=run_orchestration, daemon=True).start()
        
        return jsonify({'message': 'Orchestration started', 'session_id': monitor.current_session['id']})
        
    except Exception as e:
        os.environ["AGENTFORGE_LLM"] = original_llm
        return jsonify({'error': str(e)}), 500

@app.route('/api/system-status')
def system_status():
    """Get system capabilities and status"""
    return jsonify({
        'orchestrators': {
            'v1': {
                'available': V1_AVAILABLE,
                'name': 'Orchestrator Original',
                'description': 'Graph-based pipeline with spec extraction'
            },
            'v2': {
                'available': V2_AVAILABLE,
                'name': 'Orchestrator Enhanced',
                'description': '21 AI agents with conditional execution'
            }
        },
        'llm_providers': {
            'mock': True,
            'ollama': True,  # We'll check this dynamically in llm-status
            'openai': bool(os.environ.get('OPENAI_API_KEY'))
        }
    })

@app.route('/api/llm-status')
def llm_status():
    """Check status of different LLM providers"""
    status = {}
    
    # Test Mock
    status["mock"] = {
        "available": True,
        "name": "Fallback Déterministe",
        "description": "Ultra-rapide, fiable, sans coût",
        "speed": "0.03s"
    }
    
    # Test Ollama
    try:
        import requests
        resp = requests.get("http://localhost:11434/api/tags", timeout=2)
        if resp.status_code == 200:
            models = resp.json().get("models", [])
            status["ollama"] = {
                "available": True,
                "name": "Ollama Local",
                "description": f"Modèles disponibles: {len(models)}",
                "models": [m.get("name", "unknown") for m in models[:3]]
            }
        else:
            status["ollama"] = {"available": False, "error": "Service unavailable"}
    except:
        status["ollama"] = {"available": False, "error": "Not running"}
    
    # Test OpenAI
    try:
        api_key = os.environ.get("OPENAI_API_KEY")
        if api_key and api_key.startswith("sk-"):
            status["openai"] = {
                "available": True,
                "name": "OpenAI",
                "description": "Très intelligent, coût par usage",
                "model": os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
            }
        else:
            status["openai"] = {"available": False, "error": "No API key"}
    except:
        status["openai"] = {"available": False, "error": "Configuration error"}
    
    current_mode = os.environ.get("AGENTFORGE_LLM", "mock")
    
    return jsonify({
        "current_mode": current_mode,
        "providers": status
    })

@app.route('/preview', methods=['POST'])
def preview():
    """Preview project specifications (v1 compatibility)"""
    if not extractor:
        return jsonify({'error': 'Spec extractor not available'}), 400
        
    prompt = request.form.get("prompt", "").strip()
    name = request.form.get("name", "").strip() or "generated-project"
    
    if not prompt:
        return redirect(url_for('index'))
    
    spec, conf = extractor.extract(prompt)
    spec_dict = spec.model_dump() if hasattr(spec, 'model_dump') else spec.dict()
    return render_template("preview.html", spec=spec_dict, conf=conf, prompt=prompt, name=name)

@app.route('/download/<path:filename>')
def download_zip(filename):
    """Download generated project zip file"""
    file_path = GENERATED / filename
    if not file_path.exists():
        return "File not found", 404
    return send_file(file_path, as_attachment=True)

@app.route('/api/docker/build/<int:project_id>', methods=['POST'])
def build_docker(project_id):
    """Build Docker image for a project"""
    db = SessionLocal()
    try:
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            return jsonify({'error': 'Project not found'}), 404
        
        project_dir = Path(project.project_path)
        if not project_dir.exists():
            return jsonify({'error': 'Project directory not found'}), 404
        
        # Build Docker image
        image_name = f"agentforge/{project.name}:latest"
        try:
            result = subprocess.run(
                ["docker", "build", "-t", image_name, "."],
                cwd=project_dir,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            if result.returncode == 0:
                # Save Docker image info
                docker_image = DockerImage(
                    project_id=project_id,
                    image_name=f"agentforge/{project.name}",
                    image_tag="latest",
                    registry_url=image_name,
                    pushed=False,
                    push_log=result.stdout
                )
                db.add(docker_image)
                db.commit()
                
                return jsonify({
                    'success': True,
                    'message': f'Docker image built successfully: {image_name}',
                    'image_name': image_name
                })
            else:
                return jsonify({
                    'success': False,
                    'error': f'Docker build failed: {result.stderr}'
                }), 500
                
        except subprocess.TimeoutExpired:
            return jsonify({'success': False, 'error': 'Docker build timed out'}), 500
        except FileNotFoundError:
            return jsonify({'success': False, 'error': 'Docker not found. Please install Docker.'}), 500
        
    finally:
        db.close()

@app.route('/api/project/<int:project_id>/logs')
def get_project_logs(project_id):
    """Get logs for a specific project"""
    db = SessionLocal()
    try:
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            return jsonify({'error': 'Project not found'}), 404
        
        if project.logs_path and Path(project.logs_path).exists():
            with open(project.logs_path, 'r', encoding='utf-8') as f:
                logs = json.load(f)
            return jsonify(logs)
        else:
            return jsonify({'message': 'No logs available for this project'})
    
    except Exception as e:
        return jsonify({'error': f'Failed to load logs: {str(e)}'}), 500
    finally:
        db.close()

# SocketIO event handlers
@app.route('/project/<project_name>/download')
def download_project(project_name):
    """Download the project zip file"""
    try:
        zip_path = GENERATED / f"{project_name}.zip"
        if zip_path.exists():
            return send_file(str(zip_path), as_attachment=True, download_name=f"{project_name}.zip")
        else:
            return jsonify({'error': 'Zip file not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@socketio.on('connect')
def handle_connect():
    print('Client connected to monitoring session')
    emit('status', {'message': 'Connected to AgentForge monitoring'})

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected from monitoring session')

def zip_project(project_dir: Path) -> Path:
    """Create a zip archive of the project directory"""
    zip_path = project_dir.parent / f"{project_dir.name}.zip"
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for file_path in project_dir.rglob('*'):
            if file_path.is_file():
                arcname = file_path.relative_to(project_dir)
                zipf.write(file_path, arcname)
    
    return zip_path

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))  # Use port 5001 as expected
    print(f"🚀 Starting AgentForge v2 UI on port {port}")
    print(f"🔧 V1 Available: {V1_AVAILABLE}")
    print(f"🔧 V2 Available: {V2_AVAILABLE}")
    print(f"🔧 Spec Extractor: {HAS_V1_SYSTEM}")
    # Disable debug mode to prevent auto-restart during generation
    socketio.run(app, host='0.0.0.0', port=port, debug=False)
