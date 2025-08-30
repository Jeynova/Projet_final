orchestrator_v2 Overview
========================

Goal: A truly agentic, adaptive project generation system with multi-layer memory (statistical + semantic RAG + artifact ingestion), dynamic agent selection, and incremental learning.

Key Components:
 - DynamicOrchestrator: Chooses next agent each step (no fixed pipeline).
 - Agents: memory, tech_select, architecture, codegen, database, infra, tests, ingest, evaluation, remediate.
 - MemoryStore: Tracks runs, agent stats, decisions + feedback-weighted success bonus.
 - RAGStore: Lightweight TF-IDF retrieval over ingested summaries & artifacts.
 - IngestAgent: Summarizes generated code and feeds back into RAG for future context.
 - EvaluationAgent: Heuristic + LLM rubric scoring (JSON output).
 - RemediationAgent: Suggests improvements when score < 65 and writes REMEDIATION_NOTES.md.
 - LLM Cache: Hash-based caching to reduce duplicate LLM calls.
 - Feedback Loop: Final score adjusts per-agent score_bonus influencing future selection.
 - Run Report: AGENT_RUN_REPORT.md summarizing each adaptive session.

Adaptive Logic:
 - Agent scoring = success_rate(agent) + feedback bonus + stage heuristic.
 - MemoryAgent provides similar past prompts + RAG context for grounding.
 - RAG context appended selectively to prompts for tech, architecture, codegen.
 - IngestAgent enriches retrieval corpus mid-run.
 - EvaluationAgent invokes LLM rubric (fallback to heuristic) for final score.
 - RemediationAgent runs post-evaluation (score < 65) to propose next-iteration actions.

Run Example:
```
python -m orchestrator_v2.dynamic_orchestrator --prompt "Create a simple blog API with authentication" --name blog-agentic --output ./generated
```

Data Files:
 - orchestrator_memory.json : persistent performance & decision memory.
 - rag_store.json           : semantic retrieval corpus.
 - llm_cache.json           : cached LLM JSON responses.

Extending:
 - Add new agent: implement can_run + run, append to `self.agents` in `dynamic_orchestrator.py`.
 - Add richer evaluation: replace heuristic in `EvaluationAgent` with LLM rubric.
 - Plug vector embeddings: swap RAGStore with external vector DB (preserve interface).

Implemented Enhancements (this branch):
 - RAG-backed context injection
 - Artifact ingestion loop
 - LLM response caching
 - Multi-factor adaptive agent selection
 - Feedback-weighted learning (apply_feedback)
 - LLM rubric evaluation
 - RemediationAgent (low-score suggestions)
 - Run report generation (AGENT_RUN_REPORT.md)

Future Ideas (Not Yet Implemented):
 - Confidence-based early stop & replan
 - Active patch application (auto code improvements) based on remediation
 - Parallel agent speculative execution
 - Embedding-based semantic RAG (swap TF-IDF)

Limitations:
 - Remediation suggestions not yet auto-applied.
 - Current retrieval is bag-of-words (upgrade path: embeddings).
 - Single-threaded; no speculative parallelism.
 - Feedback weighting simple (could decay over time).

License: Inherits root project license.
