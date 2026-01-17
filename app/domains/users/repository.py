from typing import Optional
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.shared.repository import BaseRepository
from app.infrastructure.db.models.user import User
from app.infrastructure.db.enums import UserStatus
from app.infrastructure.db.models.auth_rbac import Role
from app.infrastructure.db.models.user_auth_method import UserAuthMethod


class UserRepository(BaseRepository[User]):
    def __init__(self, session: AsyncSession):
        super().__init__(User, session)

    async def get_by_id(
        self,
        id: UUID,
        tenant_id: Optional[UUID] = None
    ) -> Optional[User]:
        query = (
            select(self.model)
            .options(
                selectinload(self.model.role)
                .selectinload(Role.permissions),
                selectinload(self.model.auth_methods),
                selectinload(self.model.tenant)
            )
            .where(self.model.id == id)
        )

        if tenant_id is not None and hasattr(self.model, "tenant_id"):
            query = query.where(self.model.tenant_id == tenant_id)

        result = await self.session.execute(query)
        return result.unique().scalar_one_or_none()

    async def get_by_email(
        self,
        email: str,
        tenant_id: Optional[UUID] = None
    ) -> Optional[User]:
        query = (
            select(self.model)
            .options(
                selectinload(self.model.role)
                .selectinload(Role.permissions),
                selectinload(self.model.auth_methods),
            )
            .where(self.model.email == email)
        )

        if tenant_id is not None and hasattr(self.model, "tenant_id"):
            query = query.where(self.model.tenant_id == tenant_id)

        result = await self.session.execute(query)
        return result.unique().scalar_one_or_none()
    
    async def create(
        self,
        *,
        email: str,
        first_name: str,
        last_name: str,
        role_id: UUID,
        tenant_id: Optional[UUID] = None
    ) -> User:
        new_user = User(
            email=email,
            first_name=first_name,
            last_name=last_name,
            role_id=role_id,
            tenant_id=tenant_id,
            user_status=UserStatus.ACTIVE,
        )        

        self.session.add(new_user)
        await self.session.flush()
        return new_user
