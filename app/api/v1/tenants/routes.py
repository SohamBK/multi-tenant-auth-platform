from fastapi import APIRouter, Depends, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.exceptions import HTTPException

from app.api.deps.db import get_db
from app.api.deps.auth import get_current_user
from app.api.deps.permissions import PermissionChecker
from app.domains.tenants.repository import TenantRepository
from app.domains.tenants.service import TenantService
from app.domains.tenants.schemas import TenantCreateSchema, TenantResponseSchema
from app.core.responses import SuccessResponse

from app.domains.audit.repository import AuditLogRepository
from app.domains.audit.service import AuditService
from app.domains.audit.schemas import AuditLogCreate

router = APIRouter(prefix="/tenants", tags=["Tenants"])


@router.post(
    "/",
    response_model=SuccessResponse[TenantResponseSchema],
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(PermissionChecker("tenants:create"))],
)
async def create_tenant(
    payload: TenantCreateSchema,
    request: Request,
    session: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    # 🔒 System-only enforcement
    if current_user.tenant_id is not None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only system administrators can create tenants",
        )

    service = TenantService(TenantRepository(session))
    tenant = await service.create_tenant(payload)

    # 🔍 AUDIT LOGGING
    audit_service = AuditService(AuditLogRepository(session))

    await audit_service.log_action(
        tenant_id=tenant.id,                 # 🔑 tenant created
        actor_id=current_user.id,             # 🔑 who did it
        data=AuditLogCreate(
            action="tenants.create",
            resource_type="tenant",
            resource_id=str(tenant.id),
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            payload={
                "name": tenant.name,
            },
        ),
    )

    return SuccessResponse(
        data=TenantResponseSchema.model_validate(tenant),
        message="Tenant created successfully",
    )
