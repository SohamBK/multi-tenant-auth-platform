from app.domains.rbac.roles.repository import RoleRepository
from app.domains.tenants.repository import TenantRepository
from app.domains.rbac.permissions.repository import PermissionRepository
from app.domains.rbac.roles.schemas import RoleCreateSchema, RoleUpdateSchema, RolePermissionAttachSchema
from app.infrastructure.db.models.auth_rbac import Role
from app.core.exceptions import ResourceConflict, ResourceNotFound, AuthorizationError
from app.core.logging import get_logger

logger = get_logger(__name__)
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
    
    async def update_role(self, *, role_id, data: RoleUpdateSchema, actor):
        role = await self.role_repo.get_visible_role_by_id(
            role_id=role_id,
            tenant_id=actor.tenant_id,
        )

        if not role:
            raise ResourceNotFound("Role not found")

        # 🔒 System role protection
        if role.is_system_role and actor.tenant_id is not None:
            raise AuthorizationError("Cannot modify system role")

        # 🔒 Tenant boundary
        if role.tenant_id != actor.tenant_id and actor.tenant_id is not None:
            raise AuthorizationError("Cannot modify role outside tenant")

        # 🔁 Name uniqueness
        if data.name and data.name != role.name:
            existing = await self.role_repo.get_by_name_and_tenant(
                name=data.name,
                tenant_id=role.tenant_id,
            )
            if existing:
                raise ResourceConflict("Role name already exists")

            role.name = data.name

        if data.description is not None:
            role.description = data.description

        await self.role_repo.session.flush()
        return role
    
    async def delete_role(self, *, role_id, actor):
        role = await self.role_repo.get_visible_role_by_id(
            role_id=role_id,
            tenant_id=actor.tenant_id,
        )

        if not role:
            raise ResourceNotFound("Role not found")

        if role.is_system_role and actor.tenant_id is not None:
            raise AuthorizationError("Cannot delete system role")

        if await self.role_repo.is_role_in_use(role.id):
            logger.debug(f"Role {role.id} is assigned to users")
            raise AuthorizationError("Role is assigned to users")

        role.is_active = False
        await self.role_repo.session.flush()
        return role

    async def reactivate_role(self, *, role_id, actor):
        role = await self.role_repo.get_visible_role_by_id(
            role_id=role_id,
            tenant_id=actor.tenant_id,
        )

        if not role:
            raise ResourceNotFound("Role not found")

        # 🔒 System role protection
        if role.is_system_role and actor.tenant_id is not None:
            raise AuthorizationError("Cannot reactivate system role")

        # 🔒 Tenant boundary
        if role.tenant_id != actor.tenant_id and actor.tenant_id is not None:
            raise AuthorizationError("Cannot reactivate role outside tenant")

        # 🔁 Already active?
        if role.is_active:
            raise ResourceConflict("Role is already active")

        role.is_active = True
        await self.role_repo.session.flush()

        return role
    
    async def attach_permissions(
        self,
        *,
        role_id,
        data: RolePermissionAttachSchema,
        actor,
    ):
        role = await self.role_repo.get_visible_role_by_id(
            role_id=role_id,
            tenant_id=actor.tenant_id,
        )

        if not role:
            raise ResourceNotFound("Role not found")

        if not role.is_active:
            raise AuthorizationError("Cannot modify inactive role")

        # 🔒 System role protection
        if role.is_system_role and actor.tenant_id is not None:
            raise AuthorizationError("Cannot modify system role")

        role = await self.role_repo.get_role_with_permissions(role.id)

        permissions = await self.permission_repo.get_by_ids(data.permission_ids)
        if len(permissions) != len(set(data.permission_ids)):
            raise ResourceNotFound("One or more permissions not found")

        existing_ids = {p.id for p in role.permissions}
        new_permissions = [p for p in permissions if p.id not in existing_ids]

        if not new_permissions:
            raise ResourceConflict("Permissions already attached")

        role.permissions.extend(new_permissions)
        await self.role_repo.session.flush()

        return role, new_permissions

    async def detach_permission(
        self,
        *,
        role_id,
        permission_id,
        actor,
    ):
        role = await self.role_repo.get_visible_role_by_id(
            role_id=role_id,
            tenant_id=actor.tenant_id,
        )

        if not role:
            raise ResourceNotFound("Role not found")

        if not role.is_active:
            raise AuthorizationError("Cannot modify inactive role")

        if role.is_system_role and actor.tenant_id is not None:
            raise AuthorizationError("Cannot modify system role")

        role = await self.role_repo.get_role_with_permissions(role.id)

        permission = next(
            (p for p in role.permissions if p.id == permission_id), None
        )
        if not permission:
            raise ResourceNotFound("Permission not attached to role")

        role.permissions.remove(permission)
        await self.role_repo.session.flush()

        return role, permission