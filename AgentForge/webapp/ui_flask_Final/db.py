"""Database configuration for AgentForge UI v3"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from pathlib import Path

# Database file path
DB_PATH = Path(__file__).parent / "agentforge_v3.db"

# Create engine
engine = create_engine(f'sqlite:///{DB_PATH}', echo=False)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """Dependency to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
