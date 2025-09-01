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
import time
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

# Import simple storage system
from simple_storage import SimpleProjectStorage

# Initialize persistent storage
project_storage = SimpleProjectStorage(str(ROOT / "projects_storage.json"))

# Import database models - disabled since v2 was removed
HAS_DB_SYSTEM = False

# Import organic intelligence system
try:
    # Import from the root directory
    import sys
    sys.path.insert(0, str(ROOT))
    from agent_graph import Node, GraphConfig, GraphRunner
    from phase2_pure_intelligence import (
        PureIntelligenceOrchestrator,
        LearningMemoryAgent,
        MultiPerspectiveTechAgent,
        ArchitectureAgent,
        CodeGenAgent,
        DatabaseAgent,
        DeploymentAgent,
        ValidateAgent,
        EvaluationAgent,
        ValidationRouter,
        StackResolverAgent,
        ContractPresenceGuard,
        CapabilityAgent,
        ContractAgent
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

# Database system disabled (v2 was removed)
# if HAS_DB_SYSTEM:
#     Base.metadata.create_all(bind=engine)

class OrganicMonitor:
    """Monitors organic intelligence workflow and broadcasts in real-time"""
    
    def __init__(self):
        self.current_session = None
        self.current_session_id = None  # Store session ID for WebSocket events
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
        self.current_session_id = session_id  # Store for later use
        self.current_session = {
            'id': session_id,
            'prompt': prompt,
            'start_time': datetime.now(),
            'status': 'running',
            'agents': []
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
            'status': 'started'
        }
        try:
            with app.app_context():
                socketio.emit('pipeline_started', emit_data)
        except Exception as e:
            print(f"⚠️ Failed to emit pipeline_started: {e}")
        
    def llm_call_made(self, agent_name: str, operation: str):
        """Track LLM calls"""
        self.stats['llm_calls'] += 1
        
        # Track team perspectives for MultiPerspectiveTechAgent
        if agent_name == 'MultiPerspectiveTechAgent':
            self.stats['team_perspectives'] += 1
        
        emit_data = {
            'agent': agent_name,
            'operation': operation,
            'total_calls': self.stats['llm_calls'],
            'team_perspectives': self.stats['team_perspectives']
        }
        try:
            with app.app_context():
                socketio.emit('llm_call', emit_data)
        except Exception as e:
            print(f"⚠️ Failed to emit llm_call: {e}")
        
    def agent_started(self, agent_name: str, step: int, total: int):
        """Agent has started execution"""
        agent_info = {
            'agent': agent_name,
            'start_time': datetime.now(),
            'step': step,
            'status': 'running'
        }
        self.agents_log.append(agent_info)
        
        emit_data = {
            'agent': agent_name,
            'step': step,
            'total': total,
            'status': 'started'
        }
        try:
            with app.app_context():
                socketio.emit('agent_started', emit_data)
        except Exception as e:
            print(f"⚠️ Failed to emit agent_started: {e}")
        
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
        try:
            with app.app_context():
                socketio.emit('agent_completed', emit_data)
        except Exception as e:
            print(f"⚠️ Failed to emit agent_completed: {e}")
        
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
        try:
            with app.app_context():
                socketio.emit('agent_skipped', emit_data)
        except Exception as e:
            print(f"⚠️ Failed to emit agent_skipped: {e}")
        
    def agent_failed(self, agent_name: str, error: str):
        """Agent execution failed"""
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
        try:
            with app.app_context():
                socketio.emit('agent_failed', emit_data)
        except Exception as e:
            print(f"⚠️ Failed to emit agent_failed: {e}")
        
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
                # Database system disabled
                # db = SessionLocal()
                # project = Project(...)
                print(f"💾 Database disabled")
            except Exception as e:
                print(f"⚠️ Database save failed: {e}")
        else:
            print(f"💾 Database not available, using persistent JSON storage")
            # Store in persistent JSON storage
            if self.current_session:
                try:
                    project_id = project_storage.save_project(
                        self.current_session.get('prompt', ''), 
                        results
                    )
                    print(f"✅ Project saved to JSON storage with ID: {project_id}")
                except Exception as e:
                    print(f"⚠️ JSON storage failed: {e}")
                    
                    # Fallback to in-memory storage
                    project_info = {
                        'id': f"project_{len(self.saved_projects) + 1}",
                        'name': f"organic_project_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                        'prompt': self.current_session.get('prompt', ''),
                        'status': 'completed',
                        'created_at': datetime.now().isoformat(),
                        'tech_stack': results.get('tech_stack', []),
                        'evaluation': results.get('evaluation', {}),
                        'stats': {
                            'files_generated': self.stats.get('files_generated', 0),
                            'llm_calls': self.stats.get('llm_calls', 0),
                            'tech_choices': len(results.get('tech_stack', [])),
                            'quality_score': results.get('validation', {}).get('score', 0)
                        },
                        'data': results
                    }
                    self.saved_projects.append(project_info)
                    # Keep only last 20 projects
                    if len(self.saved_projects) > 20:
                        self.saved_projects = self.saved_projects[-20:]
            else:
                print("⚠️ No current session to store")
        
        # Count generated files
        if 'generated_code' in results:
            # Count files in generated_code
            generated_files = []
            code_data = results['generated_code']
            if isinstance(code_data, dict) and 'files' in code_data:
                if isinstance(code_data['files'], dict):
                    generated_files = list(code_data['files'].keys())
                elif isinstance(code_data['files'], list):
                    generated_files = code_data['files']
            elif isinstance(code_data, list):
                generated_files = code_data
            self.stats['files_generated'] = len(generated_files)
        elif 'files' in results:
            self.stats['files_generated'] = len(results['files'])
            
        # Extract tech stack and count TOTAL technologies
        tech_stack = []
        if 'tech_stack' in results:
            tech_stack = results['tech_stack']
            # 📊 Count TOTAL technologies (front, back, db, deploy, etc.)
            self.stats['tech_choices'] = len([t for t in tech_stack if isinstance(t, dict)])
        elif results:
            # Try to extract from various keys
            for key in ['backend', 'frontend', 'database', 'deployment']:
                if key in results:
                    tech_info = results[key]
                    if isinstance(tech_info, dict) and 'name' in tech_info:
                        tech_stack.append({'role': key, 'name': tech_info['name']})
            self.stats['tech_choices'] = len(tech_stack)
        
        emit_data = {
            'status': 'completed',
            'tech_stack': tech_stack,
            'evaluation': results.get('evaluation', {}),
            'stats': self.stats,
            'download_ready': bool(self.project_data)
        }
        try:
            with app.app_context():
                socketio.emit('pipeline_completed', emit_data)
        except Exception as e:
            print(f"⚠️ Failed to emit pipeline_completed: {e}")

# Global monitor instance
monitor = OrganicMonitor()

from agent_graph import Node, GraphConfig, GraphRunner

class UIAwareOrchestrator:
    def __init__(self):
        if ORGANIC_AVAILABLE:
            from rag_snippets.manager import RAGSnippetManager
            rag_store = RAGSnippetManager()
            self.orchestrator = PureIntelligenceOrchestrator(rag_store)
        else:
            self.orchestrator = None

    def run_pipeline_with_ui(self, prompt: str, session_id: str):
        monitor.start_pipeline(prompt, session_id)
        # Store session_id in monitor for later use
        monitor.current_session_id = session_id

        if not self.orchestrator:
            socketio.emit('error', {'message': 'Orchestrator unavailable'})
            return
        def emit_to_session(event, payload):
            payload = {**payload, 'session_id': session_id}
            socketio.emit(event, payload)
        # --- telemetry hooks:
        def on_start(name, state):
            # reuse your existing monitor hooks
            step = len([a for a in monitor.agents_log if a.get('status')=='completed']) + 1
            monitor.agent_started(name, step, 999)
            monitor.llm_call_made(name, f"Running {name}")

        def on_complete(name, state, result):
            msg = f"{name} completed"

            if name == 'MultiPerspectiveTechAgent':
                msg = f"🎭 Team selected {len(state.get('tech_stack', []))} technologies"

                emit_to_session('tech_stack_decided', {
                    'tech_stack': state.get('tech_stack', [])
                })

                team_decision = state.get('team_decision_process', {})
                if team_decision.get('parallel_debate_results'):
                    emit_to_session('team_debate_started', {})

                    # IMPORTANT: send 'proposal' (not 'response')
                    for role_result in team_decision['parallel_debate_results']:
                        emit_to_session('team_role_response', {
                            'role': role_result.get('role', 'Unknown'),
                            'response': role_result.get('proposal', {})
                        })

                    emit_to_session('team_consensus', {
                        'consensus': team_decision.get('team_discussion', '')
                    })

            elif name == 'CodeGenAgent':
                files = (state.get('generated_code', {}).get('files') or {})
                count = len(files) if isinstance(files, dict) else len(files or [])
                msg = f"💾 Generated {count} files"

            elif name == 'ValidateAgent':
                validation = state.get('validation', {})
                msg = f"✅ Validation complete - Score: {validation.get('score', 'N/A')}/10"

                emit_to_session('validation_completed', {
                    'score': validation.get('score', 0),
                    'status': validation.get('status', 'unknown'),
                    'issues': validation.get('issues', []),
                    'suggestions': validation.get('suggestions', []),
                })

            elif name == 'ValidationRouter':
                if result.get('redo_codegen'):
                    emit_to_session('refinement_triggered', {
                        'iteration': state.get('codegen_iters', 0) + 1
                    })
                elif result.get('goal_reached'):
                    emit_to_session('quality_goal_reached', {
                        'score': state.get('validation', {}).get('score', 0),
                        'threshold': state.get('validation_threshold', 7),  # demo-friendly fallback
                        'iterations': state.get('codegen_iters', 0)
                    })

            elif name == 'EvaluationAgent':
                msg = f"📊 Score: {state.get('evaluation',{}).get('overall_score','N/A')}/10"

            monitor.agent_completed(name, msg, 0.0)

        def on_error(name, e):
            monitor.agent_failed(name, str(e))

        # --- Build nodes that wrap your existing agents (same instances you already constructed inside PureIntelligenceOrchestrator)
        # Use the SAME agent objects to preserve their LLM client + config:
        agents = {a.__class__.__name__: a for a in self.orchestrator.agents}

        # add the router as a pseudo-agent
        router = ValidationRouter()
        agents['ValidationRouter'] = router

        # Defaults & thresholds in state (optimized for demos)
        state = {
            'prompt': prompt,
            'max_codegen_iters': 4,         # number of refinement loops allowed (demo-friendly)
            'validation_threshold': 7,      # required quality (demo-friendly)
            'file_contract_mode': 'strict',  # <- baseline must be met
            'events': []                     # <- enable event-aware can_run
        }

        nodes = {
            # Learning runs again post-validation (so it can coach)
            'LearningMemoryAgent': Node('LearningMemoryAgent',
                run=agents['LearningMemoryAgent'].run,
                can_run=agents['LearningMemoryAgent'].can_run,
                repeatable=True),

            # Tech team can be re-invoked when Validate emits need_debate
            'MultiPerspectiveTechAgent': Node('MultiPerspectiveTechAgent',
                run=agents['MultiPerspectiveTechAgent'].run,
                can_run=agents['MultiPerspectiveTechAgent'].can_run,
                parallel_group="debate",
                repeatable=True),

            # Include capability + contract and make contract rerunnable
            'CapabilityAgent': Node('CapabilityAgent',
                run=agents['CapabilityAgent'].run,
                can_run=agents['CapabilityAgent'].can_run),

            'ContractAgent': Node('ContractAgent',
                run=agents['ContractAgent'].run,
                can_run=agents['ContractAgent'].can_run,
                repeatable=True),

            # NEW: ensure contract exists
            'ContractPresenceGuard': Node('ContractPresenceGuard',
                run=agents['ContractPresenceGuard'].run,
                can_run=agents['ContractPresenceGuard'].can_run,
                repeatable=True),

            # NEW: resolve "A or B" stacks
            'StackResolverAgent': Node('StackResolverAgent',
                run=agents['StackResolverAgent'].run,
                can_run=agents['StackResolverAgent'].can_run,
                repeatable=True),

            'ArchitectureAgent': Node('ArchitectureAgent',
                run=agents['ArchitectureAgent'].run,
                can_run=agents['ArchitectureAgent'].can_run),

            'DatabaseAgent': Node('DatabaseAgent',
                run=agents['DatabaseAgent'].run,
                can_run=agents['DatabaseAgent'].can_run),

            # 🔁 refinement loop nodes
            'CodeGenAgent': Node('CodeGenAgent',
                run=agents['CodeGenAgent'].run,
                can_run=agents['CodeGenAgent'].can_run,
                repeatable=True),

            'ValidateAgent': Node('ValidateAgent',
                run=agents['ValidateAgent'].run,
                can_run=agents['ValidateAgent'].can_run,
                repeatable=True),

            'ValidationRouter': Node('ValidationRouter',
                run=agents['ValidationRouter'].run,
                can_run=agents['ValidationRouter'].can_run,
                repeatable=True),

            'DeploymentAgent': Node('DeploymentAgent',
                run=agents['DeploymentAgent'].run,
                can_run=agents['DeploymentAgent'].can_run),

            'EvaluationAgent': Node('EvaluationAgent',
                run=agents['EvaluationAgent'].run,
                can_run=agents['EvaluationAgent'].can_run),
        }

        # Graph config: concurrency 3 lets Arch + DB possibly run in same tick; debate runs inside its own node
        cfg = GraphConfig(
            nodes=nodes,
            on_start=on_start,
            on_complete=on_complete,
            on_error=on_error,
            max_steps=50,
            concurrency=3,
            tick_sleep=0.0
        )

        runner = GraphRunner(cfg)
        final_state = runner.run(state)

        # learning phase (you had this already)
        if 'evaluation' in final_state and 'tech_stack' in final_state:
            evaluation = final_state['evaluation']
            overall_score = evaluation.get('overall_score', 5)
            self.orchestrator.learning_memory.learn_from_outcome(
                prompt, final_state['tech_stack'], overall_score
            )

        monitor.pipeline_completed(final_state)

# Initialize the UI-aware orchestrator
ui_orchestrator = UIAwareOrchestrator()

@app.route('/')
def dashboard():
    """Main dashboard showing project gallery and system status"""
    return render_template('dashboard.html', 
                         has_db=HAS_DB_SYSTEM, 
                         organic_available=ORGANIC_AVAILABLE)

@app.route('/organic')
def organic_intelligence():
    """Organic intelligence workflow page"""
    return render_template('organic_intelligence.html')

@app.route('/create/<mode>')
def create_project(mode):
    """Create new project page"""
    return render_template('create.html', mode=mode)

@app.route('/api/projects')
def get_projects():
    """Get all projects (from JSON storage or fallback)"""
    projects = []
    
    # Try to get from JSON storage first
    try:
        stored_projects = project_storage.get_projects(20)
        for proj in stored_projects:
            projects.append({
                'id': proj.get('id', ''),
                'name': proj.get('name', ''),
                'prompt': proj.get('prompt', ''),
                'status': proj.get('status', 'completed'),
                'created_at': proj.get('created_at', ''),
                'tech_stack': proj.get('tech_stack', [])
            })
        print(f"📊 Retrieved {len(projects)} projects from JSON storage")
    except Exception as e:
        print(f"⚠️ JSON storage error: {e}")
    
    # Add fallback in-memory projects if needed
    if not projects:
        for proj in monitor.saved_projects:
            projects.append({
                'id': proj.get('id', ''),
                'name': proj.get('name', ''),
                'prompt': proj.get('prompt', ''),
                'status': proj.get('status', 'completed'),
                'created_at': proj.get('created_at', ''),
                'tech_stack': proj.get('tech_stack', [])
            })
        print(f"📊 Using {len(projects)} projects from in-memory fallback")
    
    return jsonify(projects)

@app.route('/api/system/status')
def system_status():
    """Get system status"""
    status = {
        'organic_intelligence': ORGANIC_AVAILABLE,
        'database_system': HAS_DB_SYSTEM,
        'active_session': monitor.current_session is not None,
        'total_projects': len(monitor.saved_projects),
        'stats': monitor.stats,
        'download_ready': bool(monitor.project_data)
    }
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
                code_data = (
    monitor.project_data.get('best_generated_code')
    or monitor.project_data.get('generated_code')
)
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
    session_id = data.get('session_id', f'session_{int(time.time())}')
    
    if not ORGANIC_AVAILABLE:
        emit('error', {'message': 'Organic Intelligence system not available'})
        return
    
    if not prompt.strip():
        emit('error', {'message': 'Project prompt is required'})
        return
    
    # Run pipeline in background thread
    def run_pipeline():
        ui_orchestrator.run_pipeline_with_ui(prompt, session_id)
    
    thread = threading.Thread(target=run_pipeline)
    thread.daemon = True
    thread.start()

if __name__ == '__main__':
    print(f"🎭 Starting AgentForge v3 - Organic Intelligence Edition")
    print(f"📁 Root directory: {ROOT}")
    print(f"🤖 Organic Intelligence available: {ORGANIC_AVAILABLE}")
    print(f"💾 Database system available: {HAS_DB_SYSTEM}")
    
    socketio.run(app, host='0.0.0.0', port=5003, debug=True)
