import asyncio
import uuid
from sqlalchemy import select

from app.infrastructure.db.session import AsyncSessionLocal
from app.infrastructure.db.models.tenant import Tenant
from app.infrastructure.db.models.user import User
from app.infrastructure.db.models.user_auth_method import UserAuthMethod, AuthMethodType
from app.infrastructure.db.models.auth_rbac import Role, Permission
from app.security.hashing import hash_password

# 1. Define Permissions with Wildcards
SYSTEM_PERMISSIONS = [
    # Wildcards
    {"slug": "users:*", "description": "Full control over all user actions"},
    {"slug": "roles:*", "description": "Full control over all role actions"},
    {"slug": "tenants:*", "description": "Full control over all tenant actions"},
    # Granular (for standard users)
    {"slug": "users:view", "description": "View user profiles"},
    {"slug": "billing:view", "description": "View tenant billing"},
]

async def seed_data():
    print("Connecting to database...")
    async with AsyncSessionLocal() as session:
        # session.begin() starts a transaction and commits automatically at the end
        async with session.begin():
            print("--- Transaction Started ---")
            
            # --- 1. SEED PERMISSIONS ---
            print("Seeding permissions...")
            permission_map = {}
            for p_data in SYSTEM_PERMISSIONS:
                res = await session.execute(select(Permission).where(Permission.slug == p_data["slug"]))
                perm = res.scalar_one_or_none()
                if not perm:
                    perm = Permission(**p_data)
                    session.add(perm)
                    print(f"  + Added permission: {p_data['slug']}")
                permission_map[p_data["slug"]] = perm
            await session.flush()

            # --- 2. SEED SYSTEM ROLES ---
            print("Seeding global roles...")
            # Super Admin
            res = await session.execute(select(Role).where(Role.name == "Super Admin", Role.tenant_id == None))
            super_admin_role = res.scalar_one_or_none()
            if not super_admin_role:
                super_admin_role = Role(
                    name="Super Admin",
                    description="Global system owner with full wildcard access",
                    is_system_role=True,
                    permissions=[permission_map["users:*"], permission_map["roles:*"], permission_map["tenants:*"]]
                )
                session.add(super_admin_role)
                print("  + Added Super Admin role")

            # --- 3. SEED TEST TENANT ---
            print("Seeding test tenant...")
            res = await session.execute(select(Tenant).where(Tenant.name == "Test Corp"))
            tenant = res.scalar_one_or_none()
            if not tenant:
                tenant = Tenant(name="Test Corp", tenant_status="active")
                session.add(tenant)
                print("  + Added Tenant: Test Corp")
            await session.flush()

            # --- 4. SEED GLOBAL ADMIN ---
            admin_email = "superadmin@system.com"
            print(f"Checking for admin: {admin_email}...")
            res = await session.execute(select(User).where(User.email == admin_email))
            super_admin = res.scalar_one_or_none()
            if not super_admin:
                super_admin = User(
                    email=admin_email,
                    first_name="System", last_name="Owner",
                    user_status="active",
                    tenant_id=None,
                    role_id=super_admin_role.id
                )
                session.add(super_admin)
                await session.flush()
                
                auth = UserAuthMethod(
                    user_id=super_admin.id,
                    auth_type=AuthMethodType.PASSWORD,
                    password_hash=hash_password("system123")
                )
                session.add(auth)
                print(f"  + Created Global Super Admin: {admin_email}")

    print("\n--- SEEDING COMPLETE ---")

if __name__ == "__main__":
    asyncio.run(seed_data())