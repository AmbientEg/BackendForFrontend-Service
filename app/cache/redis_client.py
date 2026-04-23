"""Redis client wrapper for async cache operations."""

import logging
from typing import Any, Optional

import redis.asyncio as redis
from redis.exceptions import RedisError


logger = logging.getLogger(__name__)


class RedisClient:
    """Async Redis client for caching layer.
    
    Wraps redis.asyncio with a clean interface for BFF cache operations.
    Used by orchestration layer for response caching, position tracking, etc.
    """

    def __init__(self, url: str):
        """Initialize Redis client from connection URL.
        
        Args:
            url: Redis connection URL (e.g., "redis://localhost:6379/0")
        """
        self.client = redis.from_url(url, decode_responses=True)

    async def get(self, key: str) -> Optional[str]:
        """Retrieve value from cache by key.
        
        Args:
            key: Cache key to retrieve
            
        Returns:
            Cached value as string, or None if key doesn't exist
        """
        try:
            return await self.client.get(key)
        except (RedisError, OSError) as exc:
            logger.warning("Redis GET failed for %s: %s", key, exc)
            return None

    async def set(self, key: str, value: str, ttl: Optional[int] = None) -> None:
        """Store value in cache with optional TTL.
        
        Args:
            key: Cache key to store value under
            value: Value to cache (will be stored as string)
            ttl: Time-to-live in seconds (None = no expiration)
        """
        try:
            await self.client.set(key, value, ex=ttl)
        except (RedisError, OSError) as exc:
            logger.warning("Redis SET failed for %s: %s", key, exc)

    async def delete(self, key: str) -> None:
        """Delete value from cache.
        
        Args:
            key: Cache key to delete
        """
        try:
            await self.client.delete(key)
        except (RedisError, OSError) as exc:
            logger.warning("Redis DELETE failed for %s: %s", key, exc)

    async def delete_prefix(self, prefix: str) -> int:
        """Delete all keys that start with the provided prefix.

        Args:
            prefix: Key prefix to invalidate (e.g., "route:building-1:")

        Returns:
            Number of deleted keys.
        """
        return await self.delete_pattern(f"{prefix}*")

    async def delete_pattern(self, pattern: str) -> int:
        """Delete all keys matching a Redis glob pattern."""
        deleted = 0
        try:
            async for key in self.client.scan_iter(match=pattern):
                deleted += await self.client.delete(key)
            return int(deleted)
        except (RedisError, OSError) as exc:
            logger.warning("Redis pattern delete failed for %s: %s", pattern, exc)
            return 0

    async def close(self) -> None:
        """Close Redis connection gracefully.
        
        Should be called during app shutdown.
        """
        try:
            await self.client.close()
        except (RedisError, OSError) as exc:
            logger.warning("Redis close failed: %s", exc)
