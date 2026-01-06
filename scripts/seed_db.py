import asyncio
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.infrastructure.db.session import AsyncSessionLocal
from app.infrastructure.db.models.tenant import Tenant
from app.infrastructure.db.models.user import User
from app.infrastructure.db.models.user_auth_method import UserAuthMethod, AuthMethodType
from app.security.hashing import hash_password

async def seed_data():
    async with AsyncSessionLocal() as session:
        async with session.begin():
            # 1. Create a Test Tenant
            print("Checking for existing tenant...")
            result = await session.execute(select(Tenant).where(Tenant.name == "Test Corp"))
            tenant = result.scalar_one_or_none()
            
            if not tenant:
                tenant = Tenant(
                    id=uuid.uuid4(),
                    name="Test Corp",
                    tenant_status="active"
                )
                session.add(tenant)
                print(f"Created Tenant: {tenant.name}")

            # 2. Create a Super Admin User
            email = "admin@test.com"
            result = await session.execute(select(User).where(User.email == email))
            user = result.scalar_one_or_none()

            if not user:
                user = User(
                    id=uuid.uuid4(),
                    email=email,
                    first_name="Admin",
                    last_name="User",
                    user_status="active",
                    is_superuser=True,
                    tenant_id=tenant.id
                )
                session.add(user)
                
                # 3. Add Password Auth Method
                auth_method = UserAuthMethod(
                    user_id=user.id,
                    auth_type=AuthMethodType.PASSWORD,
                    password_hash=hash_password("admin1234") # Use a strong default for testing
                )
                session.add(auth_method)
                print(f"Created Super Admin: {email} / admin1234")
            else:
                print(f"User {email} already exists.")

    print("Seeding completed successfully!")

if __name__ == "__main__":
    asyncio.run(seed_data())