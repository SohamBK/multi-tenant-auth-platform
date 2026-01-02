from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.api.deps.db import get_db
from app.infrastructure.clients.redis_client import redis_client
from app.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(tags=["Health"])


@router.get("/health")
async def health_check(db: AsyncSession = Depends(get_db)):
    checks = {
        "api": "ok",
        "database": "ok",
        "redis": "ok",
    }

    # ---- Database check ----
    try:
        await db.execute(text("SELECT 1"))
    except Exception as e:
        logger.error("Database health check failed", exc_info=e)
        checks["database"] = "error"

    # ---- Redis check ----
    try:
        await redis_client.ping()
    except Exception as e:
        logger.error("Redis health check failed", exc_info=e)
        checks["redis"] = "error"

    status = "ok" if all(v == "ok" for v in checks.values()) else "error"

    return {
        "status": status,
        "checks": checks,
    }
