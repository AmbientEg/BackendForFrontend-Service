import json
from typing import Any, Dict, Optional

from app.cache.redis_client import RedisClient


class PositionCache:
    def __init__(self, redis: RedisClient):
        self.redis = redis
        self.ttl_seconds = 1

    @staticmethod
    def _key(user_id: str) -> str:
        return f"position:{user_id}"

    async def get(self, user_id: str) -> Optional[Dict[str, Any]]:
        cached_raw = await self.redis.get(self._key(user_id))
        return json.loads(cached_raw) if cached_raw else None

    async def set(self, user_id: str, value: Dict[str, Any]) -> None:
        await self.redis.set(self._key(user_id), json.dumps(value), ttl=self.ttl_seconds)

    async def delete(self, user_id: str) -> None:
        await self.redis.delete(self._key(user_id))