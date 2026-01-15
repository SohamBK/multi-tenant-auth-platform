from app.domains.tenants.repository import TenantRepository
from app.domains.tenants.schemas import TenantCreateSchema
from app.core.exceptions import ResourceConflict


class TenantService:
    def __init__(self, tenant_repo: TenantRepository):
        self.tenant_repo = tenant_repo

    async def create_tenant(self, data: TenantCreateSchema):
        existing = await self.tenant_repo.get_by_name(data.name)
        if existing:
            raise ResourceConflict("Tenant with this name already exists")

        return await self.tenant_repo.create(name=data.name)
