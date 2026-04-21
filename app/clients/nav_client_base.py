import logging
import os
from typing import Any, Dict, Optional

import httpx
from fastapi import HTTPException

from app.core.resilience import downstream_error_detail


logger = logging.getLogger(__name__)


class _NavigationClientBase:
    """Shared HTTP transport for navigation-service API clients."""

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