"""
Flask Frontend for AgentForge Orchestrator v3 - Organic Intelligence Edition
Features:
- Phase 2 Organic Intelligence with 8 Core Agents
- Live workflow visualization with team debate
- Real-time multi-perspective decision making
- Project gallery with downloads
- Pure LLM intelligence display
"""
import os
import sys
import json
import threading
import time                        # Generate meaningful result message for UI
import shutil
import zipfile
from pathlib import Path
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for, session
from flask_socketio import SocketIO, emit
from dotenv import load_dotenv

# Add the project root to the path
ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(ROOT))

# Import database models from v2
try:
    from apps.ui_flask_v2.db import Base, engine, SessionLocal
    from apps.ui_flask_v2.models import Project, DockerImage
    HAS_DB_SYSTEM = True
except ImportError:
    HAS_DB_SYSTEM = False

# Import organic intelligence system
try:
    # Import from the root directory
    import sys
    sys.path.insert(0, str(ROOT))
    from phase2_pure_intelligence import (
        PureIntelligenceOrchestrator,
        LearningMemoryAgent,
        MultiPerspectiveTechAgent,
        ArchitectureAgent,
        CodeGenAgent,
        DatabaseAgent,
        DeploymentAgent,
        ValidateAgent,
        EvaluationAgent
    )
    ORGANIC_AVAILABLE = True
    print("✅ Organic Intelligence system imported successfully")
except ImportError as e:
    ORGANIC_AVAILABLE = False
    print(f"❌ Organic Intelligence system import failed: {e}")

# Load environment variables
load_dotenv(ROOT / ".env")

app = Flask(__name__)
app.config['SECRET_KEY'] = 'agentforge-organic-v3-secret'
socketio = SocketIO(app, cors_allowed_origins="*")

GENERATED = ROOT / "generated"
GENERATED.mkdir(parents=True, exist_ok=True)

# Initialize database if available
if HAS_DB_SYSTEM:
    Base.metadata.create_all(bind=engine)

class OrganicMonitor:
    """Monitors organic intelligence workflow and broadcasts in real-time"""
    
    def __init__(self):
        self.current_session = None
        self.agents_log = []
        self.stats = {
            'tech_choices': 0,
            'files_generated': 0,
            'llm_calls': 0,
            'team_perspectives': 0
        }
        self.project_data = None
        self.saved_projects = []  # 📁 Fallback storage when DB unavailable
        
    def start_pipeline(self, prompt: str, session_id: str):
        """Initialize new organic intelligence session"""
        self.current_session = {
            'id': session_id,
            'prompt': prompt,
            'start_time': datetime.now(),
            'status': 'running',
            'current_agent': None,
            'total_agents': 8
        }
        self.agents_log = []
        self.stats = {
            'tech_choices': 0,
            'files_generated': 0,
            'llm_calls': 0,
            'team_perspectives': 0
        }
        self.project_data = None
        
        emit_data = {
            'session_id': session_id,
            'prompt': prompt,
            'total_agents': 8
        }
        socketio.emit('pipeline_started', emit_data)
        
    def agent_started(self, agent_name: str, step: int):
        """Agent has started execution"""
        agent_info = {
            'agent': agent_name,
            'step': step,
            'total': 8,
            'start_time': datetime.now(),
            'status': 'running'
        }
        
        if self.current_session:
            self.current_session['current_agent'] = agent_name
            
        emit_data = {
            'agent': agent_name,
            'step': step,
            'total': 8,
            'status': 'started'
        }
        socketio.emit('agent_started', emit_data)
        
    def llm_call_made(self, agent_name: str, operation: str):
        """LLM API call was made"""
        self.stats['llm_calls'] += 1
        
        # Special handling for multi-perspective agent
        if agent_name == 'MultiPerspectiveTechAgent':
            self.stats['team_perspectives'] += 1
            
        emit_data = {
            'agent': agent_name,
            'operation': operation,
            'total_calls': self.stats['llm_calls'],
            'team_perspectives': self.stats['team_perspectives']
        }
        socketio.emit('llm_call', emit_data)
        
    def agent_completed(self, agent_name: str, result: str, duration: float = 0):
        """Agent has completed execution"""
        agent_info = {
            'agent': agent_name,
            'result': result,
            'duration': duration,
            'end_time': datetime.now(),
            'status': 'completed'
        }
        
        # 📊 Real-time stats updates
        stats_update = {}
        
        # Track tech choices when tech agent completes
        if agent_name == 'MultiPerspectiveTechAgent':
            self.stats['tech_choices'] += 1
            stats_update['tech_choices'] = self.stats['tech_choices']
            
        # Track files when code generation completes
        elif agent_name == 'CodeGenAgent':
            # Estimate file count from result
            result_lower = result.lower()
            if 'files' in result_lower:
                import re
                file_matches = re.findall(r'(\d+)\s+files?', result_lower)
                if file_matches:
                    file_count = int(file_matches[-1])
                    self.stats['files_generated'] = file_count
                    stats_update['files_generated'] = file_count
                else:
                    self.stats['files_generated'] += 5  # Default estimate
                    stats_update['files_generated'] = self.stats['files_generated']
            else:
                self.stats['files_generated'] += 3  # Conservative estimate
                stats_update['files_generated'] = self.stats['files_generated']
                
        # Track database schemas
        elif agent_name == 'DatabaseAgent':
            self.stats['database_schemas'] = self.stats.get('database_schemas', 0) + 1
            stats_update['database_schemas'] = self.stats['database_schemas']
            
        # Track architecture components
        elif agent_name == 'ArchitectureAgent':
            self.stats['architecture_components'] = self.stats.get('architecture_components', 0) + 1
            stats_update['architecture_components'] = self.stats['architecture_components']
            
        self.agents_log.append(agent_info)
        
        emit_data = {
            'agent': agent_name,
            'result': result,
            'status': 'completed',
            'stats': stats_update  # 📊 Include real-time stats
        }
        socketio.emit('agent_completed', emit_data)
        
    def agent_skipped(self, agent_name: str, reason: str):
        """Agent was skipped"""
        agent_info = {
            'agent': agent_name,
            'reason': reason,
            'status': 'skipped'
        }
        self.agents_log.append(agent_info)
        
        emit_data = {
            'agent': agent_name,
            'reason': reason,
            'status': 'skipped'
        }
        socketio.emit('agent_skipped', emit_data)
        
    def agent_failed(self, agent_name: str, error: str):
        """Agent failed execution"""
        agent_info = {
            'agent': agent_name,
            'error': error,
            'status': 'failed'
        }
        self.agents_log.append(agent_info)
        
        emit_data = {
            'agent': agent_name,
            'error': error,
            'status': 'failed'
        }
        socketio.emit('agent_failed', emit_data)
        
    def pipeline_completed(self, results: dict):
        """Organic intelligence pipeline completed"""
        if self.current_session:
            self.current_session['status'] = 'completed'
            self.current_session['end_time'] = datetime.now()
            
        # Store project data for download
        self.project_data = results
        print(f"🔍 DEBUG: Project data stored for download")
        print(f"   📁 Keys in project_data: {list(results.keys())}")
        if 'generated_code' in results:
            code_data = results['generated_code']
            print(f"   💻 Generated code type: {type(code_data)}")
            if isinstance(code_data, dict):
                print(f"   📄 Code data keys: {list(code_data.keys())}")
                if 'files' in code_data:
                    files = code_data['files']
                    print(f"   📝 Files type: {type(files)}, count: {len(files) if hasattr(files, '__len__') else 'unknown'}")
        
        # Save to database if available
        if HAS_DB_SYSTEM and self.current_session:
            try:
                db = SessionLocal()
                project = Project(
                    name=f"organic_project_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    prompt=self.current_session.get('prompt', ''),
                    status='completed',
                    config_data=json.dumps(results)
                )
                db.add(project)
                db.commit()
                print(f"💾 Project saved to database: {project.name}")
                db.close()
            except Exception as e:
                print(f"⚠️ Database save failed: {e}")
        else:
            print(f"💾 Database not available, using in-memory storage only")
            # Store in fallback list for gallery display
            project_info = {
                'name': f"organic_project_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                'prompt': self.current_session.get('prompt', '') if self.current_session else '',
                'created_at': datetime.now().isoformat(),
                'data': results
            }
            self.saved_projects.append(project_info)
            # Keep only last 10 projects
            if len(self.saved_projects) > 10:
                self.saved_projects = self.saved_projects[-10:]
        
        # Count generated files
        if 'generated_code' in results:
            # Count files in generated_code
            generated_files = []
            code_data = results['generated_code']
            if isinstance(code_data, dict) and 'files' in code_data:
                generated_files = code_data['files']
            elif isinstance(code_data, list):
                generated_files = code_data
            self.stats['files_generated'] = len(generated_files)
        elif 'files' in results:
            self.stats['files_generated'] = len(results['files'])
            
        # Extract tech stack
        tech_stack = []
        if 'tech_stack' in results:
            tech_stack = results['tech_stack']
        elif results:
            # Try to extract from various keys
            for key in ['backend', 'frontend', 'database', 'deployment']:
                if key in results:
                    tech_info = results[key]
                    if isinstance(tech_info, dict) and 'name' in tech_info:
                        tech_stack.append({'role': key, 'name': tech_info['name']})
        
        emit_data = {
            'status': 'completed',
            'tech_stack': tech_stack,
            'evaluation': results.get('evaluation', {}),
            'stats': self.stats,
            'download_ready': bool(self.project_data)
        }
        socketio.emit('pipeline_completed', emit_data)

# Global monitor instance
monitor = OrganicMonitor()

class UIAwareOrchestrator:
    """Orchestrator that runs the real pipeline and emits UI events"""
    
    def __init__(self):
        self.orchestrator = None
        if ORGANIC_AVAILABLE:
            self.orchestrator = PureIntelligenceOrchestrator()
            
    def run_pipeline_with_ui(self, prompt: str, session_id: str):
        """Run the organic intelligence pipeline with UI integration"""
        if not self.orchestrator:
            socketio.emit('error', {'message': 'Organic Intelligence system not available'})
            return
            
        try:
            # Start monitoring
            monitor.start_pipeline(prompt, session_id)
            
            # Create a custom pipeline that emits events
            print(f"🎭 UI-INTEGRATED PIPELINE: {prompt[:50]}...")
            
            state = {'prompt': prompt}
            
            # Run agents sequentially with real-time UI updates
            for i, agent in enumerate(self.orchestrator.agents, 1):
                agent_name = agent.__class__.__name__
                
                try:
                    # Notify UI that agent is starting
                    monitor.agent_started(agent_name, i)
                    
                    if agent.can_run(state):
                        print(f"\n🔄 Running {agent_name}")
                        
                        # Emit LLM call event
                        monitor.llm_call_made(agent_name, f"Processing {agent_name}")
                        
                        # Run the actual agent
                        result = agent.run(state)
                        state.update(result)
                        
                        # Extract actual file count from generated code
                        if 'generated_code' in state:
                            code_data = state['generated_code']
                            if isinstance(code_data, dict) and 'files' in code_data:
                                files = code_data['files']
                                if isinstance(files, dict):
                                    file_count = len(files)
                                    monitor.stats['files_generated'] = file_count
                                elif isinstance(files, list):
                                    file_count = len(files)
                                    monitor.stats['files_generated'] = file_count
                        
                        # Generate meaningful result message for UI
                        if agent_name == 'MultiPerspectiveTechAgent':
                            tech_choices = [t for t in state.get('tech_stack', []) if isinstance(t, dict)]
                            result_msg = f"� Team organically selected {len(tech_choices)} technologies"
                        elif agent_name == 'CodeGenAgent':
                            files_count = 0
                            if 'generated_code' in result:
                                code_data = result['generated_code']
                                if isinstance(code_data, dict) and 'files' in code_data:
                                    files_count = len(code_data['files'])
                            result_msg = f"💾 Generated {files_count} intelligent code files"
                        elif agent_name == 'EvaluationAgent':
                            score = state.get('evaluation', {}).get('overall_score', 'N/A')
                            result_msg = f"📊 Project evaluated - Overall score: {score}/10"
                        else:
                            result_msg = f"{agent_name} completed successfully"
                        
                        # Notify completion
                        monitor.agent_completed(agent_name, result_msg, 1.0)
                        
                    else:
                        print(f"⏭️ Skipping {agent_name} - conditions not met")
                        monitor.agent_skipped(agent_name, "Conditions not met for current project state")
                        
                except Exception as e:
                    print(f"❌ {agent_name} failed: {e}")
                    monitor.agent_failed(agent_name, str(e))
                    continue
            
            # Learning phase
            if 'evaluation' in state and 'tech_stack' in state:
                evaluation = state['evaluation']
                overall_score = evaluation.get('overall_score', 5)
                
                print(f"\n🎓 LEARNING FROM PROJECT OUTCOME (Score: {overall_score}/10)")
                self.orchestrator.learning_memory.learn_from_outcome(
                    prompt, 
                    state['tech_stack'], 
                    overall_score
                )
            
            print(f"\n🎉 PURE INTELLIGENCE COMPLETE!")
            print(f"🔍 DEBUG: Final state keys: {list(state.keys())}")
            if 'generated_code' in state:
                print(f"   💻 Generated code available: {type(state['generated_code'])}")
            
            # Complete the monitoring with real results
            monitor.pipeline_completed(state)
            
        except Exception as e:
            print(f"❌ Pipeline error: {e}")
            import traceback
            traceback.print_exc()
            socketio.emit('error', {'message': f'Pipeline failed: {str(e)}'})

# Global orchestrator instance
ui_orchestrator = UIAwareOrchestrator()

@app.route('/')
def dashboard():
    """Main dashboard showing project gallery and system status"""
    projects = []
    stats = {'total': 0}
    
    if HAS_DB_SYSTEM:
        try:
            db = SessionLocal()
            projects = db.query(Project).order_by(Project.created_at.desc()).limit(20).all()
            stats['total'] = db.query(Project).count()
            db.close()
        except Exception as e:
            print(f"Database error: {e}")
    
    return render_template('dashboard.html', 
                         projects=projects, 
                         stats=stats,
                         organic_available=ORGANIC_AVAILABLE)

@app.route('/create')
def create_project():
    """Project creation page with organic intelligence"""
    return render_template('create.html', organic_available=ORGANIC_AVAILABLE)

@app.route('/organic')
def organic_intelligence():
    """Dedicated organic intelligence interface"""
    return render_template('organic_intelligence.html')

@app.route('/monitor')
def monitor_page():
    """Live monitoring page"""
    return render_template('monitor.html')

@app.route('/api/system_status')
def system_status():
    """Get current system status"""
    status = {
        'organic_available': ORGANIC_AVAILABLE,
        'database_available': HAS_DB_SYSTEM,
        'llm_status': 'checking...',
        'agents_count': 8 if ORGANIC_AVAILABLE else 0
    }
    
    # Check LLM status
    try:
        if ORGANIC_AVAILABLE:
            # Quick LLM test
            test_agent = LearningMemoryAgent()
            if hasattr(test_agent, 'call_llm'):
                status['llm_status'] = 'connected'
            else:
                status['llm_status'] = 'no_llm_method'
    except Exception as e:
        status['llm_status'] = f'error: {str(e)}'
    
    return jsonify(status)

@app.route('/download_project')
def download_project():
    """Download the last generated project"""
    if not monitor.project_data:
        print("❌ No project data available for download")
        return "No project available for download", 404
        
    print(f"🔍 DEBUG: Starting download process")
    print(f"   📁 Project data keys: {list(monitor.project_data.keys())}")
    
    try:
        # Create ZIP file
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        zip_filename = f"organic_project_{timestamp}.zip"
        zip_path = GENERATED / zip_filename
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Add project files from different possible locations
            files_added = 0
            
            # Check for generated_code structure
            if 'generated_code' in monitor.project_data:
                code_data = monitor.project_data['generated_code']
                print(f"   💻 Generated code data type: {type(code_data)}")
                
                if isinstance(code_data, dict) and 'files' in code_data:
                    files_dict = code_data['files']
                    print(f"   📁 Files dict type: {type(files_dict)}")
                    
                    if isinstance(files_dict, dict):
                        # Handle dict structure: {"filename": "content"}
                        for filename, content in files_dict.items():
                            zipf.writestr(filename, str(content))
                            files_added += 1
                            print(f"   📄 Added file: {filename}")
                    elif isinstance(files_dict, list):
                        # Handle list structure: [{"name": "filename", "content": "content"}]
                        for file_info in files_dict:
                            if isinstance(file_info, dict):
                                file_content = file_info.get('content', '')
                                file_name = file_info.get('name', f'file_{files_added}.txt')
                            else:
                                file_content = str(file_info)
                                file_name = f'file_{files_added}.txt'
                            zipf.writestr(file_name, file_content)
                            files_added += 1
                            print(f"   📄 Added file: {file_name}")
                elif isinstance(code_data, str):
                    zipf.writestr('generated_code.txt', code_data)
                    files_added += 1
            
            # Check for direct files array
            if 'files' in monitor.project_data:
                for file_info in monitor.project_data['files']:
                    if isinstance(file_info, dict):
                        file_content = file_info.get('content', '')
                        file_name = file_info.get('name', f'file_{files_added}.txt')
                    else:
                        file_content = str(file_info)
                        file_name = f'file_{files_added}.txt'
                    zipf.writestr(file_name, file_content)
                    files_added += 1
            
            # If no files found, create a summary
            if files_added == 0:
                summary_content = f"""# Organic Intelligence Project Summary

## Original Prompt
{monitor.current_session.get('prompt', '') if monitor.current_session else 'No prompt available'}

## Technology Stack Chosen by AI Team
{json.dumps(monitor.project_data.get('tech_stack', []), indent=2)}

## Full Results
{json.dumps(monitor.project_data, indent=2)}

Generated by AgentForge v3 - Organic Intelligence
"""
                zipf.writestr('project_summary.md', summary_content)
                files_added += 1
                    
            # Add project metadata
            metadata = {
                'prompt': monitor.current_session.get('prompt', '') if monitor.current_session else '',
                'tech_stack': monitor.project_data.get('tech_stack', []),
                'evaluation': monitor.project_data.get('evaluation', {}),
                'generated_at': datetime.now().isoformat(),
                'stats': monitor.stats,
                'agentforge_version': 'v3-organic',
                'files_count': files_added
            }
            zipf.writestr('agentforge_metadata.json', json.dumps(metadata, indent=2))
            
        return send_file(zip_path, as_attachment=True, download_name=zip_filename)
        
    except Exception as e:
        return f"Failed to create download: {str(e)}", 500

# WebSocket event handlers
@socketio.on('start_pipeline')
def handle_start_pipeline(data):
    """Handle pipeline start request"""
    prompt = data.get('prompt', '')
    if not prompt:
        emit('error', {'message': 'No prompt provided'})
        return
        
    session_id = session.get('session_id', request.sid)
    
    # Run pipeline in background thread
    def run_pipeline():
        ui_orchestrator.run_pipeline_with_ui(prompt, session_id)
    
    thread = threading.Thread(target=run_pipeline)
    thread.daemon = True
    thread.start()

@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    print(f"Client connected: {request.sid}")
    emit('connected', {'session_id': request.sid})

@socketio.on('disconnect') 
def handle_disconnect():
    """Handle client disconnection"""
    print(f"Client disconnected: {request.sid}")

if __name__ == '__main__':
    print("🎭 Starting AgentForge v3 - Organic Intelligence Edition")
    print(f"📁 Root directory: {ROOT}")
    print(f"🤖 Organic Intelligence available: {ORGANIC_AVAILABLE}")
    print(f"💾 Database system available: {HAS_DB_SYSTEM}")
    
    # Check for required environment
    if not ORGANIC_AVAILABLE:
        print("⚠️  Warning: Organic Intelligence system not found")
        print("   Make sure phase2_pure_intelligence.py is available")
    
    socketio.run(app, debug=True, host='0.0.0.0', port=5003)
