from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean
from sqlalchemy.sql import func
from .db import Base

class Project(Base):
    __tablename__ = "projects"
    id = Column(Integer, primary_key=True)
    name = Column(String(128), index=True, nullable=False)
    prompt = Column(Text, nullable=False)
    status = Column(String(32), default="unknown")
    project_path = Column(Text, nullable=False)     # chemin sur disque
    zip_path = Column(Text, nullable=False)         # chemin zip
    logs_path = Column(Text, nullable=True)         # fichier json de logs (optionnel)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class DockerImage(Base):
    __tablename__ = "docker_images"
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, index=True, nullable=False)
    image_name = Column(String(256), nullable=False)  # ex: jeynova/fleet-api
    image_tag = Column(String(64), default="latest")
    registry_url = Column(String(512), nullable=True) # ex: ghcr.io/...
    pushed = Column(Boolean, default=False)
    push_log = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
