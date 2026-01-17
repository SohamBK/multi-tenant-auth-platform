from uuid import UUID
from fastapi import APIRouter, Depends, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.exceptions import HTTPException

from app.api.deps.db import get_db
from app.api.deps.auth import get_current_user
from app.api.deps.permissions import PermissionChecker
from app.domains.tenants.repository import TenantRepository
from app.domains.tenants.service import TenantService
from app.domains.tenants.schemas import TenantCreateSchema, TenantResponseSchema, TenantUpdateSchema
from app.core.responses import SuccessResponse
from app.domains.shared.schemas.pagination import PaginatedData, PaginationParams
from app.domains.tenants.query_params import TenantListParams

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

@router.get(
    "/",
    response_model=SuccessResponse[PaginatedData[TenantResponseSchema]],
    dependencies=[Depends(PermissionChecker("tenants:view"))],
)
async def list_tenants(
    params: TenantListParams = Depends(),
    session: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if current_user.tenant_id is not None:
        raise HTTPException(status_code=403, detail="System access only")

    service = TenantService(TenantRepository(session))
    result = await service.list_tenants(params=params)

    return SuccessResponse(
        data=result,
        message="Tenants retrieved successfully",
    )

@router.patch(
    "/{tenant_id}",
    response_model=SuccessResponse[TenantResponseSchema],
    dependencies=[Depends(PermissionChecker("tenants:update"))],
)
async def update_tenant(
    tenant_id: UUID,
    payload: TenantUpdateSchema,
    request: Request,
    session: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    # 🔒 System-only
    if current_user.tenant_id is not None:
        raise HTTPException(status_code=403, detail="System access only")

    service = TenantService(TenantRepository(session))
    tenant = await service.update_tenant(tenant_id, payload)

    # Audit
    audit = AuditService(AuditLogRepository(session))
    await audit.log_action(
        tenant_id=tenant.id,
        actor_id=current_user.id,
        data=AuditLogCreate(
            action="tenants.update",
            resource_type="tenant",
            resource_id=str(tenant.id),
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            payload=payload.model_dump(exclude_none=True),
        ),
    )

    return SuccessResponse(
        data=TenantResponseSchema.model_validate(tenant),
        message="Tenant updated successfully",
    )

@router.delete(
    "/{tenant_id}",
    response_model=SuccessResponse[TenantResponseSchema],
    dependencies=[Depends(PermissionChecker("tenants:delete"))],
)
async def deactivate_tenant(
    tenant_id: UUID,
    request: Request,
    session: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    # 🔒 System-only
    if current_user.tenant_id is not None:
        raise HTTPException(status_code=403, detail="System access only")

    service = TenantService(TenantRepository(session))
    tenant = await service.deactivate_tenant(tenant_id)

    # Audit
    audit = AuditService(AuditLogRepository(session))
    await audit.log_action(
        tenant_id=tenant.id,
        actor_id=current_user.id,
        data=AuditLogCreate(
            action="tenants.deactivate",
            resource_type="tenant",
            resource_id=str(tenant.id),
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            payload=None,
        ),
    )

    return SuccessResponse(
        data=TenantResponseSchema.model_validate(tenant),
        message="Tenant deactivated successfully",
    )

@router.post(
    "/{tenant_id}/reactivate",
    response_model=SuccessResponse[TenantResponseSchema],
    dependencies=[Depends(PermissionChecker("tenants:update"))],
)
async def reactivate_tenant(
    tenant_id: UUID,
    request: Request,
    session: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if current_user.tenant_id is not None:
        raise HTTPException(status_code=403, detail="System access only")

    service = TenantService(TenantRepository(session))
    tenant = await service.reactivate_tenant(tenant_id)

    # Audit log
    audit = AuditService(AuditLogRepository(session))
    await audit.log_action(
        tenant_id=tenant.id,
        actor_id=current_user.id,
        data=AuditLogCreate(
            action="tenants.reactivate",
            resource_type="tenant",
            resource_id=str(tenant.id),
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            payload=None,
        ),
    )

    return SuccessResponse(
        data=TenantResponseSchema.model_validate(tenant),
        message="Tenant reactivated successfully",
    )