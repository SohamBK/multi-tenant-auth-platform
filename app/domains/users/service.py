from uuid import UUID
from app.domains.users.repository import UserRepository
from app.domains.users.schemas import UserCreateSchema
from app.core.exceptions import ResourceConflict, AuthorizationError


class UserService:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    async def create_user(
        self,
        *,
        data: UserCreateSchema,
        actor,  # current_user
    ):
        # 1️⃣ Email uniqueness (global)
        existing = await self.user_repo.get_by_email(data.email)
        if existing:
            raise ResourceConflict("User with this email already exists")

        # 2️⃣ Resolve tenant context
        if actor.tenant_id is None:
            tenant_id = data.tenant_id  # may be None or UUID
        else:
            if data.tenant_id and data.tenant_id != actor.tenant_id:
                raise AuthorizationError("Cannot create user for another tenant")

            tenant_id = actor.tenant_id

        # 3️⃣ Create user
        user = await self.user_repo.create(
            email=data.email,
            first_name=data.first_name,
            last_name=data.last_name,
            role_id=data.role_id,
            tenant_id=tenant_id,
        )

        return user
