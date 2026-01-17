from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps.db import get_db
from app.api.deps.tenant import get_current_tenant
from app.domains.users.repository import UserRepository
from app.security.tokens import decode_token

security = HTTPBearer()


async def get_current_user(
    auth: HTTPAuthorizationCredentials = Depends(security),
    session: AsyncSession = Depends(get_db),
    current_tenant=Depends(get_current_tenant),
):
    """
    Validates JWT and loads the authenticated user
    strictly within the tenant boundary.
    """
    token = auth.credentials

    try:
        payload = decode_token(token)
        user_id = payload.get("sub")

        if not user_id:
            raise ValueError("Missing sub in token")

    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_repo = UserRepository(session)
    user = await user_repo.get_by_id(
        id=user_id,
        tenant_id=current_tenant.id if current_tenant else None,
    )

    # --- User status check ---
    if not user or user.user_status != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User inactive or not found",
        )

    # --- 🔒 Tenant status enforcement ---
    # Applies ONLY to tenant-scoped users
    if user.tenant_id is not None:
        # current_tenant is guaranteed to be resolved by get_current_tenant
        if not current_tenant or current_tenant.tenant_status != "active":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Tenant is inactive",
            )

    return user
