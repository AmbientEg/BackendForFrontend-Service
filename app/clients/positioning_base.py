from typing import Any, Dict, Optional

from app.clients.http_client_base import _DownstreamHttpClientBase


class _PositioningClientBase(_DownstreamHttpClientBase):
    """Shared HTTP transport for positioning-service API clients."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        timeout_seconds: float = 8.0,
    ):
        super().__init__(
            service_name="positioning",
            base_url_env="POSITIONING_SERVICE_URL",
            default_base_url="http://positioning-service:8000",
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

    async def _multipart_request(
        self,
        method: str,
        path: str,
        *,
        files: Any,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        raise NotImplementedError

    async def root(self) -> Dict[str, Any]:
        return await self._request("GET", "/")

    async def health(self) -> Dict[str, Any]:
        return await self._request("GET", "/health")

    async def readiness(self) -> Dict[str, Any]:
        return await self._request("GET", "/health/ready")

    async def liveness(self) -> Dict[str, Any]:
        return await self._request("GET", "/health/live")