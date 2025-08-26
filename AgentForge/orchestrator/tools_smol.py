from smolagents import Tool
from pathlib import Path
import subprocess, shlex

ALLOWED_PREFIXES = ("src/", "tests/", "alembic/", ".github/", "Dockerfile", "docker-compose.yml")

def _is_allowed(path: str) -> bool:
    return path.startswith(ALLOWED_PREFIXES)

class RetrieveSnippetsTool(Tool):
    name = "retrieve_snippets"
    description = "Charge des snippets RAG (markdown) contenant certains tags."
    inputs = {"tags": {"type": "string", "description": "tags séparés par des virgules"}}
    output_type = "string"
    def __init__(self, repo_root: Path):
        super().__init__()
        self.repo_root = repo_root
    def forward(self, tags: str) -> str:
        tags_list = [t.strip().lower() for t in tags.split(",") if t.strip()]
        acc = []
        for p in (self.repo_root / "rag_snippets").glob("*.md"):
            txt = p.read_text(encoding="utf-8")
            low = txt.lower()
            if any(t in low for t in tags_list):
                acc.append(f"\n--- {p.name} ---\n{txt}\n")
            if len(acc) >= 6:
                break
        return "\n".join(acc) if acc else "NO_SNIPPETS"

class ReadFileTool(Tool):
    name = "read_file"
    description = "Lit un fichier du projet (read-only)."
    inputs = {"path": {"type": "string", "description": "chemin relatif"}}
    output_type = "string"
    def __init__(self, project_dir: Path):
        super().__init__()
        self.project_dir = project_dir
    def forward(self, path: str) -> str:
        p = (self.project_dir / path).resolve()
        if not str(p).startswith(str(self.project_dir.resolve())):
            return "FORBIDDEN_PATH"
        if not p.exists(): return "NOT_FOUND"
        return p.read_text(encoding="utf-8")

class WriteFileTool(Tool):
    name = "write_file"
    description = "Écrit un fichier sous src/, tests/, alembic/, .github/, Dockerfile*, docker-compose.yml."
    inputs = {"path": {"type": "string"}, "content": {"type": "string"}}
    output_type = "string"
    def __init__(self, project_dir: Path):
        super().__init__(); self.project_dir = project_dir
    def forward(self, path: str, content: str) -> str:
        if not _is_allowed(path): return "FORBIDDEN_PATH"
        p = (self.project_dir / path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
        return f"WROTE:{path}"

class RunPytestTool(Tool):
    name = "run_pytest"
    description = "Lance pytest et retourne un résumé."
    inputs = {}; output_type = "string"
    def __init__(self, project_dir: Path):
        super().__init__(); self.project_dir = project_dir
    def forward(self) -> str:
        try:
            proc = subprocess.run(["python","-m","pytest","-q"], cwd=self.project_dir,
                                  capture_output=True, text=True, timeout=180)
            out = (proc.stdout or "") + "\n" + (proc.stderr or "")
            return f"PYTEST_EXIT={proc.returncode}\n{out[-2000:]}"
        except Exception as e:
            return f"PYTEST_ERROR:{e}"

class RunRuffTool(Tool):
    name = "run_ruff"; description = "Lance ruff sur src"; inputs = {}; output_type = "string"
    def __init__(self, project_dir: Path):
        super().__init__(); self.project_dir = project_dir
    def forward(self) -> str:
        try:
            proc = subprocess.run(["python","-m","ruff","src"], cwd=self.project_dir,
                                  capture_output=True, text=True, timeout=120)
            out = (proc.stdout or "") + "\n" + (proc.stderr or "")
            return f"RUFF_EXIT={proc.returncode}\n{out[-2000:]}"
        except Exception as e:
            return f"RUFF_ERROR:{e}"

class RunBanditTool(Tool):
    name = "run_bandit"; description = "Lance bandit sur src"; inputs = {}; output_type = "string"
    def __init__(self, project_dir: Path):
        super().__init__(); self.project_dir = project_dir
    def forward(self) -> str:
        try:
            proc = subprocess.run(shlex.split("python -m bandit -r src -q"),
                                  cwd=self.project_dir, capture_output=True, text=True, timeout=120)
            out = (proc.stdout or "") + "\n" + (proc.stderr or "")
            return f"BANDIT_EXIT={proc.returncode}\n{out[-2000:]}"
        except Exception as e:
            return f"BANDIT_ERROR:{e}"
