"""Redis client wrapper for async cache operations."""

from typing import Any, Optional

import redis.asyncio as redis


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
        return await self.client.get(key)

    async def set(self, key: str, value: str, ttl: Optional[int] = None) -> None:
        """Store value in cache with optional TTL.
        
        Args:
            key: Cache key to store value under
            value: Value to cache (will be stored as string)
            ttl: Time-to-live in seconds (None = no expiration)
        """
        await self.client.set(key, value, ex=ttl)

    async def delete(self, key: str) -> None:
        """Delete value from cache.
        
        Args:
            key: Cache key to delete
        """
        await self.client.delete(key)

    async def close(self) -> None:
        """Close Redis connection gracefully.
        
        Should be called during app shutdown.
        """
        await self.client.close()
