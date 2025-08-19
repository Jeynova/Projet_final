from typing import Literal, Optional, List
from pydantic import BaseModel, Field

class FieldSpec(BaseModel):
    name: str
    type: Literal["int","str","float","bool","datetime"] = "str"
    pk: bool = False
    unique: bool = False
    nullable: bool = True

class EntitySpec(BaseModel):
    name: str
    fields: List[FieldSpec]

class ProjectSpec(BaseModel):
    name: str = Field(..., description="Nom du projet/dépôt")
    project_type: Literal["api", "webapp", "worker"] = "api"
    language: Literal["python", "node"] = "python"
    web: Optional[Literal["fastapi", "flask", "express"]] = None
    db: Optional[Literal["postgres", "sqlite", "mysql", "none"]] = "sqlite"
    auth: Literal["none", "jwt", "session"] = "jwt"
    features: List[str] = []
    tests: Literal["none", "basic", "crud"] = "basic"
    ci: Literal["none", "github_actions"] = "github_actions"
    security: Literal["baseline", "strict"] = "baseline"
    dockerize: bool = True
    infra: Optional[Literal["docker_compose", "k8s"]] = "docker_compose"
    entities: List[EntitySpec] = []   # <-- NOUVEAU

    def title(self) -> str:
        return self.name.replace(" ", "-")