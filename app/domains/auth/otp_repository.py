from typing import Optional
from redis.asyncio import Redis
from app.infrastructure.clients.redis_client import redis_client

class OTPRepository:
    def __init__(self, client: Redis = redis_client):
        self.client = client
        self.prefix = "otp:"

    async def store_otp(self, email: str, otp: str, expires_in: int = 300) -> None:
        """Stores OTP in Redis with an expiration (default 5 minutes)."""
        key = f"{self.prefix}{email}"
        await self.client.setex(key, expires_in, otp)

    async def get_otp(self, email: str) -> Optional[str]:
        """Retrieves OTP for a given email."""
        return await self.client.get(f"{self.prefix}{email}")

    async def delete_otp(self, email: str) -> None:
        """Removes OTP after successful verification (One-time use)."""
        await self.client.delete(f"{self.prefix}{email}")