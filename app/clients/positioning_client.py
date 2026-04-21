from typing import Any, Dict, Optional

from pyresilience import resilient

from app.clients.positioning_base import _PositioningClientBase
from app.core.resilience import build_http_resilience_policy


class PositioningClient(_PositioningClientBase):
    """HTTP client for user-facing positioning-service APIs."""

    @resilient(**build_http_resilience_policy("positioning"))
    async def _request(
        self,
        method: str,
        path: str,
        *,
        json: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        return await self._perform_request(method, path, json=json, headers=headers)

    async def _multipart_request(
        self,
        method: str,
        path: str,
        *,
        files: Any,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        return await self._perform_multipart_request(method, path, files=files, headers=headers)

    async def grid_coordinates(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return await self._request("POST", "/position/grid/coordinates", json=payload)

    async def predict(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return await self._request("POST", "/position/predict", json=payload)

