"""Simple persistent memory / knowledge base for orchestrator_v2.
Stores:
  - past_runs: list of {prompt, tech_stack, artifacts, success_score}
  - agent_stats: {agent_id: {invocations, successes, failures}}
  - decisions: list of {state_hash, chosen_agent, outcome, timestamp}

Learning is lightweight: success rate influences future agent priority.
"""
from __future__ import annotations
import json, time, hashlib
from pathlib import Path
from typing import Any, Dict, List, Optional

DEFAULT_FILE = Path(__file__).parent / "orchestrator_memory.json"

class MemoryStore:
    def __init__(self, path: Optional[Path] = None):
        # Path to JSON persistence file
        self.path = path or DEFAULT_FILE
        # In-memory structure
        self.data: Dict[str, Any] = {
            "past_runs": [],
            "agent_stats": {},
            "decisions": []
        }
        self._loaded = False
        self.load()

    def load(self):
        if self.path.exists():
            try:
                self.data = json.loads(self.path.read_text())
                self._loaded = True
            except Exception:
                self._loaded = False
        return self

    def save(self):
        try:
            self.path.write_text(json.dumps(self.data, indent=2))
        except Exception:
            pass

    # ---- Recording ----
    def record_run(self, prompt: str, tech_stack: List[str], artifacts: List[str], score: float):
        self.data.setdefault("past_runs", []).append({
            "prompt": prompt,
            "tech_stack": tech_stack,
            "artifacts": artifacts,
            "score": score,
            "time": time.time()
        })
        self.save()

    def record_agent_invocation(self, agent_id: str, success: bool):
        stats = self.data.setdefault("agent_stats", {}).setdefault(agent_id, {"invocations": 0, "successes": 0, "failures": 0})
        stats["invocations"] += 1
        if success:
            stats["successes"] += 1
        else:
            stats["failures"] += 1
        self.save()

    def record_decision(self, state: Dict[str, Any], chosen_agent: str, outcome: str):
        state_hash = hashlib.sha256(json.dumps(state, sort_keys=True)[:512].encode()).hexdigest()[:16]
        self.data.setdefault("decisions", []).append({
            "state_hash": state_hash,
            "chosen_agent": chosen_agent,
            "outcome": outcome,
            "time": time.time()
        })
        self.save()

    # ---- Query ----
    def success_rate(self, agent_id: str) -> float:
        stats = self.data.get("agent_stats", {}).get(agent_id)
        if not stats:
            # Start with modest neutral prior instead of 0.5 to let feedback raise it
            return 0.3
        inv = max(1, stats.get("invocations", 0))
        base = stats.get("successes", 0) / inv
        bonus = stats.get("score_bonus", 0.0)
        # score_bonus is in [ -1, +1 ] aggregated; scale lightly
        adjusted = base + 0.2 * bonus
        return max(0.1, min(1.0, adjusted))

    # ---- Feedback weighting ----
    def apply_feedback(self, agents: list[str], final_score: float, baseline: float = 50.0):
        """Adjust agent score_bonus based on how final score compares to baseline.

        Simple scheme: delta = (final_score - baseline)/baseline clamped [-1,1].
        Distribute delta equally across participating agents' score_bonus.
        """
        if not agents:
            return
        delta = 0.0
        if baseline > 0:
            delta = (final_score - baseline)/baseline
        delta = max(-1.0, min(1.0, delta))
        share = delta / len(agents)
        for a in agents:
            stats = self.data.setdefault("agent_stats", {}).setdefault(a, {"invocations":0,"successes":0,"failures":0})
            current = stats.get("score_bonus", 0.0)
            # Exponential decay toward zero each feedback application
            current *= 0.9
            stats["score_bonus"] = max(-1.0, min(1.0, current + share))
        self.save()

    def similar_prompts(self, prompt: str, top_k: int = 3) -> List[Dict[str, Any]]:
        def jacc(a, b):
            sa, sb = set(a.lower().split()), set(b.lower().split())
            if not sa or not sb: return 0.0
            return len(sa & sb) / len(sa | sb)
        scored = []
        for r in self.data.get("past_runs", []):
            scored.append((jacc(prompt, r.get("prompt", "")), r))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [r for _, r in scored[:top_k]]

    def dump_summary(self) -> Dict[str, Any]:
        return {
            "agents": self.data.get("agent_stats", {}),
            "runs": len(self.data.get("past_runs", [])),
            "decisions": len(self.data.get("decisions", []))
        }
