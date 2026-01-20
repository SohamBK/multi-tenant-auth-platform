from fastapi import APIRouter, Depends, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.api.deps.db import get_db
from app.api.deps.auth import get_current_user
from app.api.deps.permissions import PermissionChecker

from app.domains.rbac.roles.repository import RoleRepository
from app.domains.rbac.permissions.repository import PermissionRepository
from app.domains.tenants.repository import TenantRepository
from app.domains.rbac.roles.service import RoleService
from app.domains.rbac.roles.schemas import RoleSchema, RoleCreateSchema

from app.domains.audit.repository import AuditLogRepository
from app.domains.audit.service import AuditService
from app.domains.audit.schemas import AuditLogCreate

from app.core.responses import SuccessResponse
from app.core.exceptions import ResourceNotFound

router = APIRouter(prefix="/roles", tags=["Roles"])


@router.get(
    "/",
    response_model=SuccessResponse[list[RoleSchema]],
    dependencies=[Depends(PermissionChecker("roles:read"))],
)
async def list_roles(
    session: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    service = RoleService(RoleRepository(session))
    roles = await service.list_roles(actor=current_user)

    return SuccessResponse(
        data=[RoleSchema.model_validate(r) for r in roles],
        message="Roles retrieved successfully",
    )


@router.get(
    "/{role_id}",
    response_model=SuccessResponse[RoleSchema],
    dependencies=[Depends(PermissionChecker("roles:read"))],
)
async def get_role(
    role_id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    service = RoleService(RoleRepository(session))
    role = await service.get_role(role_id, actor=current_user)

    if not role:
        raise ResourceNotFound("Role not found")

    return SuccessResponse(
        data=RoleSchema.model_validate(role),
        message="Role retrieved successfully",
    )

@router.post(
    "/",
    response_model=SuccessResponse[RoleSchema],
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(PermissionChecker("roles:create"))],
)
async def create_role(
    payload: RoleCreateSchema,
    request: Request,
    session: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    service = RoleService(
        role_repo=RoleRepository(session),
        permission_repo=PermissionRepository(session),
        tenant_repo=TenantRepository(session),
    )

    role = await service.create_role(
        data=payload,
        actor=current_user,
    )

    # Audit
    await AuditService(AuditLogRepository(session)).log_action(
        tenant_id=role.tenant_id,
        actor_id=current_user.id,
        data=AuditLogCreate(
            action="roles.create",
            resource_type="role",
            resource_id=str(role.id),
            payload={
                "name": role.name,
                "tenant_id": str(role.tenant_id) if role.tenant_id else None,
                "permission_ids": payload.permission_ids,
            },
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        ),
    )

    return SuccessResponse(
        data=RoleSchema.model_validate(role),
        message="Role created successfully",
    )
