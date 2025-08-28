"""
Smolagents tools for agentic workflow.
Secure, whitelisted operations only.
"""
from smolagents import Tool
from pathlib import Path
import subprocess
import shlex

# Security: only allow writing to these paths
ALLOWED_PREFIXES = (
    "src/", 
    "tests/", 
    "alembic/", 
    ".github/", 
    "Dockerfile", 
    "docker-compose.yml"
)

def _is_allowed(path: str) -> bool:
    """Check if file path is allowed for write operations."""
    return path.startswith(ALLOWED_PREFIXES)

class RetrieveSnippetsTool(Tool):
    """Retrieve RAG snippets based on tags."""
    name = "retrieve_snippets"
    description = "Load RAG snippets (markdown) containing certain tags."
    inputs = {
        "tags": {
            "type": "string", 
            "description": "comma-separated tags"
        }
    }
    output_type = "string"
    
    def __init__(self, repo_root: Path):
        super().__init__()
        self.repo_root = repo_root
    
    def forward(self, tags: str) -> str:
        tags_list = [t.strip().lower() for t in tags.split(",") if t.strip()]
        acc = []
        rag_dir = self.repo_root / "rag_snippets"
        
        if not rag_dir.exists():
            return "NO_RAG_DIR"
            
        for p in rag_dir.glob("*.md"):
            try:
                txt = p.read_text(encoding="utf-8")
                low = txt.lower()
                if any(t in low for t in tags_list):
                    acc.append(f"\n--- {p.name} ---\n{txt}\n")
                if len(acc) >= 6:  # Limit results
                    break
            except Exception:
                continue
                
        return "\n".join(acc) if acc else "NO_SNIPPETS"

class ReadFileTool(Tool):
    """Read project files (read-only)."""
    name = "read_file"
    description = "Read a project file (read-only access)."
    inputs = {
        "path": {
            "type": "string", 
            "description": "relative file path"
        }
    }
    output_type = "string"
    
    def __init__(self, project_dir: Path):
        super().__init__()
        self.project_dir = project_dir
    
    def forward(self, path: str) -> str:
        try:
            p = (self.project_dir / path).resolve()
            # Security: prevent path traversal
            if not str(p).startswith(str(self.project_dir.resolve())):
                return "FORBIDDEN_PATH"
            if not p.exists():
                return "NOT_FOUND"
            return p.read_text(encoding="utf-8")
        except Exception as e:
            return f"READ_ERROR:{e}"

class WriteFileTool(Tool):
    """Write files to allowed paths only."""
    name = "write_file"
    description = "Write file to allowed paths: src/, tests/, alembic/, .github/, Dockerfile*, docker-compose.yml"
    inputs = {
        "path": {"type": "string", "description": "relative file path"},
        "content": {"type": "string", "description": "file content"}
    }
    output_type = "string"
    
    def __init__(self, project_dir: Path):
        super().__init__()
        self.project_dir = project_dir
    
    def forward(self, path: str, content: str) -> str:
        if not _is_allowed(path):
            return f"FORBIDDEN_PATH: {path}"
            
        try:
            p = self.project_dir / path
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(content, encoding="utf-8")
            return f"WROTE:{path}"
        except Exception as e:
            return f"WRITE_ERROR:{e}"

class RunPytestTool(Tool):
    """Run pytest and return summary."""
    name = "run_pytest"
    description = "Run pytest and return execution summary."
    inputs = {}
    output_type = "string"
    
    def __init__(self, project_dir: Path):
        super().__init__()
        self.project_dir = project_dir
    
    def forward(self) -> str:
        try:
            proc = subprocess.run(
                ["python", "-m", "pytest", "-q"],
                cwd=self.project_dir,
                capture_output=True,
                text=True,
                timeout=180
            )
            out = (proc.stdout or "") + "\n" + (proc.stderr or "")
            return f"PYTEST_EXIT={proc.returncode}\n{out[-2000:]}"
        except subprocess.TimeoutExpired:
            return "PYTEST_TIMEOUT"
        except Exception as e:
            return f"PYTEST_ERROR:{e}"

class RunRuffTool(Tool):
    """Run ruff linter on src/."""
    name = "run_ruff"
    description = "Run ruff linter on src directory."
    inputs = {}
    output_type = "string"
    
    def __init__(self, project_dir: Path):
        super().__init__()
        self.project_dir = project_dir
    
    def forward(self) -> str:
        try:
            proc = subprocess.run(
                ["python", "-m", "ruff", "src"],
                cwd=self.project_dir,
                capture_output=True,
                text=True,
                timeout=120
            )
            out = (proc.stdout or "") + "\n" + (proc.stderr or "")
            return f"RUFF_EXIT={proc.returncode}\n{out[-2000:]}"
        except subprocess.TimeoutExpired:
            return "RUFF_TIMEOUT"
        except Exception as e:
            return f"RUFF_ERROR:{e}"

class RunBanditTool(Tool):
    """Run bandit security scanner on src/."""
    name = "run_bandit"
    description = "Run bandit security scanner on src directory."
    inputs = {}
    output_type = "string"
    
    def __init__(self, project_dir: Path):
        super().__init__()
        self.project_dir = project_dir
    
    def forward(self) -> str:
        try:
            proc = subprocess.run(
                shlex.split("python -m bandit -r src -q"),
                cwd=self.project_dir,
                capture_output=True,
                text=True,
                timeout=120
            )
            out = (proc.stdout or "") + "\n" + (proc.stderr or "")
            return f"BANDIT_EXIT={proc.returncode}\n{out[-2000:]}"
        except subprocess.TimeoutExpired:
            return "BANDIT_TIMEOUT"
        except Exception as e:
            return f"BANDIT_ERROR:{e}"
