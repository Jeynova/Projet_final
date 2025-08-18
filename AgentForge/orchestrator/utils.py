import os, re, json, shutil, subprocess, sys
from pathlib import Path
from typing import Dict, Any, List
from jinja2 import Environment, FileSystemLoader, StrictUndefined

ROOT = Path(__file__).resolve().parents[1]
TEMPLATES = ROOT / "templates"
GENERATED = ROOT / "generated"

def ensure_dir(p: Path):
    p.mkdir(parents=True, exist_ok=True)

def render_dir(template_dir: Path, out_dir: Path, context: Dict[str, Any]):
    env = Environment(loader=FileSystemLoader(str(template_dir)), undefined=StrictUndefined, keep_trailing_newline=True)
    for root, _, files in os.walk(template_dir):
        rel = Path(root).relative_to(template_dir)
        for f in files:
            src = Path(root) / f
            # fichiers .j2 => rendu ; sinon copie brute
            if f.endswith(".j2"):
                dst = out_dir / rel / f[:-3]
                ensure_dir(dst.parent)
                tpl = env.get_template(str(rel / f).replace("\\", "/"))
                content = tpl.render(**context)
                dst.write_text(content, encoding="utf-8")
            else:
                dst = out_dir / rel / f
                ensure_dir(dst.parent)
                shutil.copyfile(src, dst)

def run_cmd(cmd: List[str], cwd: Path = None) -> int:
    print("> ", " ".join(cmd))
    proc = subprocess.Popen(cmd, cwd=str(cwd) if cwd else None)
    return proc.wait()

def write_json(p: Path, data: Dict[str, Any]):
    ensure_dir(p.parent)
    p.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
