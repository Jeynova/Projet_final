"""Database models for AgentForge UI v3 - Organic Intelligence Edition"""
from sqlalchemy import Column, Integer, String, DateTime, Text, Float, Boolean
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class Project(Base):
    __tablename__ = 'projects'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    prompt = Column(Text)  # Original user prompt
    path = Column(String(500))
    zip_path = Column(String(500))
    orchestrator_version = Column(String(10), default='v3-organic')
    created_at = Column(DateTime, default=datetime.utcnow)
    file_count = Column(Integer, default=0)
    quality_score = Column(Float, default=0.0)
    tech_stack = Column(Text)  # JSON string of tech stack
    execution_time = Column(Float, default=0.0)
    status = Column(String(20), default='completed')  # running, completed, failed
    
    # Organic intelligence specific fields
    is_organic = Column(Boolean, default=True)
    llm_calls = Column(Integer, default=0)
    tech_choices_made = Column(Integer, default=0)
    team_perspectives = Column(Integer, default=0)
    
    def __repr__(self):
        return f'<Project {self.name} ({"Organic" if self.is_organic else "Classic"})>'

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
    
    # Organic intelligence specific fields
    llm_calls_made = Column(Integer, default=0)
    is_organic_agent = Column(Boolean, default=True)
    
    def __repr__(self):
        return f'<AgentExecution {self.agent_id}>'

class OrganicSession(Base):
    __tablename__ = 'organic_sessions'
    
    id = Column(Integer, primary_key=True)
    session_id = Column(String(100), nullable=False)
    project_id = Column(Integer)
    prompt = Column(Text)
    start_time = Column(DateTime, default=datetime.utcnow)
    end_time = Column(DateTime)
    total_agents = Column(Integer, default=8)
    completed_agents = Column(Integer, default=0)
    failed_agents = Column(Integer, default=0)
    skipped_agents = Column(Integer, default=0)
    total_llm_calls = Column(Integer, default=0)
    total_tech_choices = Column(Integer, default=0)
    status = Column(String(20), default='running')  # running, completed, failed
    
    def __repr__(self):
        return f'<OrganicSession {self.session_id}>'

class DockerImage(Base):
    __tablename__ = 'docker_images'
    
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer)
    image_name = Column(String(200))
    tag = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<DockerImage {self.image_name}:{self.tag}>'
