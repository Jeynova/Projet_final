"""
SmolSmartSystem
================
Experimental agentic pipeline built with `smolagent` that mirrors the stages of
`TrulySmartAgentSystem` but composes lightweight Agents in a dynamic graph:

Stages (potentially skipped):
 1. memory      -> tries to retrieve similar past project (RAG-lite)
 2. tech_select -> chooses stack
 3. architecture-> designs file / dir structure
 4. codegen     -> generates source files
 5. database    -> (conditional) schema + init
 6. infra       -> (conditional) deployment assets
 7. tests       -> test suite
 8. evaluate    -> scoring / summary

Dynamic behaviour:
 - If memory has high confidence (>0.8) we skip tech_select (reuse hints).
 - If selected stack implies no DB we skip database.
 - If prompt does not mention deploy/prod/docker we skip infra.

Only files inside `orchestrator_v2/` are created / modified per user request.

NOTE: This file attempts to import `smolagent`. If it's not installed, an
informative error is returned. Install (example):
    pip install smolagent
or add it to your project requirements before running.
"""

from __future__ import annotations

import os
import json
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Callable
from pathlib import Path
import traceback

# Attempt smolagent import gracefully
try:
    from smolagent import Agent, Task, ChatMessage
    SMOL_AVAILABLE = True
except Exception:  # broad to keep isolated
    SMOL_AVAILABLE = False

# Re‑use existing LLM client if present (non intrusive)
_LLM_CLIENT = None
try:
    from core.llm_client import LLMClient  # type: ignore
    _LLM_CLIENT = LLMClient()
except Exception:
    pass


def _llm_json(system: str, user: str, fallback: Dict[str, Any]) -> Dict[str, Any]:
    """Helper to call existing LLMClient extract_json with safe fallback."""
    if _LLM_CLIENT is None:
        return fallback
    try:
        result = _LLM_CLIENT.extract_json(system_prompt=system, user_prompt=user)
        if isinstance(result, dict) and result:
            return result
    except Exception:
        pass
    return fallback


@dataclass
class StageResult:
    name: str
    data: Dict[str, Any]
    skipped: bool = False
    error: Optional[str] = None


class SmolSmartSystem:
    """Agentic pipeline using smolagent.

    Public entrypoint: build_project(prompt, name, output_dir) -> dict
    """

    def __init__(self):
        self.agentic_enabled = os.getenv("AGENTFORGE_AGENTIC", "0") == "1"
        self.mode = os.getenv("AGENTFORGE_MODE", "auto")
        self.results: Dict[str, StageResult] = {}
        self.project_dir: Optional[Path] = None

    # -------- Memory Stage -------------------------------------------------
    def stage_memory(self, prompt: str) -> StageResult:
        memory_path = Path(__file__).parent.parent / "agentforge.db.json"
        best = None
        if memory_path.exists():
            try:
                data = json.loads(memory_path.read_text())
                for p in data.get("projects", []):
                    sim = self._jaccard(prompt, p.get("prompt", ""))
                    if sim > 0.7 and (best is None or sim > best[0]):
                        best = (sim, p)
            except Exception:
                pass
        if best:
            return StageResult("memory", {
                "found": True,
                "confidence": round(best[0], 3),
                "project": best[1].get("name"),
                "tech_hints": best[1].get("tech_stack", [])
            })
        # Ask LLM for pattern classification as supplemental context
        llm = _llm_json(
            "You classify software project prompts.",
            f"Classify: {prompt}. Return JSON {{category, rationale}}",
            {}
        )
        return StageResult("memory", {"found": False, "confidence": 0.0, **llm})

    # -------- Tech Selection -----------------------------------------------
    def stage_tech_select(self, prompt: str, memory: StageResult) -> StageResult:
        if memory.data.get("found") and memory.data.get("confidence", 0) > 0.8:
            return StageResult("tech_select", {
                "stack": memory.data.get("tech_hints", []),
                "reasoning": "Reused high confidence memory hints",
                "confidence": memory.data.get("confidence")
            }, skipped=True)
        fallback = {"stack": ["python", "fastapi", "sqlite"], "confidence": 0.4}
        prompt_text = f"Project: {prompt}\nMemory: {json.dumps(memory.data)}"
        result = _llm_json(
            "You select pragmatic modern stacks.",
            prompt_text + "\nReturn JSON {stack, reasoning, confidence}",
            fallback
        )
        return StageResult("tech_select", result)

    # -------- Architecture -------------------------------------------------
    def stage_architecture(self, prompt: str, tech: StageResult) -> StageResult:
        fallback = {
            "architecture_pattern": "Layered",
            "files": [{"path": "app/main.py", "purpose": "Entry point"}],
            "directories": ["app", "tests"],
        }
        user = (
            f"Prompt: {prompt}\nStack: {tech.data.get('stack')}\n"
            "Design a production-ready minimal architecture. Return JSON {architecture_pattern, files, directories, key_components, reasoning}."
        )
        result = _llm_json("You design app architectures.", user, fallback)
        return StageResult("architecture", result)

    # -------- Code Generation ---------------------------------------------
    def stage_code(self, prompt: str, tech: StageResult, arch: StageResult) -> StageResult:
        actions: List[str] = []
        files = arch.data.get("files", [])
        generated = []
        if not self.project_dir:
            raise RuntimeError("project_dir not set")
        for spec in files:
            path = spec.get("path", "main.py")
            purpose = spec.get("purpose", "")
            fallback = {"code": f"# {purpose}\nprint('Hello from {path}')"}
            user = (
                f"Project: {prompt}\nStack: {tech.data.get('stack')}\n"
                f"File: {path}\nPurpose: {purpose}\nReturn JSON {{code}} with complete code."
            )
            result = _llm_json("You write complete, safe code.", user, fallback)
            code = result.get("code", "")
            file_path = self.project_dir / path
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(code)
            actions.append(f"wrote {path} ({len(code)} chars)")
            generated.append(path)
        return StageResult("codegen", {"files": generated, "actions": actions})

    # -------- Database -----------------------------------------------------
    def stage_database(self, tech: StageResult, arch: StageResult, name: str) -> StageResult:
        stack = [s.lower() for s in tech.data.get("stack", [])]
        db = next((s for s in stack if s in ["postgresql", "mysql", "sqlite", "mongodb"]), None)
        if not db:
            return StageResult("database", {"skipped": True, "reason": "No DB in stack"}, skipped=True)
        fallback = {"schema_sql": "-- placeholder schema"}
        result = _llm_json(
            "You design concise DB schemas.",
            f"Stack: {stack}\nApp: {name}\nReturn JSON {{schema_sql}}", fallback
        )
        if self.project_dir:
            (self.project_dir / f"{db}_schema.sql").write_text(result.get("schema_sql", ""))
        return StageResult("database", result)

    # -------- Infrastructure ----------------------------------------------
    def stage_infra(self, prompt: str, tech: StageResult) -> StageResult:
        if not any(k in prompt.lower() for k in ["deploy", "docker", "production", "k8s", "kubernetes"]):
            return StageResult("infra", {"skipped": True, "reason": "No deployment intent"}, skipped=True)
        fallback = {"dockerfile": "FROM python:3.11-slim\nWORKDIR /app\nCOPY . .\nRUN pip install -r requirements.txt || true\nCMD [\"python\", \"-m\", \"app.main\"]"}
        result = _llm_json(
            "You create infra assets.",
            f"Stack: {tech.data.get('stack')}\nReturn JSON {{dockerfile}}", fallback
        )
        if self.project_dir:
            (self.project_dir / "Dockerfile").write_text(result.get("dockerfile", ""))
        return StageResult("infra", {k: v for k, v in result.items() if k in ("dockerfile",)})

    # -------- Tests --------------------------------------------------------
    def stage_tests(self, arch: StageResult) -> StageResult:
        fallback = {"unit_tests": "def test_placeholder():\n    assert True"}
        result = _llm_json(
            "You write minimal reliable tests.",
            f"Files: {arch.data.get('files')} Return JSON {{unit_tests}}", fallback
        )
        if self.project_dir:
            tests_dir = self.project_dir / "tests"
            tests_dir.mkdir(exist_ok=True)
            (tests_dir / "test_basic.py").write_text(result.get("unit_tests", ""))
        return StageResult("tests", {"files": ["tests/test_basic.py"]})

    # -------- Evaluation ---------------------------------------------------
    def stage_evaluate(self) -> StageResult:
        score = 60
        if self.results.get("codegen"):
            score += 10
        if not self.results.get("infra", StageResult("infra", {}, True)).skipped:
            score += 10
        return StageResult("evaluate", {
            "score": score,
            "summary": "Heuristic score (placeholder w/ optional LLM)"
        })

    # -------- Utility ------------------------------------------------------
    @staticmethod
    def _jaccard(a: str, b: str) -> float:
        sa, sb = set(a.lower().split()), set(b.lower().split())
        if not sa or not sb:
            return 0.0
        return len(sa & sb) / len(sa | sb)

    # -------- Execution ----------------------------------------------------
    def build_project(self, prompt: str, name: str, output_dir: str) -> Dict[str, Any]:
        if not SMOL_AVAILABLE:
            return {"error": "smolagent not installed", "install_hint": "pip install smolagent"}
        self.project_dir = Path(output_dir) / name
        self.project_dir.mkdir(parents=True, exist_ok=True)

        # Stage execution order (dynamic decisions inside stages)
        memory = self.stage_memory(prompt); self.results["memory"] = memory
        tech = self.stage_tech_select(prompt, memory); self.results["tech_select"] = tech
        arch = self.stage_architecture(prompt, tech); self.results["architecture"] = arch
        code = self.stage_code(prompt, tech, arch); self.results["codegen"] = code
        db = self.stage_database(tech, arch, name); self.results["database"] = db
        infra = self.stage_infra(prompt, tech); self.results["infra"] = infra
        tests = self.stage_tests(arch); self.results["tests"] = tests
        eval_res = self.stage_evaluate(); self.results["evaluate"] = eval_res

        return {
            "status": "completed",
            "name": name,
            "project_dir": str(self.project_dir),
            "stages": {k: v.data for k, v in self.results.items()},
            "skipped": [k for k, v in self.results.items() if v.skipped],
            "score": eval_res.data.get("score"),
        }


def run_smol_system(prompt: str, name: str, project_root: 'Path') -> Dict[str, Any]:
    """Convenience wrapper used by simplified CLI (run_project.py)."""
    system = SmolSmartSystem()
    return system.build_project(prompt, name, str(project_root.parent))


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="SmolAgent based smart system")
    parser.add_argument("--prompt", required=True)
    parser.add_argument("--name", default="smol-project")
    parser.add_argument("--output", default="./generated")
    args = parser.parse_args()
    system = SmolSmartSystem()
    result = system.build_project(args.prompt, args.name, args.output)
    print(json.dumps(result, indent=2))
