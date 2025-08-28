from fastapi import APIRouter, HTTPException
from typing import List
from ..models import User

router = APIRouter()

@router.get("/users", response_model=List[dict])
async def get_users():
    """Récupère tous les users"""
    # TODO: Implémentation avec base de données
    return []

@router.post("/users", response_model=dict)
async def create_user(data: dict):
    """Crée un nouveau user"""
    # TODO: Implémentation avec base de données
    return {"id": 1, **data}

@router.get("/users/{item_id}")
async def get_user(item_id: int):
    """Récupère un user par ID"""
    # TODO: Implémentation avec base de données
    return {"id": item_id}
