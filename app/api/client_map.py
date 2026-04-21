"""Mobile client map API endpoints.

Read-focused endpoints used by mobile clients to fetch building floors,
floor map data, and floor POIs.
"""

import json
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException

from app.clients.navigation_client import NavigationClient


router = APIRouter(tags=["client-map"])


async def get_navigation_client() -> NavigationClient:
	from app.main import navigation_client

	if not navigation_client:
		raise HTTPException(status_code=503, detail="Service initialization failed")

	return navigation_client


def _cache_key(prefix: str, item_id: str) -> str:
	return f"client-map:{prefix}:{item_id}"


async def _fetch_with_cache(cache_key: str, fetcher) -> Dict[str, Any]:
	from app.main import redis_client

	cached_value = None
	if redis_client:
		cached_raw = await redis_client.get(cache_key)
		if cached_raw:
			cached_value = json.loads(cached_raw)

	try:
		fresh_value = await fetcher()
		if redis_client:
			await redis_client.set(cache_key, json.dumps(fresh_value), ttl=120)
		return fresh_value
	except HTTPException as exc:
		if exc.status_code >= 500 and cached_value is not None:
			return cached_value
		raise


@router.get("/buildings/{building_id}/floors", summary="Get Building Floors")
async def get_building_floors(
	building_id: str,
	client: NavigationClient = Depends(get_navigation_client),
) -> Dict[str, Any]:
	cache_key = _cache_key("building-floors", building_id)
	data = await _fetch_with_cache(cache_key, lambda: client.get_building_floors(building_id))
	return {"data": data}


@router.get("/floors/{floor_id}/map", summary="Get Floor Map")
async def get_floor_map(
	floor_id: str,
	client: NavigationClient = Depends(get_navigation_client),
) -> Dict[str, Any]:
	cache_key = _cache_key("floor-map", floor_id)
	data = await _fetch_with_cache(cache_key, lambda: client.get_floor_map(floor_id))
	return {"data": data}


@router.get("/admin/pois/floor/{floor_id}", summary="Get Floor POIs")
async def get_floor_pois(
	floor_id: str,
	client: NavigationClient = Depends(get_navigation_client),
) -> Dict[str, Any]:
	cache_key = _cache_key("floor-pois", floor_id)
	data = await _fetch_with_cache(cache_key, lambda: client.get_floor_pois(floor_id))
	return {"data": data}

