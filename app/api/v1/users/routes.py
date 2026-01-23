from uuid import UUID
from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps.db import get_db
from app.api.deps.auth import get_current_user
from app.infrastructure.db.models.user import User
from app.api.deps.permissions import PermissionChecker

from app.domains.users.schemas import UserCreateSchema, UserSchema, UserUpdateSchema, UserFilterParams, UserRoleAssignSchema, UserMeSchema
from app.domains.users.repository import UserRepository
from app.domains.users.service import UserService

from app.domains.tenants.repository import TenantRepository
from app.domains.rbac.roles.repository import RoleRepository
from app.domains.shared.schemas.pagination import PaginationParams, PaginatedData, PaginationMeta

from app.domains.audit.repository import AuditLogRepository
from app.domains.audit.service import AuditService
from app.domains.audit.schemas import AuditLogCreate

from app.core.responses import SuccessResponse

router = APIRouter(prefix="/users", tags=["Users"])

@router.get("/me", response_model=SuccessResponse[UserMeSchema])
async def read_user_me(
    current_user: User = Depends(get_current_user),
):
    """
    Returns the profile + RBAC context of the currently authenticated user.
    """

    role = current_user.role
    permissions = [p.slug for p in role.permissions]

    data = UserMeSchema(
        id=current_user.id,
        email=current_user.email,
        first_name=current_user.first_name,
        last_name=current_user.last_name,

        tenant_id=current_user.tenant_id,
        tenant_name=current_user.tenant.name if current_user.tenant else None,

        role_id=role.id,
        role_name=role.name,

        permissions=permissions,
    )

    return SuccessResponse(
        data=data,
        message="User context retrieved",
    )

@router.post(
    "/",
    response_model=SuccessResponse[UserSchema],
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(PermissionChecker("users:create"))],
)
async def create_user(
    payload: UserCreateSchema,
    request: Request,
    session: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    user_repo = UserRepository(session)
    tenant_repo = TenantRepository(session)
    role_repo = RoleRepository(session)

    service = UserService(
        user_repo=user_repo,
        tenant_repo=tenant_repo,
        role_repo=role_repo,
    )
    
    user = await service.create_user(
        data=payload,
        actor=current_user,
    )

    # Audit
    audit = AuditService(AuditLogRepository(session))
    await audit.log_action(
        tenant_id=user.tenant_id or current_user.tenant_id,
        actor_id=current_user.id,
        data=AuditLogCreate(
            action="users.create",
            resource_type="user",
            resource_id=str(user.id),
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            payload={
                "email": user.email,
                "tenant_id": str(user.tenant_id) if user.tenant_id else None,
            },
        ),
    )

    return SuccessResponse(
        data=UserSchema.model_validate(user),
        message="User created successfully",
    )

@router.get(
    "/",
    response_model=SuccessResponse[PaginatedData[UserSchema]],
    dependencies=[Depends(PermissionChecker("users:read"))],
)
async def list_users(
    pagination: PaginationParams = Depends(),
    filters: UserFilterParams = Depends(),
    session: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    service = UserService(
        user_repo=UserRepository(session),
        tenant_repo=None,
        role_repo=None,
    )

    users, total = await service.list_users(
        actor=current_user,
        pagination=pagination,
        filters=filters,
    )

    return SuccessResponse(
        data=PaginatedData(
            items=[UserSchema.model_validate(u) for u in users],
            pagination=PaginationMeta.create(
                page=pagination.page,
                page_size=pagination.page_size,
                total_items=total,
            ),
        ),
        message="Users retrieved successfully",
    )

@router.patch(
    "/{user_id}",
    response_model=SuccessResponse[UserSchema],
    dependencies=[Depends(PermissionChecker("users:update"))],
)
async def update_user(
    user_id: UUID,
    payload: UserUpdateSchema,
    request: Request,
    session: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    service = UserService(
        user_repo=UserRepository(session),
        tenant_repo=TenantRepository(session),
        role_repo=RoleRepository(session),
    )

    user = await service.update_user(
        user_id=user_id,
        data=payload,
        actor=current_user,
    )

    # Audit
    await AuditService(AuditLogRepository(session)).log_action(
        tenant_id=user.tenant_id or current_user.tenant_id,
        actor_id=current_user.id,
        data=AuditLogCreate(
            action="users.update",
            resource_type="user",
            resource_id=str(user.id),
            payload=payload.model_dump(exclude_unset=True),
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        ),
    )

    return SuccessResponse(
        data=UserSchema.model_validate(user),
        message="User updated successfully",
    )

@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(PermissionChecker("users:delete"))],
)
async def delete_user(
    user_id: UUID,
    request: Request,
    session: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    service = UserService(
        user_repo=UserRepository(session),
        tenant_repo=TenantRepository(session),
        role_repo=RoleRepository(session),
    )

    user = await service.update_user(
        user_id=user_id,
        data=UserUpdateSchema(user_status="inactive"),
        actor=current_user,
    )

    await AuditService(AuditLogRepository(session)).log_action(
        tenant_id=user.tenant_id or current_user.tenant_id,
        actor_id=current_user.id,
        data=AuditLogCreate(
            action="users.delete",
            resource_type="user",
            resource_id=str(user.id),
            payload={"status": "inactive"},
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        ),
    )


@router.post(
    "/{user_id}/reactivate",
    response_model=SuccessResponse[UserSchema],
    dependencies=[Depends(PermissionChecker("users:reactivate"))],
)
async def reactivate_user(
    user_id: UUID,
    request: Request,
    session: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    service = UserService(
        user_repo=UserRepository(session),
        tenant_repo=TenantRepository(session),
        role_repo=RoleRepository(session),
    )

    user = await service.update_user(
        user_id=user_id,
        data=UserUpdateSchema(user_status="active"),
        actor=current_user,
    )

    await AuditService(AuditLogRepository(session)).log_action(
        tenant_id=user.tenant_id or current_user.tenant_id,
        actor_id=current_user.id,
        data=AuditLogCreate(
            action="users.reactivate",
            resource_type="user",
            resource_id=str(user.id),
            payload={"status": "active"},
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        ),
    )

    return SuccessResponse(
        data=UserSchema.model_validate(user),
        message="User reactivated successfully",
    )

@router.patch(
    "/{user_id}/role",
    response_model=SuccessResponse[UserSchema],
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(PermissionChecker("users:update"))],
)
async def assign_role_to_user(
    user_id: UUID,
    payload: UserRoleAssignSchema,
    request: Request,
    session: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    service = UserService(
        user_repo=UserRepository(session),
        role_repo=RoleRepository(session),
        tenant_repo=TenantRepository(session),
    )

    user, role = await service.assign_role(
        user_id=user_id,
        data=payload,
        actor=current_user,
    )

    # 🧾 Audit
    await AuditService(AuditLogRepository(session)).log_action(
        tenant_id=user.tenant_id,
        actor_id=current_user.id,
        data=AuditLogCreate(
            action="users.role.assign",
            resource_type="user",
            resource_id=str(user.id),
            payload={
                "assigned_role_id": str(role.id),
                "assigned_role_name": role.name,
            },
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        ),
    )

    return SuccessResponse(
        data=UserSchema.model_validate(user),
        message="Role assigned to user successfully",
    )