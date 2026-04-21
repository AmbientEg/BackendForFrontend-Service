"""Navigation admin API endpoints.

Phase-1 behavior:
- expose navigation-service admin endpoints through the BFF
- bypass orchestration for admin flows
- forward payloads and return raw responses
"""

import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, Header, HTTPException

from app.clients.nav_client_admin import NavigationAdminClient

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["admin"])


async def get_navigation_admin_client() -> NavigationAdminClient:
    """Resolve the shared admin navigation client from app state without circular imports."""
    from app.main import navigation_admin_client

    if not navigation_admin_client:
        raise HTTPException(status_code=503, detail="Service initialization failed")

    return navigation_admin_client


@router.post("/buildings")
async def create_building(
	payload: Dict[str, Any],
	client: NavigationAdminClient = Depends(get_navigation_admin_client),
) -> Dict[str, Any]:
	return await client.create_building(payload)


@router.get("/buildings/{building_id}")
async def get_building(
	building_id: str,
	client: NavigationAdminClient = Depends(get_navigation_admin_client),
) -> Dict[str, Any]:
	return await client.get_building(building_id)


@router.get("/buildings/{building_id}/floors")
async def get_building_floors(
	building_id: str,
	client: NavigationAdminClient = Depends(get_navigation_admin_client),
) -> Dict[str, Any]:
	return await client.get_building_floors(building_id)


@router.post("/floors")
async def create_floor(
	payload: Dict[str, Any],
	client: NavigationAdminClient = Depends(get_navigation_admin_client),
) -> Dict[str, Any]:
	return await client.create_floor(payload)


@router.put("/floors/{floor_id}")
async def update_floor(
	floor_id: str,
	payload: Dict[str, Any],
	client: NavigationAdminClient = Depends(get_navigation_admin_client),
) -> Dict[str, Any]:
	return await client.update_floor(floor_id, payload)


@router.get("/floors/{floor_id}/map")
async def get_floor_map(
	floor_id: str,
	client: NavigationAdminClient = Depends(get_navigation_admin_client),
) -> Dict[str, Any]:
	return await client.get_floor_map(floor_id)


@router.post("/graphs/rebuild/{building_id}")
async def rebuild_graph_preview(
	building_id: str,
	client: NavigationAdminClient = Depends(get_navigation_admin_client),
) -> Dict[str, Any]:
	return await client.rebuild_graph_preview(building_id)


@router.post("/graphs/confirm/{building_id}")
async def confirm_graph(
	building_id: str,
	client: NavigationAdminClient = Depends(get_navigation_admin_client),
) -> Dict[str, Any]:
	return await client.confirm_graph(building_id)


@router.post("/graphs/rollback/{building_id}")
async def rollback_graph(
	building_id: str,
	client: NavigationAdminClient = Depends(get_navigation_admin_client),
) -> Dict[str, Any]:
	return await client.rollback_graph(building_id)


@router.put("/pois/{poi_id}")
async def update_poi(
	poi_id: str,
	payload: Dict[str, Any],
	authorization: Optional[str] = Header(default=None),
	client: NavigationAdminClient = Depends(get_navigation_admin_client),
) -> Dict[str, Any]:
	return await client.update_poi(poi_id, payload, authorization)


@router.delete("/pois/{poi_id}")
async def delete_poi(
	poi_id: str,
	authorization: Optional[str] = Header(default=None),
	client: NavigationAdminClient = Depends(get_navigation_admin_client),
) -> Dict[str, Any]:
	return await client.delete_poi(poi_id, authorization)
