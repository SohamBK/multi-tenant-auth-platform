from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps.db import get_db
from app.domains.tenants.repository import TenantRepository
from app.security.tokens import decode_token

security = HTTPBearer()


async def get_current_tenant(
    auth: HTTPAuthorizationCredentials = Depends(security),
    session: AsyncSession = Depends(get_db),
):
    token = auth.credentials

    try:
        payload = decode_token(token)
        tenant_id = payload.get("tenant_id")
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    # 🔹 SYSTEM CONTEXT
    if tenant_id is None:
        return None

    # 🔹 TENANT CONTEXT
    tenant_repo = TenantRepository(session)
    tenant = await tenant_repo.get_by_id(tenant_id)

    if not tenant or tenant.tenant_status != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tenant inactive or not found",
        )

    return tenant
