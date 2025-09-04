"""
Infrastructure Agent - Generates deployment configurations
Creates Docker, Kubernetes, Helm charts and other infrastructure code
"""

import os
import yaml
from typing import Dict, Any, List, Optional
from pathlib import Path
from dataclasses import dataclass

from core.llm_client import LLMClient


@dataclass
class InfraConfig:
    """Infrastructure configuration"""
    deployment_type: str  # "docker", "k8s", "helm"
    environment: str     # "dev", "staging", "prod"
    config: Dict[str, Any]


class InfraAgent:
    """
    Generates infrastructure and deployment configurations
    - Creates Dockerfiles for containerization
    - Generates Kubernetes manifests
    - Creates Helm charts for complex deployments
    - Generates docker-compose for local development
    """
    
    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client
    
    def generate_infrastructure(self, project_dir: Path, spec: Dict[str, Any],
                              tech_stack: List[str]) -> Dict[str, Any]:
        """Generate appropriate infrastructure configurations"""
        
        infra_configs = []
        
        # Determine what infrastructure to generate based on requirements
        needs = self._analyze_infrastructure_needs(spec, tech_stack)
        
        if needs.get("docker", False):
            docker_config = self._generate_dockerfile(project_dir, tech_stack)
            if docker_config:
                infra_configs.append(docker_config)
        
        if needs.get("docker_compose", False):
            compose_config = self._generate_docker_compose(project_dir, spec, tech_stack)
            if compose_config:
                infra_configs.append(compose_config)
        
        if needs.get("kubernetes", False):
            k8s_configs = self._generate_kubernetes_manifests(project_dir, spec, tech_stack)
            infra_configs.extend(k8s_configs)
        
        if needs.get("helm", False):
            helm_config = self._generate_helm_chart(project_dir, spec, tech_stack)
            if helm_config:
                infra_configs.append(helm_config)
        
        return {
            "generated_configs": infra_configs,
            "deployment_ready": len(infra_configs) > 0,
            "recommendations": self._generate_deployment_recommendations(spec, tech_stack)
        }
    
    def _analyze_infrastructure_needs(self, spec: Dict[str, Any], 
                                    tech_stack: List[str]) -> Dict[str, bool]:
        """Analyze what infrastructure configurations are needed"""
        
        needs = {
            "docker": True,  # Always generate Dockerfile
            "docker_compose": False,
            "kubernetes": False, 
            "helm": False
        }
        
        # Check for database requirements
        if any(db in tech_stack for db in ["postgresql", "mongodb", "redis"]):
            needs["docker_compose"] = True
        
        # Check for production/scaling requirements
        prompt = spec.get("prompt", "").lower()
        constraints = spec.get("constraints", "").lower()
        
        if any(word in f"{prompt} {constraints}" for word in 
               ["production", "scale", "kubernetes", "k8s", "cloud"]):
            needs["kubernetes"] = True
            
        if any(word in f"{prompt} {constraints}" for word in
               ["helm", "enterprise", "multiple environments"]):
            needs["helm"] = True
        
        return needs
    
    def _generate_dockerfile(self, project_dir: Path, tech_stack: List[str]) -> Optional[InfraConfig]:
        """Generate Dockerfile for the project"""
        
        # Determine base image
        python_version = "3.11"  # Default
        base_image = f"python:{python_version}-slim"
        
        # Build Dockerfile content
        dockerfile_content = f"""FROM {base_image}

WORKDIR /app

# Install system dependencies if needed
RUN apt-get update && apt-get install -y \\
    gcc \\
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \\
    CMD curl -f http://localhost:8000/health || exit 1

# Default command
"""
        
        # Determine command based on tech stack
        if "fastapi" in tech_stack:
            dockerfile_content += 'CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]'
        elif "flask" in tech_stack:
            dockerfile_content += 'CMD ["python", "app.py"]'
        elif "django" in tech_stack:
            dockerfile_content += 'CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]'
        else:
            dockerfile_content += 'CMD ["python", "main.py"]'
        
        # Write Dockerfile
        dockerfile_path = project_dir / "Dockerfile"
        with open(dockerfile_path, 'w') as f:
            f.write(dockerfile_content)
        
        return InfraConfig(
            deployment_type="docker",
            environment="all",
            config={"dockerfile_path": str(dockerfile_path)}
        )
    
    def _generate_docker_compose(self, project_dir: Path, spec: Dict[str, Any],
                                tech_stack: List[str]) -> Optional[InfraConfig]:
        """Generate docker-compose.yml for local development"""
        
        services = {}
        
        # Main application service
        services["app"] = {
            "build": ".",
            "ports": ["8000:8000"],
            "environment": [
                "PYTHONPATH=/app",
                "ENVIRONMENT=development"
            ],
            "volumes": [".:/app"],
            "depends_on": []
        }
        
        # Add database services
        if "postgresql" in tech_stack:
            services["db"] = {
                "image": "postgres:15",
                "environment": {
                    "POSTGRES_DB": "appdb",
                    "POSTGRES_USER": "user", 
                    "POSTGRES_PASSWORD": "password"
                },
                "volumes": ["postgres_data:/var/lib/postgresql/data"],
                "ports": ["5432:5432"]
            }
            services["app"]["depends_on"].append("db")
            services["app"]["environment"].append("DATABASE_URL=postgresql://user:password@db:5432/appdb")
        
        elif "mongodb" in tech_stack:
            services["mongo"] = {
                "image": "mongo:6",
                "environment": {
                    "MONGO_INITDB_ROOT_USERNAME": "admin",
                    "MONGO_INITDB_ROOT_PASSWORD": "password"
                },
                "volumes": ["mongo_data:/data/db"],
                "ports": ["27017:27017"]
            }
            services["app"]["depends_on"].append("mongo")
        
        # Add Redis if needed
        if "redis" in tech_stack or "celery" in tech_stack:
            services["redis"] = {
                "image": "redis:7-alpine",
                "ports": ["6379:6379"]
            }
            services["app"]["depends_on"].append("redis")
        
        compose_config = {
            "version": "3.8",
            "services": services
        }
        
        # Add volumes if databases are used
        if any(db in tech_stack for db in ["postgresql", "mongodb"]):
            compose_config["volumes"] = {}
            if "postgresql" in tech_stack:
                compose_config["volumes"]["postgres_data"] = {}
            if "mongodb" in tech_stack:
                compose_config["volumes"]["mongo_data"] = {}
        
        # Write docker-compose.yml
        compose_path = project_dir / "docker-compose.yml"
        with open(compose_path, 'w') as f:
            yaml.dump(compose_config, f, default_flow_style=False)
        
        return InfraConfig(
            deployment_type="docker_compose",
            environment="development",
            config={"compose_path": str(compose_path)}
        )
    
    def _generate_kubernetes_manifests(self, project_dir: Path, spec: Dict[str, Any],
                                     tech_stack: List[str]) -> List[InfraConfig]:
        """Generate Kubernetes deployment manifests"""
        
        configs = []
        k8s_dir = project_dir / "k8s"
        k8s_dir.mkdir(exist_ok=True)
        
        app_name = spec.get("name", "app").lower().replace(" ", "-")
        
        # 1. Deployment
        deployment = {
            "apiVersion": "apps/v1",
            "kind": "Deployment",
            "metadata": {"name": f"{app_name}-deployment"},
            "spec": {
                "replicas": 3,
                "selector": {"matchLabels": {"app": app_name}},
                "template": {
                    "metadata": {"labels": {"app": app_name}},
                    "spec": {
                        "containers": [{
                            "name": app_name,
                            "image": f"{app_name}:latest",
                            "ports": [{"containerPort": 8000}],
                            "env": [
                                {"name": "ENVIRONMENT", "value": "production"}
                            ],
                            "resources": {
                                "limits": {"cpu": "500m", "memory": "512Mi"},
                                "requests": {"cpu": "250m", "memory": "256Mi"}
                            },
                            "livenessProbe": {
                                "httpGet": {"path": "/health", "port": 8000},
                                "initialDelaySeconds": 30,
                                "periodSeconds": 10
                            }
                        }]
                    }
                }
            }
        }
        
        deployment_path = k8s_dir / "deployment.yaml"
        with open(deployment_path, 'w') as f:
            yaml.dump(deployment, f, default_flow_style=False)
        
        configs.append(InfraConfig(
            deployment_type="kubernetes",
            environment="production",
            config={"manifest_path": str(deployment_path), "type": "deployment"}
        ))
        
        # 2. Service
        service = {
            "apiVersion": "v1",
            "kind": "Service",
            "metadata": {"name": f"{app_name}-service"},
            "spec": {
                "selector": {"app": app_name},
                "ports": [{"port": 80, "targetPort": 8000}],
                "type": "ClusterIP"
            }
        }
        
        service_path = k8s_dir / "service.yaml"
        with open(service_path, 'w') as f:
            yaml.dump(service, f, default_flow_style=False)
        
        configs.append(InfraConfig(
            deployment_type="kubernetes", 
            environment="production",
            config={"manifest_path": str(service_path), "type": "service"}
        ))
        
        # 3. Ingress (if web app)
        if any(word in spec.get("prompt", "").lower() for word in ["api", "web", "frontend"]):
            ingress = {
                "apiVersion": "networking.k8s.io/v1",
                "kind": "Ingress",
                "metadata": {
                    "name": f"{app_name}-ingress",
                    "annotations": {
                        "nginx.ingress.kubernetes.io/rewrite-target": "/"
                    }
                },
                "spec": {
                    "rules": [{
                        "host": f"{app_name}.local",
                        "http": {
                            "paths": [{
                                "path": "/",
                                "pathType": "Prefix",
                                "backend": {
                                    "service": {
                                        "name": f"{app_name}-service",
                                        "port": {"number": 80}
                                    }
                                }
                            }]
                        }
                    }]
                }
            }
            
            ingress_path = k8s_dir / "ingress.yaml"
            with open(ingress_path, 'w') as f:
                yaml.dump(ingress, f, default_flow_style=False)
            
            configs.append(InfraConfig(
                deployment_type="kubernetes",
                environment="production", 
                config={"manifest_path": str(ingress_path), "type": "ingress"}
            ))
        
        return configs
    
    def _generate_helm_chart(self, project_dir: Path, spec: Dict[str, Any],
                           tech_stack: List[str]) -> Optional[InfraConfig]:
        """Generate Helm chart for the application"""
        
        app_name = spec.get("name", "app").lower().replace(" ", "-")
        helm_dir = project_dir / "helm" / app_name
        helm_dir.mkdir(parents=True, exist_ok=True)
        
        # Chart.yaml
        chart_yaml = {
            "apiVersion": "v2",
            "name": app_name,
            "description": f"Helm chart for {app_name}",
            "version": "0.1.0",
            "appVersion": "1.0.0"
        }
        
        with open(helm_dir / "Chart.yaml", 'w') as f:
            yaml.dump(chart_yaml, f, default_flow_style=False)
        
        # values.yaml with sensible defaults
        values_yaml = {
            "replicaCount": 2,
            "image": {
                "repository": app_name,
                "tag": "latest",
                "pullPolicy": "IfNotPresent"
            },
            "service": {
                "type": "ClusterIP",
                "port": 80,
                "targetPort": 8000
            },
            "ingress": {
                "enabled": True,
                "className": "nginx",
                "host": f"{app_name}.local"
            },
            "resources": {
                "limits": {"cpu": "500m", "memory": "512Mi"},
                "requests": {"cpu": "250m", "memory": "256Mi"}
            },
            "autoscaling": {
                "enabled": False,
                "minReplicas": 2,
                "maxReplicas": 10,
                "targetCPUUtilizationPercentage": 80
            }
        }
        
        with open(helm_dir / "values.yaml", 'w') as f:
            yaml.dump(values_yaml, f, default_flow_style=False)
        
        return InfraConfig(
            deployment_type="helm",
            environment="all",
            config={"chart_path": str(helm_dir)}
        )
    
    def _generate_deployment_recommendations(self, spec: Dict[str, Any], 
                                           tech_stack: List[str]) -> List[str]:
        """Generate deployment recommendations based on project needs"""
        
        recommendations = []
        
        # Basic recommendations
        recommendations.append("Use Docker for consistent deployments across environments")
        
        if any(db in tech_stack for db in ["postgresql", "mongodb"]):
            recommendations.append("Use docker-compose for local development with database")
            recommendations.append("Consider managed database services in production")
        
        # Scale-based recommendations
        prompt = spec.get("prompt", "").lower()
        if "production" in prompt or "scale" in prompt:
            recommendations.append("Deploy to Kubernetes for production scalability")
            recommendations.append("Use Helm charts for environment management")
            recommendations.append("Implement horizontal pod autoscaling")
        
        if "api" in prompt:
            recommendations.append("Configure ingress controller for API routing")
            recommendations.append("Add rate limiting and API gateway")
        
        return recommendations
