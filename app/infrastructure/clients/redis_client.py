from redis.asyncio import Redis
from redis.asyncio.connection import ConnectionPool

from app.core.config import settings

# Connection pool (created once)
redis_pool = ConnectionPool.from_url(
    settings.REDIS_URL,
    max_connections=settings.REDIS_MAX_CONNECTIONS,
    decode_responses=True,  # strings instead of bytes
)

# Redis client
redis_client = Redis(connection_pool=redis_pool)