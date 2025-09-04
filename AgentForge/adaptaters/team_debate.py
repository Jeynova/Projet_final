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

def run_debate(llm_client, prompt: str, context: str, timeout_s: int = 60, demo_mode: bool = False) -> List[Dict[str, Any]]:
    """
    Run team debate with optional demo mode for faster processing
    demo_mode: if True, uses a single LLM call instead of parallel team simulation
    """
    if demo_mode:
        return run_demo_debate(llm_client, prompt, context)
    
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

def run_demo_debate(llm_client, prompt: str, context: str) -> List[Dict[str, Any]]:
    """Fast demo mode - single LLM call simulating entire team debate"""
    print("🎭 DEMO MODE: Simulation accélérée de l'équipe technique")
    
    demo_prompt = f"""Tu es une équipe technique complète analysant un projet. Simule les 5 rôles suivants:

PROJET: {prompt}
CONTEXTE: {context}

Pour chaque rôle, propose une stack technique (backend, frontend, database, deployment):

1. PROJECT MANAGER (PM): Focus sur timeline, budget, risques
2. LEAD DEVELOPER (DEV): Focus sur implémentation, maintenabilité, performance  
3. PRODUCT OWNER (PO): Focus sur UX, fonctionnalités, roadmap
4. CONSULTANT TECH: Focus sur best practices, trade-offs
5. END USER: Focus sur facilité d'usage, vitesse perçue

Réponds en JSON avec cette structure:
{{
  "PM": {{"stack": {{"backend": "...", "frontend": "...", "database": "...", "deployment": "..."}}, "reasoning": "..."}},
  "DEV": {{"stack": {{"backend": "...", "frontend": "...", "database": "...", "deployment": "..."}}, "reasoning": "..."}},
  "PO": {{"stack": {{"backend": "...", "frontend": "...", "database": "...", "deployment": "..."}}, "reasoning": "..."}},
  "CONSULTANT": {{"stack": {{"backend": "...", "frontend": "...", "database": "...", "deployment": "..."}}, "reasoning": "..."}},
  "USER": {{"stack": {{"backend": "...", "frontend": "...", "database": "...", "deployment": "..."}}, "reasoning": "..."}}
}}"""

    try:
        team_responses = llm_client.extract_json("Tu es une équipe technique experte", demo_prompt)
        
        if isinstance(team_responses, dict):
            results = []
            for role in ["PM", "DEV", "PO", "CONSULTANT", "USER"]:
                if role in team_responses:
                    results.append({
                        "role": role,
                        "proposal": team_responses[role].get("stack", {}),
                        "reasoning": team_responses[role].get("reasoning", "")
                    })
                else:
                    # Fallback si un rôle manque
                    results.append({
                        "role": role,
                        "proposal": {
                            "backend": "Node.js",
                            "frontend": "React",
                            "database": "PostgreSQL",
                            "deployment": "Docker"
                        },
                        "reasoning": "Choix par défaut"
                    })
            return results
    except Exception as e:
        print(f"⚠️ Demo mode failed: {e}")
    
    # Fallback vers débat standard
    return run_debate(llm_client, prompt, context, 60, demo_mode=False)

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
