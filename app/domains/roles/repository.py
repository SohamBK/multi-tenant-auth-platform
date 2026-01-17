from sqlalchemy.ext.asyncio import AsyncSession
from app.domains.shared.repository import BaseRepository
from app.infrastructure.db.models.auth_rbac import Role

class RoleRepository(BaseRepository[Role]):
    def __init__(self, session: AsyncSession):
        super().__init__(Role, session)
    async def get_by_id(self, role_id):
        return await super().get_by_id(role_id)
