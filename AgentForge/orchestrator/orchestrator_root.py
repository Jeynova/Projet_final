from pathlib import Path

def get_repo_root() -> Path:
    """Retourne la racine du repo (Projet_final/AgentForge)"""
    return Path(__file__).resolve().parents[1]
