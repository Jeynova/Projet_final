from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()



class User(Base):
    __tablename__ = "users"
    
    
    
    id = Column(Integer, primary_key=True, unique=True, index=True, nullable=False)
    
    
    
    email = Column(String(255), unique=True, index=True, nullable=False)
    
    
    
    hashed_password = Column(String(255), index=False, nullable=False)
    
    
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    



