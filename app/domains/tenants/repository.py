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
