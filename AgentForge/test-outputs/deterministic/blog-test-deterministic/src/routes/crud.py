from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any

from ..db import get_db
from ..models import *
from ..security import get_current_user

router = APIRouter(tags=["crud"])



@router.get("/users", response_model=List[Dict[str, Any]])
def list_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """List all users"""
    items = db.query(User).offset(skip).limit(limit).all()
    return [item.__dict__ for item in items]

@router.get("/users/{item_id}", response_model=Dict[str, Any])
def get_user(
    item_id: int,
    db: Session = Depends(get_db)
):
    """Get user by ID"""
    item = db.query(User).filter(User.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="User not found")
    return item.__dict__

@router.post("/users", response_model=Dict[str, Any])
def create_user(
    item_data: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """Create new user"""
    # Remove id from data if present
    item_data.pop("id", None)
    item_data.pop("created_at", None)
    
    try:
        db_item = User(**item_data)
        db.add(db_item)
        db.commit()
        db.refresh(db_item)
        return db_item.__dict__
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/users/{item_id}", response_model=Dict[str, Any])
def update_user(
    item_id: int,
    item_data: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """Update user"""
    item = db.query(User).filter(User.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Remove fields that shouldn't be updated
    item_data.pop("id", None)
    item_data.pop("created_at", None)
    
    try:
        for key, value in item_data.items():
            if hasattr(item, key):
                setattr(item, key, value)
        
        db.commit()
        db.refresh(item)
        return item.__dict__
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/users/{item_id}")
def delete_user(
    item_id: int,
    db: Session = Depends(get_db)
):
    """Delete user"""
    item = db.query(User).filter(User.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="User not found")
    
    db.delete(item)
    db.commit()
    return {"message": "User deleted successfully"}



