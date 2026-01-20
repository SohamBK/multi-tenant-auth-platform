from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.domains.shared.repository import BaseRepository
from app.infrastructure.db.models.auth_rbac import Permission


class PermissionRepository(BaseRepository[Permission]):
    def __init__(self, session: AsyncSession):
        super().__init__(Permission, session)

    async def list_all(self) -> list[Permission]:
        query = select(self.model).order_by(self.model.slug)
        return (await self.session.execute(query)).scalars().all()
    
    async def get_by_id(self, permission_id) -> Permission | None:
        query = select(self.model).where(self.model.id == permission_id)
        result = await self.session.execute(query)
        return result.scalars().first()
    
    async def get_by_ids(self, ids: list) -> list[Permission]:
        if not ids:
            return []

        query = select(self.model).where(self.model.id.in_(ids))
        return (await self.session.execute(query)).scalars().all()
