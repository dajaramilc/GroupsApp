"""
Shared FastAPI dependencies (authentication, etc.).
"""
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.user import User

bearer_scheme = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Decode JWT, fetch and return the current User or raise 401."""
    token = credentials.credentials
    user_id = decode_access_token(token)
    if user_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")

    # En una arquitectura de microservicios con BD distribuida, 
    # confiamos en la firma del JWT y construimos un usuario en memoria.
    # Así evitamos consultar la tabla 'users' que solo existe en auth.db
    return User(id=UUID(user_id), is_active=True)
