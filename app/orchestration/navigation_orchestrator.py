"""Navigation orchestration layer.

- delegate navigation calls to NavigationClient
- keep orchestration surface stable for future resilience/caching additions
"""

import logging
from typing import Any, Dict, List, Optional, Tuple

import httpx
from fastapi import HTTPException

from app.cache.position_cache import PositionCache
from app.cache.route_cache import RouteCache
from app.cache.redis_client import RedisClient
from app.clients.navigation_client import NavigationClient
from app.clients.positioning_client import PositioningClient

logger = logging.getLogger(__name__)


class NavigationOrchestrator:
    """Orchestrator for navigation flows.

    In phase one this class only delegates calls to the navigation client.
    """

    def __init__(
        self,
        redis_client: RedisClient,
        navigation_client: NavigationClient,
        positioning_client: PositioningClient,
    ):
        self.redis = redis_client
        self.position_cache = PositionCache(redis_client)
        self.route_cache = RouteCache(redis_client)
        self.navigation_client = navigation_client
        self.positioning_client = positioning_client

    @staticmethod
    def _extract_coordinates(positioning_response: Dict[str, Any]) -> Tuple[float, float]:
        # Accept both direct and nested shapes to avoid coupling to one payload format.
        if "lat" in positioning_response and "lng" in positioning_response:
            return float(positioning_response["lat"]), float(positioning_response["lng"])

        position_obj = positioning_response.get("position")
        if isinstance(position_obj, dict) and "lat" in position_obj and "lng" in position_obj:
            return float(position_obj["lat"]), float(position_obj["lng"])

        data_obj = positioning_response.get("data")
        if isinstance(data_obj, dict):
            if "lat" in data_obj and "lng" in data_obj:
                return float(data_obj["lat"]), float(data_obj["lng"])
            nested_position = data_obj.get("position")
            if isinstance(nested_position, dict) and "lat" in nested_position and "lng" in nested_position:
                return float(nested_position["lat"]), float(nested_position["lng"])

        raise ValueError("Positioning response did not include valid lat/lng")

    @staticmethod
    def _build_route_payload(
        floor_id: str,
        lat: float,
        lng: float,
        poi_id: str,
        accessible: bool,
    ) -> Dict[str, Any]:
        return {
            "from": {
                "floorId": floor_id,
                "lat": lat,
                "lng": lng,
            },
            "to": {
                "poiId": poi_id,
            },
            "options": {
                "accessible": accessible,
            },
        }

    async def _get_cached_route(
        self,
        building_id: str,
        floor_id: str,
        lat: float,
        lng: float,
        poi_id: str,
        accessible: bool,
    ) -> Optional[Dict[str, Any]]:
        cached_value = await self.route_cache.get(building_id, floor_id, lat, lng, poi_id, accessible)
        if cached_value is not None:
            logger.info("Cache hit")
        return cached_value

    async def calculate_route(
        self,
        from_building_id: str,
        from_floor_id: str,
        to_poi_id: str,
        user_id: Optional[str] = None,
        from_lat: Optional[float] = None,
        from_lng: Optional[float] = None,
        from_files: Optional[List[Any]] = None,
        accessible: bool = False,
    ) -> Dict[str, Any]:
        used_positioning = False
        warning: Optional[str] = None

        resolved_lat = from_lat
        resolved_lng = from_lng

        if resolved_lat is None or resolved_lng is None:
            if not from_files:
                raise HTTPException(
                    status_code=400,
                    detail="Missing location: provide lat/lng or files for positioning",
                )

            try:
                logger.info("Using positioning fallback", extra={"floor_id": from_floor_id})
                positioning_payload = {
                    "floorId": from_floor_id,
                    "files": from_files,
                }
                positioning_response = await self.positioning_client.predict(positioning_payload)
                resolved_lat, resolved_lng = self._extract_coordinates(positioning_response)
                used_positioning = True

                if user_id:
                    await self.position_cache.set(
                        user_id,
                        {
                            "floorId": from_floor_id,
                            "lat": resolved_lat,
                            "lng": resolved_lng,
                        },
                    )
            except HTTPException as exc:
                if user_id:
                    last_position = await self.position_cache.get(user_id)
                    if last_position and last_position.get("lat") is not None and last_position.get("lng") is not None:
                        resolved_lat = float(last_position["lat"])
                        resolved_lng = float(last_position["lng"])
                        warning = "position may be outdated"
                    else:
                        raise HTTPException(status_code=400, detail=f"Positioning failed: {exc.detail}") from exc
                else:
                    raise HTTPException(status_code=400, detail=f"Positioning failed: {exc.detail}") from exc
            except (ValueError, TypeError, KeyError) as exc:
                if user_id:
                    last_position = await self.position_cache.get(user_id)
                    if last_position and last_position.get("lat") is not None and last_position.get("lng") is not None:
                        resolved_lat = float(last_position["lat"])
                        resolved_lng = float(last_position["lng"])
                        warning = "position may be outdated"
                    else:
                        raise HTTPException(status_code=400, detail=f"Positioning failed: {str(exc)}") from exc
                else:
                    raise HTTPException(status_code=400, detail=f"Positioning failed: {str(exc)}") from exc
            except (httpx.RequestError, httpx.HTTPStatusError) as exc:
                if user_id:
                    last_position = await self.position_cache.get(user_id)
                    if last_position and last_position.get("lat") is not None and last_position.get("lng") is not None:
                        resolved_lat = float(last_position["lat"])
                        resolved_lng = float(last_position["lng"])
                        warning = "position may be outdated"
                    else:
                        raise HTTPException(status_code=400, detail="Positioning failed: downstream unavailable") from exc
                else:
                    raise HTTPException(status_code=400, detail="Positioning failed: downstream unavailable") from exc

        cached_route = await self._get_cached_route(
            building_id=from_building_id,
            floor_id=from_floor_id,
            lat=resolved_lat,
            lng=resolved_lng,
            poi_id=to_poi_id,
            accessible=accessible,
        )
        if cached_route is not None:
            response = {
                "route": cached_route,
                "meta": {
                    "source": "cache",
                    "usedPositioning": used_positioning,
                },
            }
            if warning:
                response["warning"] = warning
            return response

        payload = self._build_route_payload(
            floor_id=from_floor_id,
            lat=resolved_lat,
            lng=resolved_lng,
            poi_id=to_poi_id,
            accessible=accessible,
        )

        try:
            route_response = await self.navigation_client.calculate_route(payload)
            await self.route_cache.set(
                building_id=from_building_id,
                floor_id=from_floor_id,
                lat=resolved_lat,
                lng=resolved_lng,
                poi_id=to_poi_id,
                accessible=accessible,
                value=route_response,
            )
            response = {
                "route": route_response,
                "meta": {
                    "source": "live",
                    "usedPositioning": used_positioning,
                },
            }
            if warning:
                response["warning"] = warning
            return response
        except HTTPException as exc:
            if exc.status_code < 500:
                raise

            fallback = await self._get_cached_route(
                building_id=from_building_id,
                floor_id=from_floor_id,
                lat=resolved_lat,
                lng=resolved_lng,
                poi_id=to_poi_id,
                accessible=accessible,
            )
            if fallback is not None:
                logger.warning("Navigation failed, using fallback")
                response = {
                    "route": fallback,
                    "meta": {
                        "source": "cache",
                        "usedPositioning": used_positioning,
                    },
                }
                response["warning"] = warning or "served cached route due to navigation failure"
                return response
            raise HTTPException(status_code=503, detail="Navigation service unavailable") from exc
        except (httpx.RequestError, httpx.HTTPStatusError) as exc:
            fallback = await self._get_cached_route(
                building_id=from_building_id,
                floor_id=from_floor_id,
                lat=resolved_lat,
                lng=resolved_lng,
                poi_id=to_poi_id,
                accessible=accessible,
            )
            if fallback is not None:
                logger.warning("Navigation failed, using fallback")
                response = {
                    "route": fallback,
                    "meta": {
                        "source": "cache",
                        "usedPositioning": used_positioning,
                    },
                }
                response["warning"] = warning or "served cached route due to navigation failure"
                return response
            raise HTTPException(status_code=503, detail="Navigation service unavailable") from exc
