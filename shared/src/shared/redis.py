"""Async Redis client wrapper."""

import json
from typing import TYPE_CHECKING, Any, Optional
from uuid import UUID

import redis.asyncio as aioredis
from redis.asyncio import Redis

if TYPE_CHECKING:
    from shared.settings import RedisSettings
else:
    from shared import settings

    RedisSettings = settings.RedisSettings


class RedisClient:
    """Async Redis client with helper methods."""

    def __init__(self, settings: "RedisSettings"):
        """
        Initialize Redis client.

        Args:
            settings: Redis settings
        """
        self.settings = settings
        self.client: Optional[Redis] = None

    async def connect(self) -> None:
        """Connect to Redis."""
        if self.client is None:
            self.client = await aioredis.from_url(
                self.settings.redis_url,
                encoding="utf-8",
                decode_responses=True,
                max_connections=self.settings.max_connections,
            )

    async def disconnect(self) -> None:
        """Disconnect from Redis."""
        if self.client:
            await self.client.close()
            self.client = None

    async def get(self, key: str) -> Optional[str]:
        """
        Get value by key.

        Args:
            key: Redis key

        Returns:
            Value or None if not found
        """
        if not self.client:
            await self.connect()
        return await self.client.get(key)

    async def set(
        self,
        key: str,
        value: Any,
        ex: Optional[int] = None,
        nx: bool = False,
    ) -> bool:
        """
        Set key-value pair.

        Args:
            key: Redis key
            value: Value to set (will be JSON serialized if not string)
            ex: Expiration time in seconds
            nx: Only set if key doesn't exist

        Returns:
            True if set successfully
        """
        if not self.client:
            await self.connect()

        if not isinstance(value, str):
            value = json.dumps(value)

        return await self.client.set(key, value, ex=ex, nx=nx)

    async def delete(self, *keys: str) -> int:
        """
        Delete keys.

        Args:
            *keys: Keys to delete

        Returns:
            Number of keys deleted
        """
        if not self.client:
            await self.connect()
        return await self.client.delete(*keys)

    async def exists(self, *keys: str) -> int:
        """
        Check if keys exist.

        Args:
            *keys: Keys to check

        Returns:
            Number of existing keys
        """
        if not self.client:
            await self.connect()
        return await self.client.exists(*keys)

    async def expire(self, key: str, time: int) -> bool:
        """
        Set expiration time for key.

        Args:
            key: Redis key
            time: Expiration time in seconds

        Returns:
            True if expiration was set
        """
        if not self.client:
            await self.connect()
        return await self.client.expire(key, time)

    async def get_json(self, key: str) -> Optional[Any]:
        """
        Get and deserialize JSON value.

        Args:
            key: Redis key

        Returns:
            Deserialized value or None
        """
        value = await self.get(key)
        if value is None:
            return None
        return json.loads(value)

    async def set_json(
        self,
        key: str,
        value: Any,
        ex: Optional[int] = None,
        nx: bool = False,
    ) -> bool:
        """
        Serialize and set JSON value.

        Args:
            key: Redis key
            value: Value to serialize and set
            ex: Expiration time in seconds
            nx: Only set if key doesn't exist

        Returns:
            True if set successfully
        """
        return await self.set(key, json.dumps(value), ex=ex, nx=nx)

    def make_key(self, *parts: str, tenant_id: Optional[UUID] = None) -> str:
        """
        Create Redis key with tenant prefix.

        Args:
            *parts: Key parts
            tenant_id: Optional tenant ID for multi-tenancy

        Returns:
            Formatted Redis key
        """
        key_parts = [self.settings.key_prefix]
        if tenant_id:
            key_parts.append(f"tenant:{tenant_id}")
        key_parts.extend(str(part) for part in parts)
        return ":".join(key_parts)

    async def health_check(self) -> bool:
        """
        Check Redis connection health.

        Returns:
            True if connection is healthy
        """
        try:
            if not self.client:
                await self.connect()
            await self.client.ping()
            return True
        except Exception:
            return False


# Global Redis client instance
redis_client: Optional[RedisClient] = None


def get_redis() -> RedisClient:
    """
    Get global Redis client instance.

    Returns:
        RedisClient instance

    Raises:
        RuntimeError: If Redis client not initialized
    """
    if redis_client is None:
        raise RuntimeError("Redis client not initialized. Call init_redis() first.")
    return redis_client


def init_redis(settings: "RedisSettings") -> RedisClient:
    """
    Initialize global Redis client.

    Args:
        settings: Redis settings

    Returns:
        RedisClient instance
    """
    global redis_client
    redis_client = RedisClient(settings)
    return redis_client

