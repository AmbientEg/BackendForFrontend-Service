from typing import Any, Dict, Optional

from pyresilience import resilient

from app.clients.nav_client_base import _NavigationClientBase
from app.core.resilience import build_admin_http_resilience_policy


class NavigationAdminClient(_NavigationClientBase):
    """HTTP client for admin navigation-service APIs."""

    @resilient(**build_admin_http_resilience_policy("navigation"))
    async def _request(
        self,
        method: str,
        path: str,
        *,
        json: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        return await self._perform_request(method, path, json=json, headers=headers)

    # -------- Buildings --------
    async def create_building(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return await self._request("POST", "/api/buildings/create", json=payload)

    async def get_building(self, building_id: str) -> Dict[str, Any]:
        return await self._request("GET", f"/api/buildings/get/{building_id}")

    async def get_building_floors(self, building_id: str) -> Dict[str, Any]:
        return await self._request("GET", f"/api/buildings/get/{building_id}/floors")

    # -------- Floors --------
    async def create_floor(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return await self._request("POST", "/api/floors/create", json=payload)

    async def update_floor(self, floor_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        return await self._request("PUT", f"/api/floors/{floor_id}", json=payload)

    # -------- Graph lifecycle --------
    async def rebuild_graph_preview(self, building_id: str) -> Dict[str, Any]:
        return await self._request("POST", f"/api/graphs/rebuild/{building_id}")

    async def confirm_graph(self, building_id: str) -> Dict[str, Any]:
        return await self._request("POST", f"/api/graphs/confirm/{building_id}")

    async def rollback_graph(self, building_id: str) -> Dict[str, Any]:
        return await self._request("POST", f"/api/graphs/rollback/{building_id}")

    # -------- Admin POI --------
    async def update_poi(
        self,
        poi_id: str,
        payload: Dict[str, Any],
        authorization: Optional[str] = None,
    ) -> Dict[str, Any]:
        headers = {"Authorization": authorization} if authorization else None
        return await self._request(
            "PUT",
            f"/api/admin/pois/{poi_id}",
            json=payload,
            headers=headers,
        )

    async def delete_poi(self, poi_id: str, authorization: Optional[str] = None) -> Dict[str, Any]:
        headers = {"Authorization": authorization} if authorization else None
        return await self._request(
            "DELETE",
            f"/api/admin/pois/{poi_id}",
            headers=headers,
        )
