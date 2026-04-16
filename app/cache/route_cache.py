from pydantic import json


class RouteCache:
    def __init__(self, redis):
        self.redis = redis
        self.ttl = 900  # 15 min

    def _key(self, building_id, floor, from_, to, accessible):
        return f"route:{building_id}:{floor}:{from_}:{to}:{accessible}"

    async def get(self, building_id, floor, from_, to, accessible):
        key = self._key(building_id, floor, from_, to, accessible)
        data = await self.redis.get(key)
        return json.loads(data) if data else None

    async def set(self, building_id, floor, from_, to, accessible, value):
        key = self._key(building_id, floor, from_, to, accessible)
        await self.redis.set(key, json.dumps(value), ex=self.ttl)