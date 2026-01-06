from typing import Optional
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.domains.shared.repository import BaseRepository
from app.infrastructure.db.models.user import User

from sqlalchemy.ext.asyncio import AsyncSession

class UserRepository(BaseRepository[User]):
    def __init__(self, session: AsyncSession):
        super().__init__(User, session)

    async def get_by_email(self, email: str) -> Optional[User]:
        """
        Find a user by email globally for login.
        Eagerly loads related tenant and auth methods to avoid N+1 queries.
        """
        # selectinload() issues a separate query with an IN clause,
        # which is more efficient for collections like auth_methods.
        query = (
            select(User)
            .where(User.email == email)
            .options(
                selectinload(User.tenant),
                selectinload(User.auth_methods)
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()