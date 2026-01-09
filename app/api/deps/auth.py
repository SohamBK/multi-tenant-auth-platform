from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps.db import get_db
from app.domains.users.repository import UserRepository
from app.security.tokens import decode_token
from app.infrastructure.db.models.user import User
from app.security.permissions import has_permission

# Security scheme for Swagger UI
security = HTTPBearer()

async def get_current_user(
    auth: HTTPAuthorizationCredentials = Depends(security),
    session: AsyncSession = Depends(get_db)
) -> User:
    """
    Validates the Bearer token and retrieves the User with full RBAC context.
    """
    token = auth.credentials
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        # Decode the RS256 JWT
        payload = decode_token(token)
        user_id: str = payload.get("sub")
        if not user_id:
            raise credentials_exception
    except Exception:
        raise credentials_exception

    # Use the optimized repository method to get user + role + permissions
    user_repo = UserRepository(session)
    user = await user_repo.get_by_id(id=user_id)

    if not user or user.user_status != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="User inactive or not found"
        )

    return user

class PermissionChecker:
    """
    Dependency factory for granular, wildcard-aware RBAC.
    """
    def __init__(self, required_permission: str):
        self.required_permission = required_permission

    async def __call__(self, current_user: User = Depends(get_current_user)) -> bool:
        """
        Validates the user's role permissions against the required slug.
        """
        # 1. Ensure the user actually has a role assigned
        if not current_user.role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User has no assigned role"
            )

        # 2. Extract permission slugs (e.g., ['users:*', 'tenants:view'])
        user_permissions = [p.slug for p in current_user.role.permissions]
        
        # 3. Match against wildcard or exact slug
        if not has_permission(user_permissions, self.required_permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing required permission: {self.required_permission}"
            )
        
        return True