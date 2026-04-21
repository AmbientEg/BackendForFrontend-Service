import logging
import os
from typing import Any, Dict, List, Optional, Tuple

import httpx
from fastapi import HTTPException
from pyresilience import resilient

from app.core.resilience import build_http_resilience_policy, downstream_error_detail


logger = logging.getLogger(__name__)


class PositioningClient:
    """HTTP client for positioning-service APIs.

    This client is transport-only: it performs outbound HTTP calls and returns JSON.
    Orchestration, caching, and response shaping must stay outside this layer.
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        timeout_seconds: float = 8.0,
    ):
        service_url = (base_url or os.getenv("POSITIONING_SERVICE_URL", "http://positioning-service:8000")).rstrip("/")
        self.base_url = service_url
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=httpx.Timeout(timeout_seconds),
        )

    async def close(self) -> None:
        await self._client.aclose()

    @resilient(**build_http_resilience_policy("positioning"))
    async def _request(
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
                    "Positioning service returned client error status",
                    extra={"status_code": response.status_code, "path": path},
                )
                raise HTTPException(status_code=response.status_code, detail=downstream_error_detail(response))

            if not response.content:
                return {}
            return response.json()
        except httpx.HTTPStatusError as exc:
            logger.warning(
                "Positioning service returned error status",
                extra={"status_code": exc.response.status_code, "path": path},
            )
            raise
        except httpx.RequestError as exc:
            logger.error(
                "Positioning service request failed",
                extra={"path": path, "error": str(exc)},
            )
            raise

    @resilient(**build_http_resilience_policy("positioning"))
    async def _multipart_request(
        self,
        method: str,
        path: str,
        *,
        files: Any,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        try:
            response = await self._client.request(method=method, url=path, files=files, headers=headers)

            if response.status_code >= 500:
                response.raise_for_status()

            if response.status_code >= 400:
                logger.warning(
                    "Positioning service returned client error status",
                    extra={"status_code": response.status_code, "path": path},
                )
                raise HTTPException(status_code=response.status_code, detail=downstream_error_detail(response))

            if not response.content:
                return {}
            return response.json()
        except httpx.HTTPStatusError as exc:
            logger.warning(
                "Positioning service returned error status",
                extra={"status_code": exc.response.status_code, "path": path},
            )
            raise
        except httpx.RequestError as exc:
            logger.error(
                "Positioning service request failed",
                extra={"path": path, "error": str(exc)},
            )
            raise

    # -------- Service --------
    async def root(self) -> Dict[str, Any]:
        return await self._request("GET", "/")

    # -------- Health --------
    async def health(self) -> Dict[str, Any]:
        return await self._request("GET", "/health")

    async def readiness(self) -> Dict[str, Any]:
        return await self._request("GET", "/health/ready")

    async def liveness(self) -> Dict[str, Any]:
        return await self._request("GET", "/health/live")

    # -------- Grid operations --------
    async def get_coordinates_from_grid_label(self, grid_label: str) -> Dict[str, Any]:
        return await self._request("POST", "/h", json={"grid_label": grid_label})

    async def import_geojson_gridpoints(
        self,
        endpoint_path: str,
        filename: str,
        content: bytes,
        content_type: str = "application/geo+json",
    ) -> Dict[str, Any]:
        files = {"file": (filename, content, content_type)}
        return await self._multipart_request("POST", endpoint_path, files=files)

    # -------- Prediction --------
    async def predict_grid_from_rssi_files(
        self,
        endpoint_path: str,
        files_payload: List[Tuple[str, bytes, str]],
    ) -> Dict[str, Any]:
        if len(files_payload) != 5:
            raise ValueError("predict_grid_from_rssi_files requires exactly 5 files")

        files = [("files", (filename, content, content_type)) for filename, content, content_type in files_payload]
        return await self._multipart_request("POST", endpoint_path, files=files)

