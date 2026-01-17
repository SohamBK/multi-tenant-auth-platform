from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.sql import asc, desc

from uuid import UUID

from app.domains.shared.repository import BaseRepository
from app.infrastructure.db.models.tenant import Tenant


class TenantRepository(BaseRepository[Tenant]):
    def __init__(self, session: AsyncSession):
        super().__init__(Tenant, session)

    async def get_by_id(self, tenant_id: UUID):
        query = select(self.model).where(self.model.id == tenant_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_by_name(self, name:str) -> Tenant | None:
        result = await self.session.execute(
            select(self.model).where(self.model.name == name)
        )

        return result.scalar_one_or_none()
    

    async def create(self, *, name: str) -> Tenant:
        tenant = Tenant(
            name=name,
            tenant_status="active",
        )
        self.session.add(tenant)
        await self.session.flush()
        return tenant
    
    async def list_paginated(
        self,
        *,
        offset: int,
        limit: int,
        status: str | None,
        sort_by: str,
        sort_order: str,
    ) -> tuple[list[Tenant], int]:

        query = select(self.model)

        # 🔍 Filtering
        if status:
            query = query.where(self.model.tenant_status == status)

        # ↕ Sorting
        sort_column = getattr(self.model, sort_by)

        if sort_order == "asc":
            query = query.order_by(asc(sort_column))
        else:
            query = query.order_by(desc(sort_column))

        # Pagination
        query = query.offset(offset).limit(limit)

        tenants = (await self.session.execute(query)).scalars().all()

        # Count query
        count_query = select(func.count()).select_from(self.model)
        if status:
            count_query = count_query.where(self.model.tenant_status == status)

        total = (await self.session.execute(count_query)).scalar_one()

        return tenants, total
    
    async def update(self, tenant: Tenant) -> Tenant:
        self.session.add(tenant)
        await self.session.flush()
        return tenant
