from typing import Any, Dict, List, Optional, Tuple

from pyresilience import resilient

from app.clients.positioning_base import _PositioningClientBase
from app.core.resilience import build_admin_http_resilience_policy


class PositioningAdminClient(_PositioningClientBase):
    """HTTP client for admin positioning-service APIs."""

    @resilient(**build_admin_http_resilience_policy("positioning"))
    async def _request(
        self,
        method: str,
        path: str,
        *,
        json: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        return await self._perform_request(method, path, json=json, headers=headers)

    @resilient(**build_admin_http_resilience_policy("positioning"))
    async def _multipart_request(
        self,
        method: str,
        path: str,
        *,
        files: Any,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        return await self._perform_multipart_request(method, path, files=files, headers=headers)

    async def import_geojson_gridpoints(
        self,
        filename: str,
        content: bytes,
        content_type: str = "application/geo+json",
    ) -> Dict[str, Any]:
        files = {"file": (filename, content, content_type)}
        return await self._multipart_request("POST", "/position/grid/import", files=files)