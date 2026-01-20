from uuid import UUID
from app.domains.users.repository import UserRepository
from app.domains.tenants.repository import TenantRepository
from app.domains.roles.repository import RoleRepository
from app.domains.users.schemas import UserCreateSchema, UserUpdateSchema
from app.domains.shared.schemas.pagination import PaginationParams
from app.core.exceptions import ResourceConflict, AuthorizationError, ResourceNotFound


class UserService:
    def __init__(
        self,
        user_repo: UserRepository,
        tenant_repo: TenantRepository,
        role_repo: RoleRepository,
    ):
        self.user_repo = user_repo
        self.tenant_repo = tenant_repo
        self.role_repo = role_repo

    async def create_user(
        self,
        *,
        data: UserCreateSchema,
        actor,  # current_user
    ):
        # 1️⃣ Email uniqueness (global)
        existing = await self.user_repo.get_by_email(data.email)
        if existing:
            raise ResourceConflict("User with this email already exists")

        # 2️⃣ Resolve tenant context
        if actor.tenant_id is None:
            tenant_id = data.tenant_id  # may be None or UUID
        else:
            if data.tenant_id and data.tenant_id != actor.tenant_id:
                raise AuthorizationError("Cannot create user for another tenant")

            tenant_id = actor.tenant_id

        # 3️⃣ Validate tenant (if applicable)
        if tenant_id:
            tenant = await self.tenant_repo.get_active_by_id(tenant_id)
            if not tenant:
                raise ResourceNotFound("Tenant not found or inactive")

        # 4️⃣ Validate role
        role = await self.role_repo.get_by_id(data.role_id)
        if not role:
            raise ResourceNotFound("Role not found")

        # Role must belong to same tenant OR be system role
        if role.tenant_id is not None and role.tenant_id != tenant_id:
            raise AuthorizationError("Role does not belong to this tenant")

        # 3️⃣ Create user
        user = await self.user_repo.create(
            email=data.email,
            first_name=data.first_name,
            last_name=data.last_name,
            role_id=data.role_id,
            tenant_id=tenant_id,
        )

        return user
    
    async def list_users(
        self,
        *,
        actor,
        pagination: PaginationParams,
    ):
        # 🔐 Scope resolution
        if actor.tenant_id is None:
            tenant_id = None  # system → all users
        else:
            tenant_id = actor.tenant_id  # tenant → own users only

        users, total = await self.user_repo.list_paginated(
            tenant_id=tenant_id,
            offset=pagination.offset,
            limit=pagination.limit,
        )

        return users, total
    
    async def update_user(
        self,
        *,
        user_id,
        data: UserUpdateSchema,
        actor,
    ):
        # 1️⃣ Resolve scope
        scope_tenant_id = None if actor.tenant_id is None else actor.tenant_id

        user = await self.user_repo.get_by_id_scoped(
            user_id=user_id,
            tenant_id=scope_tenant_id,
        )

        if not user:
            raise ResourceNotFound("User not found")

        # 2️⃣ Role update validation
        if data.role_id:
            role = await self.role_repo.get_by_id(data.role_id)
            if not role:
                raise ResourceNotFound("Role not found")

            if role.tenant_id is not None and role.tenant_id != user.tenant_id:
                raise AuthorizationError("Role does not belong to user's tenant")

            user.role_id = role.id

        # 3️⃣ Apply updates
        if data.first_name is not None:
            user.first_name = data.first_name

        if data.last_name is not None:
            user.last_name = data.last_name

        if data.user_status is not None:
            user.user_status = data.user_status

        return user
