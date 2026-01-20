from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from sqlalchemy.orm import selectinload

from app.domains.shared.repository import BaseRepository
from app.infrastructure.db.models.auth_rbac import Role, Permission


class RoleRepository(BaseRepository[Role]):
    def __init__(self, session: AsyncSession):
        super().__init__(Role, session)

    async def get_by_ids(self, ids: list):
        if not ids:
            return []

        query = select(self.model).where(self.model.id.in_(ids))
        return (await self.session.execute(query)).scalars().all()

    async def list_visible_roles(self, tenant_id):
        query = (
            select(self.model)
            .options(selectinload(self.model.permissions))
            .order_by(self.model.name)
        )

        # 🔐 Tenant scoping
        if tenant_id is not None:
            query = query.where(
                or_(
                    self.model.tenant_id == tenant_id,
                    self.model.tenant_id.is_(None),
                )
            )

        return (await self.session.execute(query)).scalars().all()
    
    async def get_by_name_and_tenant(self, *, name: str, tenant_id):
        query = select(self.model).where(self.model.name == name)

        if tenant_id is None:
            query = query.where(self.model.tenant_id.is_(None))
        else:
            query = query.where(self.model.tenant_id == tenant_id)

        return (await self.session.execute(query)).scalar_one_or_none()
