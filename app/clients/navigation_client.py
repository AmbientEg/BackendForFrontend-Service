import logging
import os
from typing import Any, Dict, Optional

import httpx
from fastapi import HTTPException
from pyresilience import resilient

from app.core.resilience import (
    build_admin_http_resilience_policy,
    build_http_resilience_policy,
    downstream_error_detail,
)


logger = logging.getLogger(__name__)


class NavigationClient:
    """HTTP client for navigation-service APIs.

    This client is transport-only: it performs outbound HTTP calls and returns JSON.
    Orchestration, caching, and response shaping must stay outside this layer.
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        timeout_seconds: float = 8.0,
    ):
        service_url = (base_url or os.getenv("NAVIGATION_SERVICE_URL", "http://navigation-service:8000")).rstrip("/")
        self.base_url = service_url
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=httpx.Timeout(timeout_seconds),
        )

    async def close(self) -> None:
        await self._client.aclose()

    async def _perform_request(
        self,
        method: str,
        path: str,
        *,
        json: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        try:
            response = await self._client.request(method=method, url=path, json=json, headers=headers)

            if response.status_code >= 500:
                response.raise_for_status()

            if response.status_code >= 400:
                logger.warning(
                    "Navigation service returned client error status",
                    extra={"status_code": response.status_code, "path": path},
                )
                raise HTTPException(status_code=response.status_code, detail=downstream_error_detail(response))

            if not response.content:
                return {}
            return response.json()
        except httpx.HTTPStatusError as exc:
            logger.warning(
                "Navigation service returned error status",
                extra={"status_code": exc.response.status_code, "path": path},
            )
            raise
        except httpx.RequestError as exc:
            logger.error(
                "Navigation service request failed",
                extra={"path": path, "error": str(exc)},
            )
            raise

    @resilient(**build_http_resilience_policy("navigation"))
    async def _request(
        self,
        method: str,
        path: str,
        *,
        json: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        return await self._perform_request(method, path, json=json, headers=headers)

    @resilient(**build_admin_http_resilience_policy("navigation"))
    async def _admin_request(
        self,
        method: str,
        path: str,
        *,
        json: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        return await self._perform_request(method, path, json=json, headers=headers)

    # -------- Health --------
    async def health(self) -> Dict[str, Any]:
        return await self._request("GET", "/health")

    async def readiness(self) -> Dict[str, Any]:
        return await self._request("GET", "/health/ready")

    async def liveness(self) -> Dict[str, Any]:
        return await self._request("GET", "/health/live")

    # -------- Service Status --------
    async def root(self) -> Dict[str, Any]:
        return await self._request("GET", "/")

    async def api_status(self) -> Dict[str, Any]:
        return await self._request("GET", "/api/status")

    # -------- Buildings --------
    async def create_building(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return await self._request("POST", "/api/buildings", json=payload)

    async def get_building(self, building_id: str) -> Dict[str, Any]:
        return await self._request("GET", f"/api/buildings/{building_id}")

    async def get_building_floors(self, building_id: str) -> Dict[str, Any]:
        return await self._request("GET", f"/api/buildings/{building_id}/floors")

    # -------- Floors --------
    async def create_floor(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return await self._request("POST", "/api/floors", json=payload)

    async def update_floor(self, floor_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        return await self._request("PUT", f"/api/floors/{floor_id}", json=payload)

    async def get_floor_map(self, floor_id: str) -> Dict[str, Any]:
        return await self._request("GET", f"/api/floors/{floor_id}/map")

    # -------- Graph lifecycle --------
    async def rebuild_graph_preview(self, building_id: str) -> Dict[str, Any]:
        return await self._request("POST", f"/api/graphs/rebuild/{building_id}")

    async def confirm_graph(self, building_id: str) -> Dict[str, Any]:
        return await self._request("POST", f"/api/graphs/confirm/{building_id}")

    async def rollback_graph(self, building_id: str) -> Dict[str, Any]:
        return await self._request("POST", f"/api/graphs/rollback/{building_id}")

    # -------- Navigation --------
    async def calculate_route(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return await self._request("POST", "/api/navigation/route", json=payload)

    # -------- Admin POI --------
    async def update_poi(
        self,
        poi_id: str,
        payload: Dict[str, Any],
        authorization: Optional[str] = None,
    ) -> Dict[str, Any]:
        headers = {"Authorization": authorization} if authorization else None
        return await self._admin_request(
            "PUT",
            f"/api/admin/pois/{poi_id}",
            json=payload,
            headers=headers,
        )

    async def delete_poi(self, poi_id: str, authorization: Optional[str] = None) -> Dict[str, Any]:
        headers = {"Authorization": authorization} if authorization else None
        return await self._admin_request(
            "DELETE",
            f"/api/admin/pois/{poi_id}",
            headers=headers,
        )

    async def get_floor_pois(self, floor_id: str) -> Dict[str, Any]:
        return await self._admin_request("GET", f"/api/admin/pois/floor/{floor_id}")