from datetime import timedelta
from app.infrastructure.clients.redis_client import redis_client
from app.core.exceptions import AuthenticationError

class RateLimiter:
    def __init__(self, key_prefix: str, limit: int, window_seconds: int):
        """
        :param key_prefix: Unique name (e.g., 'otp_limit')
        :param limit: Max requests allowed
        :param window_seconds: Time window before reset
        """
        self.client = redis_client
        self.key_prefix = key_prefix
        self.limit = limit
        self.window_seconds = window_seconds

    async def check_limit(self, identifier: str):
        """
        Checks if the identifier (email/IP) has exceeded the limit.
        """
        key = f"rl:{self.key_prefix}:{identifier}"
        
        # 1. INCR increments the number in Redis by 1.
        # If the key doesn't exist, Redis creates it and sets it to 1.
        current_count = await self.client.incr(key)
        
        # 2. If it's the first request in this window, set the expiration.
        if current_count == 1:
            await self.client.expire(key, self.window_seconds)
            
        # 3. If count exceeds limit, block the request.
        if current_count > self.limit:
            # TTL tells us how many seconds are left until the limit resets.
            retry_after = await self.client.ttl(key)
            raise AuthenticationError(
                f"Too many requests. Please try again in {retry_after} seconds."
            )