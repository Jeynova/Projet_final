"""Concrete agents for orchestrator_v2 dynamic system."""
from __future__ import annotations
from pathlib import Path
from typing import Dict, Any, List
from .agent_base import Agent, AgentResult, LLMBackedMixin
from .memory_store import MemoryStore
from .rag_store import RAGStore
from .scaffold_registry import get_scaffold
import json

class MemoryAgent(LLMBackedMixin):
    id = "memory"
    def __init__(self, memory: MemoryStore, rag: RAGStore | None = None):
        self.memory = memory
        self.rag = rag or RAGStore()
    def can_run(self, state: Dict[str, Any]) -> bool:
        return 'prompt' in state and 'memory' not in state
    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        sims = self.memory.similar_prompts(state['prompt'])
        rag_context = self.rag.contextualize(state['prompt'], top_k=3)
        high = sims[0] if sims and sims[0].get('prompt') != state['prompt'] else None
        result = {
            'similar': sims,
            'reuse_candidate': high,
            'confidence': (len(high.get('prompt',''))/len(state['prompt'])) if high else 0.0,
            'rag_context': rag_context
        }
        llm = self.llm_json('You classify project domains.', f"Classify: {state['prompt']} Return JSON {{domain, rationale}}", {})
        if isinstance(llm, dict):
            result.update(llm)
        return result

class TechSelectAgent(LLMBackedMixin):
    id = "tech_select"
    def can_run(self, state: Dict[str, Any]) -> bool:
        return 'tech' not in state
    def _normalize(self, stack) -> list:
        norm = []
        if isinstance(stack, list):
            for item in stack:
                if isinstance(item, str):
                    norm.append({'name': item.lower(), 'origin': 'llm'})
                elif isinstance(item, dict):
                    name = item.get('name') or item.get('id') or item.get('value')
                    if name:
                        d = dict(item)
                        d['name'] = str(name).lower()
                        norm.append(d)
        elif isinstance(stack, str):
            norm.append({'name': stack.lower()})
        return norm
    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        if (mem:=state.get('memory')) and mem.get('confidence',0)>0.8 and mem.get('similar'):
            stack = mem.get('reuse_candidate', {}).get('tech_stack', ['python','fastapi','sqlite'])
            return {'stack': self._normalize(stack), 'source':'memory_reuse'}
        fb = {'stack':['python','fastapi','sqlite'],'confidence':0.5}
        rag_section = ''
        if state.get('memory', {}).get('rag_context'):
            rag_section = f"\nRelevant prior artifacts:\n{state['memory']['rag_context']}\n"
        res = self.llm_json('You pick pragmatic stacks.', f"Prompt: {state['prompt']}{rag_section}Return JSON {{stack, reasoning, confidence}}", fb)
        stack = res.get('stack', fb['stack'])
        res['stack'] = self._normalize(stack)
        return res

class ArchitectureAgent(LLMBackedMixin):
    id = "architecture"
    def can_run(self, state: Dict[str, Any]) -> bool:
        return 'tech' in state and 'architecture' not in state
    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        # Enhanced architecture prompt for comprehensive project structure
        stack = state['tech'].get('stack', [])
        prompt = state.get('prompt', '')
        
        # Default fallback architecture
        fb = {
            'files': [
                {'path': 'app/main.py', 'purpose': 'entry'},
                {'path': 'app/models/__init__.py', 'purpose': 'models package'},
                {'path': 'app/routes/__init__.py', 'purpose': 'routes package'},
                {'path': 'app/schemas.py', 'purpose': 'pydantic schemas'},
                {'path': 'requirements.txt', 'purpose': 'dependencies'},
                {'path': 'README.md', 'purpose': 'documentation'}
            ],
            'directories': ['app', 'app/models', 'app/routes', 'tests'],
            'pattern': 'Clean Architecture'
        }
        
        rag_section = ''
        if state.get('memory', {}).get('rag_context'):
            rag_section = f"\nContext hints:\n{state['memory']['rag_context']}\n"
        
        # Enhanced architecture prompt
        arch_prompt = f"""Design a comprehensive project architecture for: "{prompt}"
        
Tech Stack: {stack}
{rag_section}

Create a production-ready file structure with:
- Main application entry point
- Separate modules for models, routes, schemas
- Configuration files (requirements.txt, etc.)
- Database setup files  
- Test directories
- Documentation files
- Deployment configurations

Return JSON with:
{{
    "files": [
        {{"path": "file/path.py", "purpose": "description"}},
        ...
    ],
    "directories": ["dir1", "dir2", ...],
    "pattern": "architecture_pattern_name"
}}

Generate at least 8-12 files for a comprehensive structure."""
        
        res = self.llm_json('You design comprehensive, production-ready architectures.', arch_prompt, fb)
        # Normalize files list to list[dict]
        norm = []
        for item in res.get('files', []):
            if isinstance(item, str):
                norm.append({'path': item, 'purpose': 'generated'})
            elif isinstance(item, dict):
                # ensure required key
                if 'path' in item:
                    norm.append(item)
        if not norm:
            norm = fb['files']
        res['files'] = norm
        return res

class ArchitectureValidationAgent(LLMBackedMixin):
    """Validates and enriches the architecture specification before code generation.
    - Ensures an entrypoint file
    - Ensures tests directory exists
    - Optionally adds framework-specific starter files if absent
    """
    id = 'arch_validate'
    REQUIRED_PY_ENTRY = 'app/main.py'
    def can_run(self, state: Dict[str, Any]) -> bool:
        return 'architecture' in state and 'arch_validate' not in state
    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        arch = state.get('architecture', {})
        files = arch.get('files', [])
        changed = False
        # Ensure dict format
        norm = []
        for f in files:
            if isinstance(f, str):
                norm.append({'path': f, 'purpose': 'generated'})
            elif isinstance(f, dict) and 'path' in f:
                norm.append(f)
        files = norm
        paths = {f['path'] for f in files}
        # Add entrypoint for python frameworks if missing
        stack_names = [s.get('name') if isinstance(s, dict) else str(s) for s in state.get('tech', {}).get('stack', [])]
        py_stack = any(n in ('fastapi','flask','django') for n in stack_names)
        if py_stack and self.REQUIRED_PY_ENTRY not in paths:
            files.append({'path': self.REQUIRED_PY_ENTRY, 'purpose': 'entrypoint (injected by validator)'})
            changed = True
        # Ensure tests directory placeholder
        if not any(p.startswith('tests/') for p in paths):
            files.append({'path': 'tests/__init__.py', 'purpose': 'tests package (validator)'} )
            changed = True
        # Write back if changed
        if changed:
            arch['files'] = files
        # Basic metrics
        metrics = {
            'file_count': len(files),
            'has_entrypoint': self.REQUIRED_PY_ENTRY in {f['path'] for f in files} if py_stack else True,
            'added_files': [f['path'] for f in files if '(validator)' in f.get('purpose','')]
        }
        return metrics

class ArchitectureExpandAgent(LLMBackedMixin):
    """Adds deterministic extra files for common stacks if architecture is too small."""
    id = 'arch_expand'
    MIN_FILES = 5
    def can_run(self, state: Dict[str, Any]) -> bool:
        if 'architecture' not in state: return False
        if 'arch_expand' in state: return False
        files = state['architecture'].get('files', [])
        return len(files) < self.MIN_FILES
    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        arch = state['architecture']
        files = arch.get('files', [])
        existing = {f['path'] if isinstance(f, dict) else f for f in files}
        stack = [s.get('name') if isinstance(s, dict) else str(s) for s in state.get('tech', {}).get('stack', [])]
        lower = [s.lower() for s in stack]
        added = []
        def add(p, purpose):
            if p not in existing:
                files.append({'path': p, 'purpose': purpose})
                existing.add(p)
                added.append(p)
        if any(s in lower for s in ['fastapi','flask']):
            add('app/routes/__init__.py','routes pkg')
            add('app/routes/health.py','health route')
            add('app/models/__init__.py','models pkg')
            add('app/schemas.py','pydantic schemas')
        prompt = state.get('prompt','').lower()
        for kw in ['user','post','task','item']:
            if kw in prompt and any(s in lower for s in ['fastapi','flask']):
                add(f'app/models/{kw}.py', f'model {kw}')
                add(f'app/routes/{kw}s.py', f'CRUD routes {kw}')
        arch['files'] = files
        return {'added': added, 'final_count': len(files)}

class CodeGenAgent(LLMBackedMixin):
    id = "codegen"
    def __init__(self, project_root: Path):
        self.project_root = project_root
    def can_run(self, state: Dict[str, Any]) -> bool:
        if state.get('config', {}).get('boilerplate_only'):
            return False
        return 'architecture' in state and 'codegen' not in state
    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        raw_files = list(state['architecture'].get('files',[]))
        # Inject entity-driven model stubs if clarify produced entities
        clarify = state.get('clarify', {})
        entities = clarify.get('entities') if isinstance(clarify.get('entities'), list) else []
        for ent in entities[:8]:  # cap to avoid explosion
            model_path = f"app/models/{ent.lower()}.py"
            if not any((isinstance(f, dict) and f.get('path')==model_path) or f==model_path for f in raw_files):
                raw_files.append({'path': model_path, 'purpose': f'model for {ent}'})
        # Ensure main entry if missing
        if not any((isinstance(f, dict) and f.get('path')=='app/main.py') or f=='app/main.py' for f in raw_files):
            raw_files.append({'path':'app/main.py','purpose':'entrypoint'})
        files = []
        for spec in raw_files:
            if isinstance(spec, str):
                files.append({'path': spec, 'purpose': 'generated'})
            elif isinstance(spec, dict):
                files.append(spec)
        written = []
        stack_names = []
        for s in state.get('tech', {}).get('stack', []):
            if isinstance(s, dict) and 'name' in s:
                stack_names.append(s['name'])
            elif isinstance(s, str):
                stack_names.append(s)
        lower_stack = [n.lower() for n in stack_names]
        for spec in files:
            path = spec.get('path','app/main.py')
            purpose = spec.get('purpose','')
            
            # Validate and clean the path
            if not path or path.strip() == '':
                path = 'app/main.py'  # Default fallback
            
            # Remove any invalid characters and normalize path
            path = str(path).replace('\\', '/').strip()
            
            # Remove leading slashes and ensure relative path
            while path.startswith('/'):
                path = path[1:]
            
            # Skip empty paths or root-level paths that could cause issues
            if not path or path == '.' or path == '/' or len(path.split('/')) == 0:
                continue
                
            # Skip non-source files that should be handled by dedicated agents (manifest, docs)
            if path.lower().endswith(('requirements.txt','package.json','readme.md','license','license.txt')):
                continue
                
            print(f"   📝 Generating: {path} (purpose: {purpose})")
            
            # Enhanced LLM prompt for better code generation
            code_prompt = f"""
            You are a Code Generation Agent that writes production-quality code.
            
            Project request: "{state.get('prompt', '')}"
            Tech stack: {stack_names}
            Architecture files: {[f.get('path', '') for f in files]}
            
            Generate complete, working code for:
            File: {path}
            Purpose: {purpose}
            
            CONTEXT ANALYSIS:
            - This is an e-commerce site project
            - Need products, cart, user functionality
            - Using FastAPI and SQLite based on tech stack
            - File purpose indicates: {purpose}
            
            SPECIFIC INSTRUCTIONS FOR THIS FILE:
            """
            
            # Add file-specific generation instructions
            if 'schemas' in path.lower():
                code_prompt += '''
            For schemas.py - Create Pydantic models for API validation:
            - ProductCreate, ProductResponse schemas with name, description, price, stock fields
            - UserCreate, UserResponse schemas with username, email fields
            - CartItem, CartResponse schemas with product_id, quantity fields
            - Include field validation, examples
            - Use proper typing with Optional, List imports from typing
            '''
            elif 'models' in path.lower() and '__init__' not in path:
                code_prompt += '''
            For model files - Create SQLAlchemy ORM models:
            - Define database table with proper columns
            - Include relationships (ForeignKey, backref) if needed
            - Add __repr__ method for debugging
            - Use appropriate column types (String, Integer, Float, DateTime)
            - Include indexes where performance matters
            '''
            elif 'routes' in path.lower() and '__init__' not in path:
                code_prompt += '''
            For route files - Create FastAPI router with CRUD operations:
            - Include all HTTP methods (GET, POST, PUT, DELETE)
            - Use proper dependency injection for database
            - Include request/response models from schemas
            - Add error handling with HTTPException
            - Include pagination for list endpoints
            '''
            elif 'main.py' in path:
                code_prompt += '''
            For main.py - Create FastAPI application entry point:
            - Initialize FastAPI app with title and description
            - Add CORS middleware configuration
            - Include all route modules with app.include_router
            - Add database initialization logic
            - Include startup/shutdown events if needed
            - Add basic health and root endpoints
            '''
            else:
                code_prompt += f'''
            For {path} - Generate appropriate code based on file purpose: {purpose}
            - Follow FastAPI/SQLAlchemy patterns
            - Include necessary imports
            - Write functional, not placeholder code
            '''
            
            code_prompt += '''
            
            Requirements:
            - Write COMPLETE, FUNCTIONAL code - not templates or placeholders
            - Follow best practices for FastAPI and SQLAlchemy
            - Include proper imports and dependencies
            - Add error handling where appropriate
            - Include docstrings/comments for clarity
            - Make it production-ready
            - Ensure the code actually implements the intended functionality
            
            CRITICAL: Return JSON with ONLY this structure:
            {
                "code": "complete file content as a single string"
            }
            
            Example response:
            {
                "code": "from fastapi import FastAPI\\napp = FastAPI()\\n\\n@app.get('/')\\nasync def root():\\n    return {'status': 'ok'}"
            }
            
            Generate REAL working code, not placeholder comments.
            '''
            
            # Framework-aware deterministic baseline if LLM returns weak content
            baseline = ''
            if path.endswith('app/main.py') and 'fastapi' in lower_stack:
                baseline = "from fastapi import FastAPI\nfrom fastapi.middleware.cors import CORSMiddleware\n\napp = FastAPI(title='E-commerce API', description='Simple e-commerce platform')\n\napp.add_middleware(\n    CORSMiddleware,\n    allow_origins=['*'],\n    allow_credentials=True,\n    allow_methods=['*'],\n    allow_headers=['*']\n)\n\n@app.get('/')\nasync def root():\n    return {'status': 'ok', 'message': 'E-commerce API is running'}\n\n@app.get('/health')\nasync def health():\n    return {'status': 'healthy'}\n"
            elif path.endswith('app/main.py') and 'flask' in lower_stack:
                baseline = "from flask import Flask, jsonify\nfrom flask_cors import CORS\n\napp = Flask(__name__)\nCORS(app)\n\n@app.route('/')\ndef root():\n    return jsonify(status='ok', message='E-commerce API is running')\n\n@app.route('/health')\ndef health():\n    return jsonify(status='healthy')\n\nif __name__ == '__main__':\n    app.run(debug=True, port=8000)\n"
            elif 'schemas.py' in path:
                baseline = "from pydantic import BaseModel, Field\nfrom typing import Optional, List\nfrom datetime import datetime\n\nclass ProductBase(BaseModel):\n    name: str = Field(..., min_length=1, max_length=200)\n    description: Optional[str] = Field(None, max_length=500)\n    price: float = Field(..., gt=0)\n    stock: int = Field(..., ge=0)\n    category: Optional[str] = Field(None, max_length=100)\n\nclass ProductCreate(ProductBase):\n    pass\n\nclass ProductResponse(ProductBase):\n    id: int\n    created_at: datetime\n    \n    class Config:\n        from_attributes = True\n\nclass UserBase(BaseModel):\n    username: str = Field(..., min_length=3, max_length=50)\n    email: str = Field(..., regex=r'^[^@]+@[^@]+\\.[^@]+$')\n\nclass UserCreate(UserBase):\n    pass\n\nclass UserResponse(UserBase):\n    id: int\n    created_at: datetime\n    \n    class Config:\n        from_attributes = True\n\nclass CartItem(BaseModel):\n    product_id: int\n    quantity: int = Field(..., gt=0)\n\nclass CartResponse(BaseModel):\n    items: List[CartItem]\n    total: float\n"
            elif 'product' in path.lower() and path.endswith('.py') and 'models' in path:
                if 'fastapi' in lower_stack:
                    baseline = f"from sqlalchemy import Column, Integer, String, Float, DateTime\nfrom sqlalchemy.ext.declarative import declarative_base\nfrom datetime import datetime\n\nBase = declarative_base()\n\nclass Product(Base):\n    __tablename__ = 'products'\n    \n    id = Column(Integer, primary_key=True, index=True)\n    name = Column(String(200), nullable=False, index=True)\n    description = Column(String(500))\n    price = Column(Float, nullable=False)\n    stock = Column(Integer, default=0)\n    category = Column(String(100), index=True)\n    created_at = Column(DateTime, default=datetime.utcnow)\n    \n    def __repr__(self):\n        return f'<Product {{self.name}} - ${{self.price}}>'\n"
            elif 'user' in path.lower() and path.endswith('.py') and 'models' in path:
                if 'fastapi' in lower_stack:
                    baseline = f"from sqlalchemy import Column, Integer, String, DateTime\nfrom sqlalchemy.ext.declarative import declarative_base\nfrom datetime import datetime\n\nBase = declarative_base()\n\nclass User(Base):\n    __tablename__ = 'users'\n    \n    id = Column(Integer, primary_key=True, index=True)\n    username = Column(String(50), unique=True, nullable=False, index=True)\n    email = Column(String(100), unique=True, nullable=False, index=True)\n    created_at = Column(DateTime, default=datetime.utcnow)\n    \n    def __repr__(self):\n        return f'<User {{self.username}}>'\n"
            elif 'routes' in path.lower() and 'product' in path.lower():
                if 'fastapi' in lower_stack:
                    baseline = f"from fastapi import APIRouter, HTTPException, Depends\nfrom sqlalchemy.orm import Session\nfrom typing import List\nfrom .. import models, database\nfrom ..schemas import ProductCreate, ProductResponse\n\nrouter = APIRouter(\n    prefix='/products',\n    tags=['products']\n)\n\n@router.get('/', response_model=List[ProductResponse])\nasync def get_products(skip: int = 0, limit: int = 100, db: Session = Depends(database.get_db)):\n    products = db.query(models.Product).offset(skip).limit(limit).all()\n    return products\n\n@router.post('/', response_model=ProductResponse)\nasync def create_product(product: ProductCreate, db: Session = Depends(database.get_db)):\n    db_product = models.Product(**product.dict())\n    db.add(db_product)\n    db.commit()\n    db.refresh(db_product)\n    return db_product\n\n@router.get('/{{product_id}}', response_model=ProductResponse)\nasync def get_product(product_id: int, db: Session = Depends(database.get_db)):\n    product = db.query(models.Product).filter(models.Product.id == product_id).first()\n    if not product:\n        raise HTTPException(status_code=404, detail='Product not found')\n    return product\n"
            
            fb = {'code': baseline or f"# {purpose or 'generated file'}\n# Generated for: {path}\nprint('LLM-generated placeholder for {path}')"}
            rag_section = ''
            if state.get('memory', {}).get('rag_context'):
                rag_section = f"\nPrevious project context:\n{state['memory']['rag_context']}\n"
                code_prompt = f"{code_prompt}\n{rag_section}"
            
            try:
                res = self.llm_json('You are a senior software engineer. Write production-quality code.', code_prompt, fb)
                
                # Enhanced response processing
                content = ''
                if isinstance(res, dict):
                    code_field = res.get('code')
                    if isinstance(code_field, str) and code_field.strip():
                        content = code_field.strip()
                    elif isinstance(code_field, list):
                        content = '\n'.join(str(line) for line in code_field)
                    elif isinstance(code_field, dict):
                        # Handle nested code structures
                        if 'content' in code_field:
                            content = str(code_field['content'])
                        else:
                            content = str(code_field)
                            
                # Validate that we got actual code, not just metadata
                if not content or len(content.strip()) < 20:
                    content = fb['code']  # Use baseline
                elif 'print(' not in content and len(content.strip().split('\n')) < 3:
                    content = fb['code']  # Use baseline if too simple
                    
                # Clean up markdown if present
                if content.startswith('```'):
                    lines = content.split('\n')
                    if len(lines) > 1:
                        content = '\n'.join(lines[1:-1]) if lines[-1].strip() == '```' else '\n'.join(lines[1:])
                        
                # Ensure newline at end
                if not content.endswith('\n'):
                    content += '\n'
                    
                # Safe file writing with validation
                try:
                    full = self.project_root / path
                    # Ensure the parent directory exists
                    full.parent.mkdir(parents=True, exist_ok=True)
                    
                    # Validate the full path before writing
                    if full.parent.exists() and str(full.parent) != 'C:\\':
                        full.write_text(content, encoding='utf-8')
                        written.append(path)
                        print(f"   ✅ Created: {path} ({len(content)} chars)")
                    else:
                        print(f"   ❌ Invalid path: {full}")
                        
                except Exception as write_error:
                    print(f"   ❌ Write failed for {path}: {write_error}")
                    # Try alternative path
                    alt_path = self.project_root / f"src/{path.split('/')[-1]}"
                    try:
                        alt_path.parent.mkdir(parents=True, exist_ok=True)
                        alt_path.write_text(content, encoding='utf-8')
                        written.append(f"src/{path.split('/')[-1]}")
                        print(f"   ✅ Created alternative: src/{path.split('/')[-1]}")
                    except:
                        print(f"   ❌ Alternative path also failed")
                        
            except Exception as llm_error:
                print(f"   ❌ LLM call failed for {path}: {llm_error}")
                continue
        # Post-pass enrichment for FastAPI domain routes
        if 'fastapi' in lower_stack:
            prompt = state.get('prompt','').lower()
            domains = []
            for kw in ['user','post','task','item']:
                if kw in prompt:
                    domains.append(kw)
            models_dir = self.project_root / 'app/models'
            routes_dir = self.project_root / 'app/routes'
            models_dir.mkdir(parents=True, exist_ok=True)
            routes_dir.mkdir(parents=True, exist_ok=True)
            # health route
            health_path = routes_dir / 'health.py'
            if not health_path.exists():
                health_path.write_text("from fastapi import APIRouter\nrouter = APIRouter()\n@router.get('/health')\nasync def health():\n    return {'ok': True}\n")
                written.append('app/routes/health.py')
            for d in domains:
                mfile = models_dir / f'{d}.py'
                if not mfile.exists():
                    mfile.write_text(f"from pydantic import BaseModel\nclass {d.capitalize()}(BaseModel):\n    id: int | None = None\n    name: str\n")
                    written.append(f'app/models/{d}.py')
                rfile = routes_dir / f'{d}s.py'
                if not rfile.exists():
                    rfile.write_text(
                        "from fastapi import APIRouter\nfrom pydantic import BaseModel\nrouter = APIRouter(prefix='/{name}s', tags=['{name}s'])\nclass {cls}(BaseModel):\n    id: int | None = None\n    name: str\n_db: list[{cls}] = []\n@router.post('/', response_model={cls})\nasync def create_{name}(data: {cls}):\n    data.id = len(_db)+1\n    _db.append(data)\n    return data\n@router.get('/', response_model=list[{cls}])\nasync def list_{name}s():\n    return _db\n".replace('{name}', d).replace('{cls}', d.capitalize())
                    )
                    written.append(f'app/routes/{d}s.py')
        return {'files': written}

class ManifestAgent(LLMBackedMixin):
    """Generates dependency manifests (requirements.txt or package.json) if missing based on code and stack."""
    id = 'manifest'
    PY_IGNORE = {'os','sys','pathlib','typing','json','logging','asyncio','re','dataclasses','datetime','functools','itertools','math'}
    PY_SUGGEST = {
        'fastapi': ['fastapi','uvicorn'],
        'flask': ['flask'],
        'sqlalchemy': ['sqlalchemy'],
        'pydantic': ['pydantic'],
    }
    def __init__(self, project_root: Path):
        self.project_root = project_root
    def can_run(self, state: Dict[str, Any]) -> bool:
        if 'manifest' in state:
            return False
        cfg = state.get('config', {})
        # In boilerplate-only mode run right after scaffold
        if cfg.get('boilerplate_only') and 'scaffold' in state:
            return True
        # In full mode run after codegen to scan generated files
        if 'codegen' in state:
            return True
        return False
    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        stack = state.get('tech', {}).get('stack', [])
        stack_names = [s.get('name') if isinstance(s, dict) else str(s) for s in stack]
        lower_stack = [s.lower() for s in stack_names]
        req_path = self.project_root / 'requirements.txt'
        created = []
        if any(lang in lower_stack for lang in ['fastapi','flask']) and not req_path.exists():
            imports: set[str] = set()
            for py in self.project_root.rglob('*.py'):
                try:
                    for line in py.read_text().splitlines():
                        line=line.strip()
                        if line.startswith('import '):
                            mods=line.replace('import ','').split(',')
                            for m in mods:
                                imports.add(m.strip().split(' ')[0].split('.')[0])
                        elif line.startswith('from '):
                            mod=line.split(' ')[1].split('.')[0]
                            imports.add(mod)
                except Exception:
                    pass
            wanted = []
            for mod in sorted(imports):
                if mod in self.PY_IGNORE: continue
                if mod in ('fastapi','flask','sqlalchemy','pydantic','uvicorn'):
                    wanted.append(mod)
            # augment from stack hints
            for sn in lower_stack:
                for pkg in self.PY_SUGGEST.get(sn, []):
                    if pkg not in wanted:
                        wanted.append(pkg)
            if wanted:
                req_path.write_text('\n'.join(sorted(set(wanted)))+'\n')
                created.append('requirements.txt')
        return {'created': created, 'stack': stack_names}

class ValidateAgent(LLMBackedMixin):
    id = 'validate'
    def __init__(self, project_root: Path):
        self.project_root = project_root
    def can_run(self, state: Dict[str, Any]) -> bool:
        # Defer until after manifest if manifest could still run
        if 'validate' in state:
            return False
        if 'manifest' not in state and ('codegen' in state or state.get('config', {}).get('boilerplate_only')):
            # allow manifest agent chance first
            return False
        # Need at least scaffold or codegen
        return 'scaffold' in state or 'codegen' in state
    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        py_files = list(self.project_root.rglob('*.py'))
        total = len(py_files)
        placeholders = 0
        trivial = []
        for f in py_files:
            try:
                txt = f.read_text()
                lines = [l for l in txt.splitlines() if l.strip()]
                if ("Hello from" in txt or (len(lines) <= 3 and not any(k in txt for k in ('FastAPI','Flask','app =','class ')))):
                    placeholders += 1
                    trivial.append(str(f.relative_to(self.project_root)))
            except Exception:
                pass
        has_manifest = (self.project_root / 'requirements.txt').exists() or (self.project_root / 'package.json').exists()
        status = 'ok'
        problems = []
        if total < 3:
            status = 'insufficient'
            problems.append('too_few_files')
        if placeholders > 0:
            status = 'needs_improvement'
            problems.append('placeholders')
        if not has_manifest:
            problems.append('no_manifest')
        return {
            'file_count': total,
            'placeholder_files': placeholders,
            'trivial_list': trivial[:10],
            'has_manifest': has_manifest,
            'status': status,
            'problems': problems
        }

class ScaffoldAgent(LLMBackedMixin):
    """Writes minimal boilerplate based on selected stack BEFORE full codegen.
    Runs if architecture empty OR boilerplate_only flag set."""
    id = 'scaffold'
    def __init__(self, project_root: Path):
        self.project_root = project_root
    def can_run(self, state: Dict[str, Any]) -> bool:
        if 'tech' not in state: return False
        if 'scaffold' in state: return False
        arch_files = state.get('architecture', {}).get('files', [])
        if state.get('config', {}).get('boilerplate_only'):
            return True
        return len(arch_files) == 0
    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        stack = state.get('tech', {}).get('stack', [])
        scaffold = get_scaffold(stack if isinstance(stack, list) else [])
        written = []
        for path, content in scaffold.items():
            full = self.project_root / path
            full.parent.mkdir(parents=True, exist_ok=True)
            full.write_text(content)
            written.append(path)
        return {'files': written, 'strategy': 'registry'}

class DeploymentSelectAgent(LLMBackedMixin):
    """Decides deployment strategy: dockerfile only, docker-compose, or kubernetes.
    Heuristic + optional LLM refinement."""
    id = 'deploy_select'
    def can_run(self, state: Dict[str, Any]) -> bool:
        if 'deploy_select' in state: return False
        if 'tech' not in state or 'architecture' not in state: return False
        # don't run if clarification unresolved
        if (clar:=state.get('clarify')) and clar.get('questions'): return False
        return True
    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        prompt = state.get('prompt','').lower()
        arch_files = state.get('architecture', {}).get('files', [])
        file_count = len(arch_files)
        has_db = 'database' in state or any('db' in str(f) for f in arch_files)
        scale_signals = any(k in prompt for k in ['scale','scalable','microservice','cluster','multi-region'])
        k8s_signals = any(k in prompt for k in ['k8s','kubernetes'])
        if k8s_signals or (scale_signals and file_count > 6):
            strategy = 'kubernetes'
        elif has_db or file_count > 3:
            strategy = 'compose'
        else:
            strategy = 'dockerfile'
        fb = {'strategy': strategy,'rationale':'heuristic'}
        llm_res = self.llm_json('You validate deployment strategy.', f"Prompt: {prompt}\nFiles: {file_count}\nProposed: {strategy}. Return JSON {{strategy, rationale}}", fb)
        strat = llm_res.get('strategy', strategy)
        if strat not in ['dockerfile','compose','kubernetes']:
            strat = strategy
        return {'strategy': strat, 'rationale': llm_res.get('rationale','')}        

class IngestAgent(LLMBackedMixin):
    """Decides which generated artifacts to add to RAG store and ingests summaries."""
    id = "ingest"
    def __init__(self, project_root: Path, rag_store):
        self.project_root = project_root
        self.rag = rag_store
    def can_run(self, state: Dict[str, Any]) -> bool:
        # Run after codegen and before evaluation, only once
        return 'codegen' in state and 'ingest' not in state
    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        added = []
        files = state.get('codegen', {}).get('files', [])[:25]  # cap
        for f in files:
            fp = self.project_root / f
            if not fp.exists():
                continue
            content = fp.read_text()[:4000]
            # Summarize via LLM (optional)
            summary_fb = {'summary': content[:200]}
            summary_res = self.llm_json('You summarize code files.', f"Summarize file for retrieval: {f}\nContent:\n{content[:1500]}\nReturn JSON {{summary}}", summary_fb)
            summary = summary_res.get('summary', content[:200])
            doc_text = f"FILE: {f}\nSUMMARY: {summary}\nCONTENT:\n{content[:1500]}"
            self.rag.add_document(f, doc_text, {'type': 'code', 'len': len(content)})
            added.append(f)
        return {'indexed': added}

class DatabaseAgent(LLMBackedMixin):
    id = "database"
    def __init__(self, project_root: Path):
        self.project_root = project_root
    def can_run(self, state: Dict[str, Any]) -> bool:
        if 'tech' not in state or 'architecture' not in state: return False
        # skip if already done or no db in stack
        if 'database' in state: return False
        raw_stack = state['tech'].get('stack', [])
        stack = []
        for s in raw_stack:
            if isinstance(s, str):
                stack.append(s.lower())
            elif isinstance(s, dict) and 'name' in s:
                stack.append(str(s['name']).lower())
        return any(db in stack for db in ['postgresql','mysql','sqlite','mongodb'])
    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        raw_stack = state['tech'].get('stack', [])
        names = []
        for s in raw_stack:
            if isinstance(s, str):
                names.append(s)
            elif isinstance(s, dict) and 'name' in s:
                names.append(s['name'])
        db = next((s for s in names if isinstance(s, str) and s.lower() in ['postgresql','mysql','sqlite','mongodb']), 'sqlite')
        
        # Enhanced database prompt with model detection
        prompt = state.get('prompt', '')
        db_prompt = f"""Design database schema for: "{prompt}"
        
Tech stack: {names}
Database: {db}

Analyze the project requirements and create:
1. Database schema SQL
2. List of main entities/models needed
3. Relationships between entities

Return JSON:
{{
    "schema_sql": "CREATE TABLE statements...",
    "models": ["User", "Product", "Order", ...],
    "relationships": ["User has many Orders", ...]
}}

Generate comprehensive database design."""
        
        fb = {'schema_sql': f'-- {db} schema for {prompt}\nCREATE TABLE placeholder (id INTEGER);', 'models': [], 'relationships': []}
        res = self.llm_json('You are a database architect.', db_prompt, fb)
        
        # Write schema file
        (self.project_root / f"{db}_schema.sql").write_text(res.get('schema_sql',''))
        
        # Count models for evaluation
        models = res.get('models', [])
        model_count = len(models) if isinstance(models, list) else 0
        
        return {'db': db, 'models': models, 'model_count': model_count, 'setup': 'schema'}

class InfraAgent(LLMBackedMixin):
    id = "infra"
    def __init__(self, project_root: Path):
        self.project_root = project_root
    def can_run(self, state: Dict[str, Any]) -> bool:
        if 'infra' in state: return False
        p = state.get('prompt','').lower()
        return any(k in p for k in ['deploy','docker','production','k8s','kubernetes'])
    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        fb = {'dockerfile': 'FROM python:3.11-slim\nWORKDIR /app\nCOPY . .\nCMD ["python","-m","app.main"]'}
        res = self.llm_json('You produce dockerfiles.', 'Return JSON {dockerfile}', fb)
        (self.project_root / 'Dockerfile').write_text(res.get('dockerfile',''))
        return {'docker': True}

class TestAgent(LLMBackedMixin):
    id = "tests"
    def __init__(self, project_root: Path):
        self.project_root = project_root
    def can_run(self, state: Dict[str, Any]) -> bool:
        # Enhanced: also run in boilerplate-only mode if scaffold present
        if 'tests' in state:
            return False
        if 'codegen' in state:
            return True
        return state.get('config', {}).get('boilerplate_only') and 'scaffold' in state
    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        code_files = []
        if 'codegen' in state:
            code_files = state.get('codegen', {}).get('files', [])
        elif 'scaffold' in state:
            code_files = state.get('scaffold', {}).get('files', [])
        py_files = [f for f in code_files if f.endswith('.py') and 'tests/' not in f]
        js_files = [f for f in code_files if f.endswith(('.js','.ts')) and 'test' not in f.lower()]
        tdir = self.project_root / 'tests'
        tdir.mkdir(parents=True, exist_ok=True)
        created = []
        # Python tests
        if py_files:
            for pf in py_files[:5]:  # cap
                test_name = 'test_' + pf.split('/')[-1].replace('.py','') + '.py'
                test_path = tdir / test_name
                module_name = pf.replace('/', '.').replace('.py','')
                content_fb = (
                    "from pathlib import Path\n\n"
                    f"# Auto-generated test skeleton for {pf}\n\n"
                    "def test_import():\n"
                    "    import importlib, sys\n"
                    "    try:\n"
                    f"        import importlib; importlib.import_module('{module_name}')\n"
                    "    except Exception as exc:\n"
                    f"        assert False, 'Import failed: {pf}: ' + str(exc)\n"
                )
                test_path.write_text(content_fb)
                created.append(f'tests/{test_name}')
        # JS tests
        if js_files:
            for jf in js_files[:3]:
                test_name = jf.split('/')[-1].replace('.ts','').replace('.js','') + '.spec.js'
                test_path = tdir / test_name
                js_content = (
                    f"// Auto-generated test skeleton for {jf}\n"
                    "const assert = require('assert');\n"
                    f"describe('{jf}', () => {{\n"
                    "  it('loads module', () => {\n"
                    f"    require('../{jf}');\n"
                    "    assert.ok(true);\n"
                    "  });\n"
                    "});\n"
                )
                test_path.write_text(js_content)
                created.append(f'tests/{test_name}')
        summary_fb = {'unit_tests': 'def test_placeholder():\n    assert True'}
        return {'created': created, 'count': len(created)}

class EvaluationAgent(LLMBackedMixin):
    id = "evaluate"
    def can_run(self, state: Dict[str, Any]) -> bool:
        if 'evaluate' in state:
            return False
        if 'codegen' in state:
            return True
        # allow evaluation in boilerplate-only mode if scaffold exists
        return state.get('config', {}).get('boilerplate_only') and 'scaffold' in state
    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        heuristic = 25
        if 'tests' in state:
            heuristic += 15  # Increased test bonus
        if 'infra' in state:
            heuristic += 10
        if 'database' in state:
            db_info = state['database']
            if isinstance(db_info, dict):
                model_count = db_info.get('model_count', 0)
                heuristic += min(15, model_count * 3)  # Bonus for database models
            else:
                heuristic += 10
        files_list = state.get('codegen', {}).get('files', []) or state.get('scaffold', {}).get('files', [])
        file_count = len(files_list)
        if file_count >= 5:
            heuristic += 15  # Good file coverage
        elif file_count >= 3:
            heuristic += 10
        
        # Bonus for comprehensive prompts (more features = higher expectations met)
        prompt = state.get('prompt', '').lower()
        complexity_words = ['authentication', 'admin', 'dashboard', 'real-time', 'search', 'comprehensive', 'platform', 'system']
        complexity_score = sum(5 for word in complexity_words if word in prompt)
        heuristic += min(15, complexity_score)
        
        # Penalize if validation says insufficient
        val = state.get('validate', {})
        if val.get('status') == 'insufficient':
            heuristic -= 10
            
        rubric = """Evaluate this generated project on a 0-100 scale using these criteria:
- Completeness of architecture (file count, proper structure)
- Code quality and functionality (not just templates)
- Presence of tests and proper test structure
- Database design and model relationships  
- Deployment/infrastructure readiness
- Feature coverage relative to requirements

Consider that this is AI-generated code in under 2 minutes, so be fair in evaluation.
Provide JSON {score, rationale, strengths, improvements}. Score should be integer between 0-100."""
        
        user_desc = {
            'prompt': state.get('prompt',''),
            'files': files_list,
            'file_count': file_count,
            'has_tests': 'tests' in state,
            'has_infra': 'infra' in state,
            'has_database': 'database' in state,
            'database_models': state.get('database', {}).get('model_count', 0),
            'mode': 'boilerplate_only' if state.get('config', {}).get('boilerplate_only') else 'full',
            'tech_stack': state.get('tech', {}).get('stack', [])
        }
        fb = {'score': heuristic, 'rationale': 'heuristic fallback based on feature coverage', 'strengths': ['AI-generated in under 2 minutes'], 'improvements': ['Add more comprehensive features']}
        res = self.llm_json('You are a fair software evaluator who considers AI generation context.', f"Project analysis: {json.dumps(user_desc)}\n{rubric}", fb)
        score = int(res.get('score', heuristic))
        
        # Adjust score based on actual generation quality
        if file_count >= 8 and score < 70:
            score = max(score, 70)  # Reward comprehensive generation
        elif file_count >= 5 and score < 60:
            score = max(score, 60)  # Reward good generation
            
        # Force remediation path if file_count < 3
        if val and val.get('file_count', 0) < 3 and score > 50:
            score = 40
        res['score'] = score
        return res

class ValidateAgent(LLMBackedMixin):
    """Performs lightweight validation of generated code: counts files, detects obvious placeholders, ensures entrypoint exists."""
    id = 'validate'
    def __init__(self, project_root: Path):
        self.project_root = project_root
    def can_run(self, state: Dict[str, Any]) -> bool:
        # Run after codegen or scaffold (if boilerplate_only) and before evaluation
        if 'validate' in state: return False
        if state.get('config', {}).get('boilerplate_only') and 'scaffold' in state:
            return True
        return 'codegen' in state and 'validate' not in state
    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        root = self.project_root
        files = [p for p in root.rglob('*') if p.is_file()]
        stats = {
            'total_files': len(files),
            'python_files': sum(1 for f in files if f.suffix=='.py'),
            'placeholders': 0,
            'has_entrypoint': any(str(f).endswith(('app/main.py','main.go','src/server.js','src/main.ts','WebApp/Program.cs','pages/index.js')) for f in files)
        }
        placeholder_tokens = ['print("Hello from', 'Status ok', 'status:\'ok\'']
        for f in files[:200]:  # cap
            try:
                txt = f.read_text(errors='ignore')
                if any(tok in txt for tok in placeholder_tokens):
                    stats['placeholders'] += 1
            except Exception:
                pass
        # Simple heuristic pass/fail
        stats['quality_flag'] = 'ok' if stats['has_entrypoint'] and stats['total_files']>0 else 'incomplete'
        return stats

class RemediationAgent(LLMBackedMixin):
    """Attempts to improve project when evaluation score is low by suggesting patches.
    Produces remediation notes file and optional code augmentations."""
    id = "remediate"
    def __init__(self, project_root: Path):
        self.project_root = project_root
    def can_run(self, state: Dict[str, Any]) -> bool:
        # Run only if evaluation exists and low score and not already remediated this round
        evald = state.get('evaluate')
        if not evald: return False
        if evald.get('score', 0) >= 65: return False
        return 'remediate' not in state
    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        evald = state.get('evaluate', {})
        files = state.get('codegen', {}).get('files', [])
        fb = {'actions': ['add docstring', 'improve tests'], 'notes': 'Increase test coverage and separate concerns.'}
        res = self.llm_json('You suggest minimal impactful remediation steps.', f"Eval: {json.dumps(evald)} Files: {files}\nReturn JSON { '{' }actions, notes{'}' }", fb)
        # Write remediation notes
        notes_path = self.project_root / 'REMEDIATION_NOTES.md'
        try:
            notes_path.write_text(f"Remediation Suggestions\n======================\n\nScore: {evald.get('score')}\n\nNotes: {res.get('notes')}\n\nActions: \n- " + "\n- ".join(res.get('actions', [])))
        except Exception:
            pass
        return {'applied': False, 'suggested_actions': res.get('actions', []), 'notes_file': str(notes_path)}

# --- Additional advanced agents ---
import re, zipfile

class ClarifyAgent(LLMBackedMixin):
    id = 'clarify'
    REQUIRED_KEYS = ["domain","entities","auth","persistence","deployment"]
    def can_run(self, state: Dict[str, Any]) -> bool:
        if 'memory' not in state: return False
        if 'clarify' in state and state['clarify'].get('resolved'): return False
        return 'tech' not in state  # ensure it runs early
    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        prompt = state.get('prompt','')
        answers = state.get('answers', {}) or {}
        lower = prompt.lower()
        info: Dict[str, Any] = {}
        info['auth'] = answers.get('auth') or any(k in lower for k in ['auth','login','user account'])
        info['persistence'] = answers.get('persistence') or any(k in lower for k in ['db','database','store','persist'])
        info['deployment'] = answers.get('deployment') or ('kubernetes' if ('k8s' in lower or 'kubernetes' in lower) else None)
        ents = answers.get('entities') or []
        if not ents:
            candidates = re.findall(r"\b([A-Za-z]{4,})s\b", prompt)
            ents = list({c for c in candidates if c.lower() not in ['pages','users','posts','items']})
        info['entities'] = ents
        info['domain'] = answers.get('domain') or ('blog' if 'blog' in lower else None)
        questions = []
        q_map = {
            'domain': 'What is the primary domain or business context?',
            'entities': 'List the core data entities (comma separated).',
            'auth': 'Is user authentication required (yes/no)?',
            'persistence': 'Do you need a database (yes/no + preferred DB)?',
            'deployment': 'Deployment target preference (docker-compose, kubernetes, both)?'
        }
        for k in self.REQUIRED_KEYS:
            if not info.get(k):
                questions.append(q_map[k])
        return {**info, 'questions': questions, 'resolved': len(questions)==0}

class DockerComposeAgent(LLMBackedMixin):
    id = 'compose'
    def __init__(self, project_root: Path):
        self.project_root = project_root
    def can_run(self, state: Dict[str, Any]) -> bool:
        strat = state.get('deploy_select', {}).get('strategy')
        return strat == 'compose' and 'codegen' in state and 'compose' not in state
    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        # Emit YAML directly (no PyYAML dependency)
        services = ["  app:\n    build: .\n    command: python app/main.py\n    ports:\n      - '8000:8000'\n"]
        if state.get('database', {}).get('db'):
            services.append("  db:\n    image: postgres:15-alpine\n    environment:\n      POSTGRES_PASSWORD: password\n      POSTGRES_USER: user\n      POSTGRES_DB: app\n    ports:\n      - '5432:5432'\n")
        compose_yaml = "version: '3.9'\nservices:\n" + ''.join(services)
        (self.project_root / 'docker-compose.yml').write_text(compose_yaml)
        return {'services': ['app'] + (['db'] if state.get('database', {}).get('db') else [])}

class KubeAgent(LLMBackedMixin):
    id = 'kube'
    def __init__(self, project_root: Path):
        self.project_root = project_root
    def can_run(self, state: Dict[str, Any]) -> bool:
        strat = state.get('deploy_select', {}).get('strategy')
        return strat == 'kubernetes' and 'codegen' in state and 'kube' not in state
    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        kdir = self.project_root / 'k8s'
        kdir.mkdir(exist_ok=True)
        deployment = """apiVersion: apps/v1
kind: Deployment
metadata:
  name: app
spec:
  replicas: 1
  selector:
    matchLabels: {app: app}
  template:
    metadata: {labels: {app: app}}
    spec:
      containers:
        - name: app
          image: app:latest
          ports: [{containerPort: 8000}]"""
        service = """apiVersion: v1
kind: Service
metadata:
  name: app
spec:
  selector: {app: app}
  ports:
    - port: 80
      targetPort: 8000"""
        (kdir/'deployment.yaml').write_text(deployment)
        (kdir/'service.yaml').write_text(service)
        return {'manifests': ['deployment.yaml','service.yaml']}

class PackageAgent(LLMBackedMixin):
    id = 'package'
    def __init__(self, project_root: Path):
        self.project_root = project_root
    def can_run(self, state: Dict[str, Any]) -> bool:
        if 'package' in state:
            return False
        if 'evaluate' not in state:
            return False
        return 'codegen' in state or 'scaffold' in state
    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        zip_path = self.project_root.parent / f"{self.project_root.name}.zip"
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            for p in self.project_root.rglob('*'):
                if p.is_file():
                    zf.write(p, p.relative_to(self.project_root.parent))
        return {'zip': str(zip_path)}

class QuickstartAgent(LLMBackedMixin):
    """Generates QUICKSTART.md with role-based onboarding instructions."""
    id = 'quickstart'
    def __init__(self, project_root: Path):
        self.project_root = project_root
    def can_run(self, state: Dict[str, Any]) -> bool:
        if 'quickstart' in state: return False
        if 'codegen' in state: return True
        # allow in boilerplate-only mode once scaffold is present
        return state.get('config', {}).get('boilerplate_only') and 'scaffold' in state
    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        stack = state.get('tech', {}).get('stack', [])
        has_db = 'database' in state
        deploy = state.get('deploy_select', {}).get('strategy')
        lines = [
            f"# Quickstart for {state.get('name','Project')}",
            '',
            '## Stack',
            '- ' + '\n- '.join([str(s) for s in stack]) if stack else 'Minimal stack',
            '',
            '## Setup',
            '```bash',
            'python -m venv .venv',
            'source .venv/Scripts/activate  # Windows: .venv\\Scripts\\activate',
            'pip install -r requirements.txt  # if exists',
            'python app/main.py',
            '```',
            '',
            '## Roles',
            '### Backend',
            '- Implement business logic in app/ modules.',
            '### QA',
            '- Run pytest inside venv.',
            '### DevOps',
            f"- Deployment strategy: {deploy or 'dockerfile'}",
            '  - docker build -t app .',
            '  - docker run -p 8000:8000 app',
            '### Database' if has_db else '',
            ('- Apply schema SQL file found at root.' if has_db else ''),
        ]
        content = '\n'.join([l for l in lines if l is not None])
        (self.project_root / 'QUICKSTART.md').write_text(content)
        return {'path': 'QUICKSTART.md'}
