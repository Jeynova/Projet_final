from typing import Literal, Optional, List
from pydantic import BaseModel, Field

class ProjectSpec(BaseModel):
    name: str = Field(..., description="Nom du projet (slug court, ex: fleet-api)")
    project_type: Literal["api","webapp","worker"] = "api"
    language: Literal["python","node"] = "python"
    web: Optional[Literal["fastapi","flask","express"]] = "fastapi"
    db: Optional[Literal["postgres","sqlite","mysql","none"]] = "postgres"
    auth: Literal["none","jwt","session"] = "jwt"
    features: List[str] = Field(default_factory=lambda: ["healthcheck", "rate_limit"])
    tests: Literal["none","basic","crud"] = "basic"
    ci: Literal["none","github_actions"] = "github_actions"
    security: Literal["baseline","strict"] = "baseline"
    dockerize: bool = True
    infra: Optional[Literal["docker_compose","k8s"]] = "docker_compose"