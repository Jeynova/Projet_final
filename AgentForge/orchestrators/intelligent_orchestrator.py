# intelligent_orchestrator.py
"""
Intelligent Orchestrator
- Wires the agent pipeline
- Runs multi-pass loops until goal is reached or progress stalls
- Tracks best code snapshot
- Can persist generated projects to disk

Usage (programmatic):
    from intelligent_orchestrator import IntelligentOrchestrator, OrchestratorConfig
    orch = IntelligentOrchestrator()
    state = orch.run("Build a real-time chat application")
    out_dir = orch.materialize_project(state, project_name="chat-boilerplate")

CLI (minimal):
    python intelligent_orchestrator.py "Build a real-time chat application"
"""

from __future__ import annotations

import os
import sys
import json
import tempfile
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, List, Callable, Optional, Sequence, Tuple, Union

# Your agents package “barrel” (exported in agents/__init__.py)
from agents import load_default_pipeline

# -------------------------------
# Config & Logger
# -------------------------------

@dataclass
class OrchestratorConfig:
    max_outer_loops: int = 6                # passes over the pipeline
    validation_threshold: int = 7           # echoed into initial state
    max_codegen_iters: int = 4              # echoed into initial state
    file_contract_mode: str = "strict"      # 'free'|'guided'|'strict'
    stop_on_first_valid: bool = True        # short-circuit when >= threshold
    echo_state_keys: Tuple[str, ...] = (
        "prompt", "domain", "complexity", "performance_needs",
        "tech_stack", "contract", "validation", "goal_reached"
    )

def default_logger(msg: str) -> None:
    print(msg)

# -------------------------------
# Orchestrator
# -------------------------------

class IntelligentOrchestrator:
    def __init__(
        self,
        *,
        agents: Optional[Sequence[object]] = None,
        rag_store: Optional[object] = None,
        config: Optional[OrchestratorConfig] = None,
        logger: Optional[Callable[[str], None]] = None,
    ) -> None:
        self.config = config or OrchestratorConfig()
        self.log = logger or default_logger
        self.agents: List[object] = list(agents or load_default_pipeline(rag_store=rag_store))

        # Keep a handle to memory agent (if present) for learn_from_outcome
        self._memory_agent = next((a for a in self.agents if getattr(a, "id", None) == "memory"), None)

    # ---- Core API ------------------------------------------------------------

    def run(self, prompt: str, *, initial_state: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Run the multi-pass agent pipeline on a prompt.
        Returns the final state (including 'generated_code', 'validation', etc.).
        """
        state: Dict[str, Any] = {
            "prompt": prompt,
            "validation_threshold": self.config.validation_threshold,
            "max_codegen_iters": self.config.max_codegen_iters,
            "file_contract_mode": self.config.file_contract_mode,
            **(initial_state or {}),
        }

        self.log(f"🎭 PIPELINE START: {prompt[:80]}{'…' if len(prompt) > 80 else ''}")

        progress_made_any_pass = False

        for outer in range(1, self.config.max_outer_loops + 1):
            self.log(f"\n──────── Pass {outer}/{self.config.max_outer_loops} ────────")
            progress_this_pass = False

            for agent in self.agents:
                name = agent.__class__.__name__
                try:
                    can_run = bool(agent.can_run(state)) if hasattr(agent, "can_run") else True
                except Exception as e:
                    self.log(f"⏭️  {name}.can_run() errored → skipping: {e}")
                    continue

                if not can_run:
                    self.log(f"⏭️  Skipping {name} (conditions not met)")
                    continue

                self.log(f"🔄 Running {name}")
                try:
                    result = agent.run(state) if hasattr(agent, "run") else {}
                except Exception as e:
                    self.log(f"❌ {name}.run() failed: {e}")
                    continue

                if isinstance(result, dict) and result:
                    # Track whether something actually changed
                    before = json.dumps(_stable_keys(state), sort_keys=True)
                    state.update(result)
                    after = json.dumps(_stable_keys(state), sort_keys=True)
                    changed = (before != after)
                    progress_this_pass = progress_this_pass or changed

                    # Pretty echo of the most relevant deltas
                    self._echo_small_delta(name, result)

                # Early-out if quality goal reached and allowed to stop
                if state.get("goal_reached") and self.config.stop_on_first_valid:
                    self.log("✅ Goal reached → short-circuiting pipeline.")
                    break

            progress_made_any_pass = progress_made_any_pass or progress_this_pass

            # If we hit the goal, we can stop
            if state.get("goal_reached") and self.config.stop_on_first_valid:
                break

            # If nothing progressed in this pass, bail to avoid spinning
            if not progress_this_pass:
                self.log("🛑 No progress this pass → stopping.")
                break

        # Learning memory: reflect on the outcome if we have enough signal
        try:
            if self._memory_agent and "evaluation" in state and "tech_stack" in state:
                overall = state["evaluation"].get("overall_score", 5)
                self.log(f"\n🎓 LEARNING FROM OUTCOME ({overall}/10)")
                self._memory_agent.learn_from_outcome(prompt, state["tech_stack"], overall)
        except Exception as e:
            self.log(f"⚠️ learning failed: {e}")

        self.log("\n🎉 PIPELINE COMPLETE")
        return state

    # ---- Utilities -----------------------------------------------------------

    def materialize_project(
        self,
        state: Dict[str, Any],
        *,
        project_name: str = "generated_project",
        output_dir: Optional[Union[str, Path]] = None,
        prefer_best: bool = True,
    ) -> str:
        """
        Write files from 'generated_code' (or 'best_generated_code') to disk.
        Returns the folder path.
        """
        code_blob = None
        if prefer_best and state.get("best_generated_code", {}).get("files"):
            code_blob = state["best_generated_code"]
        else:
            code_blob = state.get("generated_code", {})

        files = (code_blob or {}).get("files", {})
        if not files:
            self.log("❌ No files to write (generated_code is empty).")
            return ""

        base_dir = Path(output_dir) if output_dir else Path(tempfile.mkdtemp())
        project_dir = base_dir / project_name
        project_dir.mkdir(parents=True, exist_ok=True)

        for rel_path, content in files.items():
            dest = project_dir / rel_path
            dest.parent.mkdir(parents=True, exist_ok=True)
            # normalize newlines for cross-platform friendliness
            text = content if isinstance(content, str) else str(content)
            dest.write_text(text, encoding="utf-8")

        self.log(f"💾 Project written to: {project_dir}")
        return str(project_dir)

    def _echo_small_delta(self, agent_name: str, result: Dict[str, Any]) -> None:
        keys = list(result.keys())
        preview_keys = ", ".join(keys[:6]) + ("…" if len(keys) > 6 else "")
        self.log(f"   ↳ {agent_name} updated: {preview_keys}")

# -------------------------------
# Helpers
# -------------------------------

def _stable_keys(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Make a light copy of state but keep only stable/simple keys to compare progress.
    This avoids huge diffs from full file contents.
    """
    keep = {}
    for k in ("tech_stack", "architecture", "contract", "validation", "codegen_iters",
              "last_validated_iter", "goal_reached", "redo_codegen", "redo_contract"):
        if k in state:
            keep[k] = state[k]
    return keep

# -------------------------------
# Minimal CLI
# -------------------------------

def _main(argv: List[str]) -> int:
    if len(argv) < 2:
        print("Usage: python intelligent_orchestrator.py \"<your project prompt>\"")
        return 2

    prompt = argv[1]
    orch = IntelligentOrchestrator()
    state = orch.run(prompt)

    # Optionally dump a quick summary
    summary = {
        "tech_stack": state.get("tech_stack"),
        "contract": state.get("contract"),
        "validation": state.get("validation"),
        "goal_reached": state.get("goal_reached"),
        "best_validation_score": state.get("best_validation_score"),
    }
    print("\n--- SUMMARY ---")
    print(json.dumps(summary, indent=2))

    # Write project to a temp dir so user can try it immediately
    out = orch.materialize_project(state, project_name="web-boilerplate")
    if out:
        print(f"\n📦 Files written to: {out}")
    return 0

if __name__ == "__main__":
    raise SystemExit(_main(sys.argv))