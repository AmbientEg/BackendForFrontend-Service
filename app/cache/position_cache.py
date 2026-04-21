class PositionCache:
    def __init__(self, redis):
        self.redis = redis
        self.ttl = 1  # seconds

    def _key(self, user_id):
        return f"position:{user_id}"

    async def get(self, user_id):
        return await self.redis.get(self._key(user_id))

    async def set(self, user_id, value):
        await self.redis.set(self._key(user_id), value, ex=self.ttl)