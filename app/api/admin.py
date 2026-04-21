"""Navigation admin API endpoints.

Phase-1 behavior:
- expose navigation-service admin endpoints through the BFF
- bypass orchestration for admin flows
- forward payloads and return raw responses
"""

import logging
from typing import Any, Dict

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pydantic import BaseModel, ConfigDict

from app.cache.route_cache import RouteCache
from app.clients.nav_client_admin import NavigationAdminClient
from app.clients.positioning_admin_client import PositioningAdminClient
from app.security.auth_middleware import require_admin

logger = logging.getLogger(__name__)

router = APIRouter(tags=["admin"], dependencies=[Depends(require_admin)])


class AdminPayload(BaseModel):
	model_config = ConfigDict(extra="allow")


async def get_navigation_admin_client() -> NavigationAdminClient:
    """Resolve the shared admin navigation client from app state without circular imports."""
    from app.main import navigation_admin_client

    if not navigation_admin_client:
        raise HTTPException(status_code=503, detail="Service initialization failed")

    return navigation_admin_client


async def get_positioning_admin_client() -> PositioningAdminClient:
	from app.main import positioning_admin_client

	if not positioning_admin_client:
		raise HTTPException(status_code=503, detail="Service initialization failed")

	return positioning_admin_client


async def _get_route_cache() -> RouteCache:
	from app.main import redis_client
	if not redis_client:
		raise HTTPException(status_code=503, detail="Service initialization failed")
	return RouteCache(redis_client)


@router.post("/buildings")
async def create_building(
	payload: AdminPayload,
	client: NavigationAdminClient = Depends(get_navigation_admin_client),
) -> Dict[str, Any]:
	return {"data": await client.create_building(payload.model_dump(exclude_none=True))}


@router.get("/buildings/{building_id}")
async def get_building(
	building_id: str,
	client: NavigationAdminClient = Depends(get_navigation_admin_client),
) -> Dict[str, Any]:
	return {"data": await client.get_building(building_id)}


@router.post("/floors")
async def create_floor(
	payload: AdminPayload,
	client: NavigationAdminClient = Depends(get_navigation_admin_client),
	route_cache: RouteCache = Depends(_get_route_cache),
) -> Dict[str, Any]:
	result = await client.create_floor(payload.model_dump(exclude_none=True))
	building_id = payload.model_dump(exclude_none=True).get("buildingId") or payload.model_dump(exclude_none=True).get("building_id")
	if building_id:
		try:
			await route_cache.invalidate_building(str(building_id))
		except Exception:
			logger.warning("Failed to invalidate route cache for building on create_floor", exc_info=True)
	return {"data": result}


@router.put("/floors/{floor_id}")
async def update_floor(
	floor_id: str,
	payload: AdminPayload,
	client: NavigationAdminClient = Depends(get_navigation_admin_client),
	route_cache: RouteCache = Depends(_get_route_cache),
) -> Dict[str, Any]:
	result = await client.update_floor(floor_id, payload.model_dump(exclude_none=True))
	try:
		await route_cache.invalidate_floor(floor_id)
	except Exception:
		logger.warning("Failed to invalidate route cache for floor on update_floor", exc_info=True)
	return {"data": result}


@router.post("/graphs/rebuild/{building_id}")
async def rebuild_graph_preview(
	building_id: str,
	client: NavigationAdminClient = Depends(get_navigation_admin_client),
	route_cache: RouteCache = Depends(_get_route_cache),
) -> Dict[str, Any]:
	result = await client.rebuild_graph_preview(building_id)
	try:
		await route_cache.invalidate_building(building_id)
	except Exception:
		logger.warning("Failed to invalidate route cache on graph rebuild", exc_info=True)
	return {"data": result}


@router.post("/graphs/confirm/{building_id}")
async def confirm_graph(
	building_id: str,
	client: NavigationAdminClient = Depends(get_navigation_admin_client),
	route_cache: RouteCache = Depends(_get_route_cache),
) -> Dict[str, Any]:
	result = await client.confirm_graph(building_id)
	try:
		await route_cache.invalidate_building(building_id)
	except Exception:
		logger.warning("Failed to invalidate route cache on graph confirm", exc_info=True)
	return {"data": result}


@router.post("/graphs/rollback/{building_id}")
async def rollback_graph(
	building_id: str,
	client: NavigationAdminClient = Depends(get_navigation_admin_client),
	route_cache: RouteCache = Depends(_get_route_cache),
) -> Dict[str, Any]:
	result = await client.rollback_graph(building_id)
	try:
		await route_cache.invalidate_building(building_id)
	except Exception:
		logger.warning("Failed to invalidate route cache on graph rollback", exc_info=True)
	return {"data": result}


@router.put("/admin/pois/{poi_id}")
async def update_poi(
	poi_id: str,
	payload: AdminPayload,
	client: NavigationAdminClient = Depends(get_navigation_admin_client),
	route_cache: RouteCache = Depends(_get_route_cache),
) -> Dict[str, Any]:
	payload_data = payload.model_dump(exclude_none=True)
	result = await client.update_poi(poi_id, payload_data)

	building_id = payload_data.get("buildingId") or payload_data.get("building_id")
	floor_id = payload_data.get("floorId") or payload_data.get("floor_id")

	try:
		if building_id:
			await route_cache.invalidate_building(str(building_id))
		elif floor_id:
			await route_cache.invalidate_floor(str(floor_id))
		else:
			await route_cache.invalidate_all()
	except Exception:
		logger.warning("Failed to invalidate route cache on poi update", exc_info=True)

	return {"data": result}


@router.delete("/admin/pois/{poi_id}")
async def delete_poi(
	poi_id: str,
	client: NavigationAdminClient = Depends(get_navigation_admin_client),
	route_cache: RouteCache = Depends(_get_route_cache),
) -> Dict[str, Any]:
	result = await client.delete_poi(poi_id)
	try:
		await route_cache.invalidate_all()
	except Exception:
		logger.warning("Failed to invalidate route cache on poi delete", exc_info=True)
	return {"data": result}


@router.post("/position/grid/import")
async def import_grid_points(
	file: UploadFile = File(...),
	client: PositioningAdminClient = Depends(get_positioning_admin_client),
) -> Dict[str, Any]:
	content = await file.read()
	return {"data": await client.import_geojson_gridpoints(
		file.filename or "grid.geojson",
		content,
		content_type=file.content_type or "application/geo+json",
	)}
