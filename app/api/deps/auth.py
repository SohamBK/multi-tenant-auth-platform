from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps.db import get_db
from app.domains.users.repository import UserRepository
from app.security.tokens import decode_token

# ✅ Use HTTPBearer instead of OAuth2PasswordBearer
# auto_error=False allows us to handle the error response manually
security = HTTPBearer()

async def get_current_user(
    auth: HTTPAuthorizationCredentials = Depends(security),
    session: AsyncSession = Depends(get_db)
):
    """
    Directly accepts a Bearer token from the Authorize header.
    """
    token = auth.credentials # This is the raw string you paste in Swagger
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = decode_token(token)
        user_id: str = payload.get("sub")
        if not user_id:
            raise credentials_exception
    except Exception:
        raise credentials_exception

    user_repo = UserRepository(session)
    user = await user_repo.get_by_id(id=user_id)

    if not user or user.user_status != "active":
        raise HTTPException(status_code=403, detail="User inactive or not found")

    return user