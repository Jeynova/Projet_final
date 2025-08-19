import os
from datetime import datetime, timedelta
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
import jwt

from .db import get_db
from .models import User

JWT_SECRET = os.getenv("JWT_SECRET", "devsecret")
ALGORITHM = "HS256"
auth_scheme = HTTPBearer(auto_error=False)

def get_current_user(
    token: Optional[HTTPAuthorizationCredentials] = Depends(auth_scheme),
    db: Session = Depends(get_db)
):
    # MVP: n'impose pas l'auth, retourne None si pas de token
    if token is None:
        return None
    
    try:
        payload = jwt.decode(token.credentials, JWT_SECRET, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            return None
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user