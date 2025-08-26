"""Tests unitaires pour la normalisation et le mapping des choix LLM"""

from orchestrator.tech_selector_smol import _map_choice, _norm

def test_norm():
    """Test de la normalisation des chaînes"""
    assert _norm("Docker Compose") == "docker_compose"
    assert _norm("GitHub-Actions") == "github_actions"
    assert _norm("  PostgreSQL  ") == "postgresql"
    assert _norm("K8s/Kubernetes") == "k8s_kubernetes"
    assert _norm("FastAPI") == "fastapi"

def test_map_web_alias():
    """Test des alias pour frameworks web"""
    assert _map_choice("web","Django") == "fastapi"
    assert _map_choice("web","Starlette") == "fastapi"
    assert _map_choice("web","Flask") == "flask"
    assert _map_choice("web","Quart") == "flask"
    assert _map_choice("web","Tornado") == "fastapi"
    # Choix valides déjà
    assert _map_choice("web","fastapi") == "fastapi"
    assert _map_choice("web","flask") == "flask"
    # Choix inconnu -> fallback
    assert _map_choice("web","unknown_framework") == "fastapi"

def test_map_db_alias():
    """Test des alias pour bases de données"""
    assert _map_choice("db","postgresql") == "postgres"
    assert _map_choice("db","PostgreSQL") == "postgres"
    assert _map_choice("db","mysql") == "postgres"
    assert _map_choice("db","MongoDB") == "sqlite"
    assert _map_choice("db","redis") == "sqlite"
    assert _map_choice("db","clickhouse") == "postgres"
    # Choix valides
    assert _map_choice("db","postgres") == "postgres"
    assert _map_choice("db","sqlite") == "sqlite"
    # Choix inconnu -> fallback
    assert _map_choice("db","unknown_db") == "postgres"

def test_map_infra_alias():
    """Test des alias pour infrastructure"""
    assert _map_choice("infra","docker compose") == "docker_compose"
    assert _map_choice("infra","Docker-Compose") == "docker_compose"
    assert _map_choice("infra","kubernetes") == "k8s"
    assert _map_choice("infra","Kubernetes") == "k8s"
    assert _map_choice("infra","docker swarm") == "docker_compose"
    assert _map_choice("infra","bare metal") == "docker_compose"
    assert _map_choice("infra","nomad") == "k8s"
    # Choix valides
    assert _map_choice("infra","docker_compose") == "docker_compose"
    assert _map_choice("infra","k8s") == "k8s"
    # Choix inconnu -> fallback
    assert _map_choice("infra","unknown_infra") == "docker_compose"

def test_map_ci_alias():
    """Test des alias pour CI/CD"""
    assert _map_choice("ci","gitlab ci") == "github_actions"
    assert _map_choice("ci","GitLab CI") == "github_actions"
    assert _map_choice("ci","jenkins") == "github_actions"
    assert _map_choice("ci","circleci") == "github_actions"
    assert _map_choice("ci","azure pipelines") == "github_actions"
    # Choix valides
    assert _map_choice("ci","github_actions") == "github_actions"
    assert _map_choice("ci","none") == "none"
    # Choix inconnu -> fallback
    assert _map_choice("ci","unknown_ci") == "github_actions"

def test_edge_cases():
    """Test des cas limites"""
    # Valeurs vides/nulles
    assert _map_choice("web", "") == "fastapi"
    assert _map_choice("web", None) == "fastapi"
    assert _map_choice("db", " ") == "postgres"
    
    # Espaces et caractères spéciaux
    assert _map_choice("web", "  Django  ") == "fastapi"
    assert _map_choice("infra", "Docker/Compose") == "docker_compose"

if __name__ == "__main__":
    # Tests rapides
    print("Running tests...")
    test_norm()
    test_map_web_alias()
    test_map_db_alias()
    test_map_infra_alias()  
    test_map_ci_alias()
    test_edge_cases()
    print("✅ All tests passed!")
