from app.domains.tenants.repository import TenantRepository
from app.domains.tenants.schemas import TenantCreateSchema, TenantResponseSchema, TenantUpdateSchema
from app.domains.tenants.query_params import TenantListParams
from app.core.exceptions import ResourceConflict, ResourceNotFound
from app.domains.shared.schemas.pagination import PaginatedData, PaginationMeta, PaginationParams

class TenantService:
    def __init__(self, tenant_repo: TenantRepository):
        self.tenant_repo = tenant_repo

    async def create_tenant(self, data: TenantCreateSchema):
        existing = await self.tenant_repo.get_by_name(data.name)
        if existing:
            raise ResourceConflict("Tenant with this name already exists")

        return await self.tenant_repo.create(name=data.name)
    
    async def list_tenants(
        self,
        *,
        params: TenantListParams,
    ) -> PaginatedData[TenantResponseSchema]:

        tenants, total = await self.tenant_repo.list_paginated(
            offset=params.offset,
            limit=params.limit,
            status=params.status,
            sort_by=params.sort_by,
            sort_order=params.sort_order,
        )

        items = [
            TenantResponseSchema.model_validate(t)
            for t in tenants
        ]

        pagination = PaginationMeta.create(
            page=params.page,
            page_size=params.page_size,
            total_items=total,
        )

        return PaginatedData(items=items, pagination=pagination)
    
    async def update_tenant(
        self,
        tenant_id,
        data: TenantUpdateSchema,
    ):
        tenant = await self.tenant_repo.get_by_id(tenant_id)
        if not tenant:
            raise ResourceNotFound("Tenant not found")
        
        tenant.name = data.name

        return await self.tenant_repo.update(tenant)
    
    async def deactivate_tenant(
        self,
        tenant_id
    ):
        tenant = await self.tenant_repo.get_by_id(tenant_id)
        if not tenant:
            raise ResourceNotFound("Tenant not found")
        
        tenant.tenant_status = "inactive"

        return await self.tenant_repo.update(tenant)
    
    async def reactivate_tenant(self, tenant_id):
        tenant = await self.tenant_repo.get_by_id(tenant_id)
        if not tenant:
            raise ResourceNotFound("Tenant not found")

        if tenant.tenant_status == "active":
            return tenant  # idempotent

        tenant.tenant_status = "active"
        return await self.tenant_repo.update(tenant)