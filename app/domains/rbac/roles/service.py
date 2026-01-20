from app.domains.rbac.roles.repository import RoleRepository
from app.domains.tenants.repository import TenantRepository
from app.domains.rbac.permissions.repository import PermissionRepository
from app.domains.rbac.roles.schemas import RoleCreateSchema
from app.infrastructure.db.models.auth_rbac import Role
from app.core.exceptions import ResourceConflict, ResourceNotFound, AuthorizationError

class RoleService:
    def __init__(
            self, 
            role_repo: RoleRepository,
            permission_repo: PermissionRepository,
            tenant_repo: TenantRepository,
        ):
        self.role_repo = role_repo
        self.permission_repo = permission_repo
        self.tenant_repo = tenant_repo

    async def list_roles(self, actor):
        # Super admin → see everything
        tenant_id = None if actor.tenant_id is None else actor.tenant_id
        return await self.role_repo.list_visible_roles(tenant_id)

    async def get_role(self, role_id, actor):
        roles = await self.list_roles(actor)
        for role in roles:
            if role.id == role_id:
                return role
        return None

    async def create_role(self, *, data: RoleCreateSchema, actor):
        # 1️⃣ Resolve tenant scope
        if actor.tenant_id is None:
            # super admin
            tenant_id = data.tenant_id
            is_system_role = tenant_id is None
        else:
            # tenant admin
            if data.tenant_id and data.tenant_id != actor.tenant_id:
                raise AuthorizationError("Cannot create role for another tenant")

            tenant_id = actor.tenant_id
            is_system_role = False

        # 2️⃣ Validate tenant (if tenant role)
        if tenant_id:
            tenant = await self.tenant_repo.get_by_id(tenant_id)
            if not tenant:
                raise ResourceNotFound("Tenant not found")

        # 3️⃣ Enforce name uniqueness per scope
        existing = await self.role_repo.get_by_name_and_tenant(
            name=data.name,
            tenant_id=tenant_id,
        )
        if existing:
            raise ResourceConflict("Role with this name already exists")

        # 4️⃣ Validate permissions
        permissions = await self.permission_repo.get_by_ids(data.permission_ids)
        if len(permissions) != len(set(data.permission_ids)):
            raise ResourceNotFound("One or more permissions not found")

        # 5️⃣ Create role
        role = Role(
            name=data.name,
            description=data.description,
            tenant_id=tenant_id,
            is_system_role=is_system_role,
            permissions=permissions,
        )

        self.role_repo.session.add(role)
        await self.role_repo.session.flush()

        return role