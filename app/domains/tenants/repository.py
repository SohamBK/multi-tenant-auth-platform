from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
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
