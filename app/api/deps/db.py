from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession
from app.infrastructure.db.session import AsyncSessionLocal


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()   # ✅ COMMIT HERE
        except Exception:
            await session.rollback() # ✅ ROLLBACK ON ERROR
            raise
        finally:
            await session.close()

