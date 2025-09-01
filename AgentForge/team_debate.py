# team_debate.py
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, Any, List, Callable

def llm_json(client, system_prompt, user_prompt, fallback):
    try:
        return client.extract_json(system_prompt, user_prompt) or fallback
    except Exception:
        return fallback

ROLES = {
    "PM": "You are a Project Manager focused on timeline, budget, and risk.",
    "DEV": "You are a Lead Developer focused on implementation, maintainability, and performance.",
    "PO": "You are a Product Owner focused on UX, features, and roadmap.",
    "CONSULTANT": "You are a Technology Consultant focused on industry best practices and tradeoffs.",
    "USER": "You are the end user focused on usability and perceived speed."
}

def run_debate(llm_client, prompt: str, context: str, timeout_s: int = 60) -> List[Dict[str, Any]]:
    qs = []
    for role, sys_prompt in ROLES.items():
        user = f"""Project: {prompt}

Context:
{context}

As {role}, propose a concrete stack (backend, frontend, database, deployment) and justify."""
        qs.append((role, sys_prompt, user))

    results = []
    with ThreadPoolExecutor(max_workers=len(qs)) as ex:
        futs = [ex.submit(llm_json, llm_client, sys, usr, {}) for (_, sys, usr) in qs]
        for fut, (role, _, _) in zip(futs, qs):
            try:
                out = fut.result(timeout=timeout_s)
            except Exception:
                out = {}
            results.append({"role": role, "proposal": out})
    return results

def moderate(llm_client, prompt: str, debate: List[Dict[str, Any]]):
    sys = """You are a neutral moderator. Combine role proposals into ONE coherent stack:
Return JSON:
{
  "backend": {"name": "...", "reasoning": "..."},
  "frontend": {"name": "...", "reasoning": "..."},
  "database": {"name": "...", "reasoning": "..."},
  "deployment": {"name": "...", "reasoning": "..."},
  "team_discussion": "concise synthesis of points and tradeoffs"
}"""
    bullets = []
    for d in debate:
        bullets.append(f"- {d['role']}: {d['proposal']}")
    user = f"Project: {prompt}\n\nProposals:\n" + "\n".join(bullets)
    fallback = {
        "backend": {"name":"Express.js","reasoning":"Consensus default"},
        "frontend": {"name":"React","reasoning":"Consensus default"},
        "database": {"name":"PostgreSQL","reasoning":"Reliable"},
        "deployment":{"name":"Docker + Cloud","reasoning":"Standard"},
        "team_discussion":"Default synthesis"
    }
    return llm_json(llm_client, sys, user, fallback)
