"""Navigation orchestration layer.

Phase-1 behavior:
- delegate navigation calls to NavigationClient
- keep orchestration surface stable for future resilience/caching additions
"""

import logging
from typing import Any, Dict

from app.cache.redis_client import RedisClient
from app.clients.navigation_client import NavigationClient

logger = logging.getLogger(__name__)


class NavigationOrchestrator:
    """Orchestrator for navigation flows.

    In phase one this class only delegates calls to the navigation client.
    """

    def __init__(self, redis_client: RedisClient, navigation_client: NavigationClient):
        self.redis = redis_client
        self.navigation_client = navigation_client

    async def calculate_route(
        self,
        from_floor_id: str,
        from_lat: float,
        from_lng: float,
        to_poi_id: str,
        accessible: bool = False,
    ) -> Dict[str, Any]:
        # Check cache first
        # check route cache class

        # if does not exist, call navigation service

        # then persist baaa in cache and return response
        
        payload = {
            "from": {
                "floorId": from_floor_id,
                "lat": from_lat,
                "lng": from_lng,
            },
            "to": {
                "poiId": to_poi_id,
            },
            "options": {
                "accessible": accessible,
            },
        }
        return await self.navigation_client.calculate_route(payload)
