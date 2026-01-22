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
from app.domains.rbac.roles.schemas import RoleSchema, RoleCreateSchema, RoleUpdateSchema, RolePermissionAttachSchema

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
    service = RoleService(
        RoleRepository(session),
        PermissionRepository(session),
        TenantRepository(session),
    )
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
    service = RoleService(
        RoleRepository(session),
        PermissionRepository(session),
        TenantRepository(session),
    )
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

@router.put(
    "/{role_id}",
    response_model=SuccessResponse[RoleSchema],
    dependencies=[Depends(PermissionChecker("roles:update"))],
)
async def update_role(
    role_id: UUID,
    payload: RoleUpdateSchema,
    request: Request,
    session: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    service = RoleService(
        role_repo=RoleRepository(session),
        permission_repo=PermissionRepository(session),
        tenant_repo=TenantRepository(session),
    )

    role = await service.update_role(
        role_id=role_id,
        data=payload,
        actor=current_user,
    )

    # Audit
    await AuditService(AuditLogRepository(session)).log_action(
        tenant_id=role.tenant_id,
        actor_id=current_user.id,
        data=AuditLogCreate(
            action="roles.update",
            resource_type="role",
            resource_id=str(role.id),
            payload=payload.model_dump(exclude_none=True),
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        ),
    )

    return SuccessResponse(
        data=RoleSchema.model_validate(role),
        message="Role updated successfully",
    )

@router.delete(
    "/{role_id}",
    response_model=SuccessResponse[None],
    dependencies=[Depends(PermissionChecker("roles:delete"))],
)
async def delete_role(
    role_id: UUID,
    request: Request,
    session: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    service = RoleService(
        role_repo=RoleRepository(session),
        permission_repo=PermissionRepository(session),
        tenant_repo=TenantRepository(session),
    )

    role = await service.delete_role(
        role_id=role_id,
        actor=current_user,
    )

    await AuditService(AuditLogRepository(session)).log_action(
        tenant_id=role.tenant_id,
        actor_id=current_user.id,
        data=AuditLogCreate(
            action="roles.delete",
            resource_type="role",
            resource_id=str(role.id),
            payload={"name": role.name},
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        ),
    )

    return SuccessResponse(
        data =None,
        message="Role deleted successfully"
    )

@router.patch(
    "/{role_id}/reactivate",
    response_model=SuccessResponse[None],
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(PermissionChecker("roles:update"))],
)
async def reactivate_role(
    role_id: UUID,
    request: Request,
    session=Depends(get_db),
    current_user=Depends(get_current_user),
):
    service = RoleService(
        role_repo=RoleRepository(session),
        permission_repo=PermissionRepository(session),
        tenant_repo=TenantRepository(session),
    )

    role = await service.reactivate_role(
        role_id=role_id,
        actor=current_user,
    )

    # 🧾 Audit log
    await AuditService(AuditLogRepository(session)).log_action(
        tenant_id=role.tenant_id,
        actor_id=current_user.id,
        data=AuditLogCreate(
            action="roles.reactivate",
            resource_type="role",
            resource_id=str(role.id),
            payload={"name": role.name},
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        ),
    )

    return SuccessResponse(
        data=None,
        message="Role reactivated successfully"
    )

@router.post(
    "/{role_id}/permissions",
    response_model=SuccessResponse[RoleSchema],
    dependencies=[Depends(PermissionChecker("roles:update"))],
)
async def attach_permissions(
    role_id: UUID,
    payload: RolePermissionAttachSchema,
    request: Request,
    session: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    service = RoleService(
        role_repo=RoleRepository(session),
        permission_repo=PermissionRepository(session),
        tenant_repo=TenantRepository(session),
    )

    role, attached = await service.attach_permissions(
        role_id=role_id,
        data=payload,
        actor=current_user,
    )

    await AuditService(AuditLogRepository(session)).log_action(
        tenant_id=role.tenant_id,
        actor_id=current_user.id,
        data=AuditLogCreate(
            action="roles.permissions.attach",
            resource_type="role",
            resource_id=str(role.id),
            payload={
                "attached_permission_ids": [str(p.id) for p in attached]
            },
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        ),
    )

    return SuccessResponse(
        data=RoleSchema.model_validate(role),
        message="Permissions attached successfully",
    )

@router.delete(
    "/{role_id}/permissions/{permission_id}",
    response_model=SuccessResponse[None],
    dependencies=[Depends(PermissionChecker("roles:update"))],
)
async def detach_permission(
    role_id: UUID,
    permission_id: UUID,
    request: Request,
    session: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    service = RoleService(
        role_repo=RoleRepository(session),
        permission_repo=PermissionRepository(session),
        tenant_repo=TenantRepository(session),
    )

    role, permission = await service.detach_permission(
        role_id=role_id,
        permission_id=permission_id,
        actor=current_user,
    )

    await AuditService(AuditLogRepository(session)).log_action(
        tenant_id=role.tenant_id,
        actor_id=current_user.id,
        data=AuditLogCreate(
            action="roles.permissions.detach",
            resource_type="role",
            resource_id=str(role.id),
            payload={"permission_id": str(permission.id)},
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        ),
    )

    return SuccessResponse(
        data=None,
        message="Permission detached successfully"
    )
