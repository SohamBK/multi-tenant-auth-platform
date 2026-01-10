from typing import Optional
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.shared.repository import BaseRepository
from app.infrastructure.db.models.user import User
from app.infrastructure.db.models.auth_rbac import Role


class UserRepository(BaseRepository[User]):
    def __init__(self, session: AsyncSession):
        super().__init__(User, session)

    async def get_by_id(self, id: UUID, tenant_id: Optional[UUID] = None) -> Optional[User]:
        """
        Fetch a user with Role and Permissions eager-loaded.
        This prevents N+1 queries during the permission check process.
        """
        query = (
            select(self.model)
            .options(
                selectinload(self.model.role)
                .selectinload(Role.permissions)
            )
            .where(self.model.id == id)
        )

        # Enforce tenant isolation
        if tenant_id and hasattr(self.model, "tenant_id"):
            query = query.where(self.model.tenant_id == tenant_id)

        result = await self.session.execute(query)
        return result.unique().scalar_one_or_none()
