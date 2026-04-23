import json
from typing import Any, Dict, Optional

from app.cache.redis_client import RedisClient


class RouteCache:
    def __init__(self, redis: RedisClient):
        self.redis = redis
        self.ttl_seconds = 900  # 15 min

    @staticmethod
    def _key(
        building_id: str,
        floor_id: str,
        lat: float,
        lng: float,
        poi_id: str,
        accessible: bool,
    ) -> str:
        return f"route:{building_id}:{floor_id}:{lat:.6f}:{lng:.6f}:{poi_id}:{accessible}"

    async def get(
        self,
        building_id: str,
        floor_id: str,
        lat: float,
        lng: float,
        poi_id: str,
        accessible: bool,
    ) -> Optional[Dict[str, Any]]:
        key = self._key(building_id, floor_id, lat, lng, poi_id, accessible)
        data = await self.redis.get(key)
        return json.loads(data) if data else None

    async def set(
        self,
        building_id: str,
        floor_id: str,
        lat: float,
        lng: float,
        poi_id: str,
        accessible: bool,
        value: Dict[str, Any],
    ) -> None:
        key = self._key(building_id, floor_id, lat, lng, poi_id, accessible)
        await self.redis.set(key, json.dumps(value), ttl=self.ttl_seconds)

    async def invalidate_building(self, building_id: str) -> int:
        return await self.redis.delete_prefix(f"route:{building_id}:")

    async def invalidate_floor(self, floor_id: str) -> int:
        return await self.redis.delete_pattern(f"route:*:{floor_id}:*")

    async def invalidate_all(self) -> int:
        return await self.redis.delete_prefix("route:")