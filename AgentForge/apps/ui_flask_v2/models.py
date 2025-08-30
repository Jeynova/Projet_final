"""Database models for AgentForge UI v2"""
from sqlalchemy import Column, Integer, String, DateTime, Text, Float
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class Project(Base):
    __tablename__ = 'projects'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    path = Column(String(500))
    zip_path = Column(String(500))
    orchestrator_version = Column(String(10), default='v2')  # v1 or v2
    created_at = Column(DateTime, default=datetime.utcnow)
    file_count = Column(Integer, default=0)
    quality_score = Column(Float, default=0.0)
    tech_stack = Column(Text)  # JSON string of tech stack
    execution_time = Column(Float, default=0.0)
    
    def __repr__(self):
        return f'<Project {self.name}>'

class AgentExecution(Base):
    __tablename__ = 'agent_executions'
    
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer)
    agent_id = Column(String(50))
    agent_class = Column(String(100))
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    duration = Column(Float)
    score = Column(Float)
    competitors = Column(Integer)
    result_summary = Column(Text)
    success = Column(Integer, default=1)  # 1=success, 0=failure
    
    def __repr__(self):
        return f'<AgentExecution {self.agent_id}>'

class DockerImage(Base):
    __tablename__ = 'docker_images'
    
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer)
    image_name = Column(String(200))
    tag = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<DockerImage {self.image_name}:{self.tag}>'
