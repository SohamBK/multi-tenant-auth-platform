from app.domains.rbac.permissions.repository import PermissionRepository


class PermissionService:
    def __init__(self, permission_repo: PermissionRepository):
        self.permission_repo = permission_repo

    async def list_permissions(self):
        return await self.permission_repo.list_all()

    async def get_permission(self, permission_id):
        return await self.permission_repo.get_by_id(permission_id)
