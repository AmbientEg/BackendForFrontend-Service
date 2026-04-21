from typing import Any, Dict, Optional

from app.clients.http_client_base import _DownstreamHttpClientBase


class _NavigationClientBase(_DownstreamHttpClientBase):
    """Shared HTTP transport for navigation-service API clients."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        timeout_seconds: float = 8.0,
    ):
        super().__init__(
            service_name="navigation",
            base_url_env="NAVIGATION_SERVICE_URL",
            default_base_url="http://navigation-service:8000",
            base_url=base_url,
            timeout_seconds=timeout_seconds,
        )

    async def _request(
        self,
        method: str,
        path: str,
        *,
        json: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        raise NotImplementedError

    # -------- Health --------
    async def root(self) -> Dict[str, Any]:
        return await self._request("GET", "/")

    async def health(self) -> Dict[str, Any]:
        return await self._request("GET", "/health")

    async def readiness(self) -> Dict[str, Any]:
        return await self._request("GET", "/health/ready")

    async def liveness(self) -> Dict[str, Any]:
        return await self._request("GET", "/health/live")

    # -------- Service Status --------
    async def api_status(self) -> Dict[str, Any]:
        return await self._request("GET", "/api/status")

    # -------- Shared Read APIs --------
    async def get_building_floors(self, building_id: str) -> Dict[str, Any]:
        return await self._request("GET", f"/api/buildings/{building_id}/floors")

    async def get_floor_map(self, floor_id: str) -> Dict[str, Any]:
        return await self._request("GET", f"/api/floors/{floor_id}/map")

    async def get_floor_pois(self, floor_id: str) -> Dict[str, Any]:
        return await self._request("GET", f"/api/admin/pois/floor/{floor_id}")