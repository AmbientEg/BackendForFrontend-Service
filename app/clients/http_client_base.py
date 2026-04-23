import logging
import os
from typing import Any, Dict, Optional

import httpx
from fastapi import HTTPException

from app.core.resilience import downstream_error_detail


class _DownstreamHttpClientBase:
    """Shared async HTTP transport for downstream service clients."""

    def __init__(
        self,
        *,
        service_name: str,
        base_url_env: str,
        default_base_url: str,
        base_url: Optional[str] = None,
        timeout_seconds: float = 8.0,
    ) -> None:
        self.service_name = service_name
        self._logger = logging.getLogger(__name__)
        resolved_base_url = (base_url or os.getenv(base_url_env, default_base_url)).rstrip("/")
        self.base_url = resolved_base_url
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
                self._logger.error(
                    "%s service returned server error",
                    self.service_name,
                    extra={"status_code": response.status_code, "path": path},
                )
                response.raise_for_status()

            if response.status_code >= 400:
                self._logger.warning(
                    "%s service returned client error",
                    self.service_name,
                    extra={"status_code": response.status_code, "path": path},
                )
                raise HTTPException(status_code=response.status_code, detail=downstream_error_detail(response))

            if not response.content:
                return {}
            return response.json()
        except httpx.HTTPStatusError as exc:
            self._logger.error(
                "%s service returned HTTP status error",
                self.service_name,
                extra={"status_code": exc.response.status_code, "path": path},
            )
            raise
        except httpx.RequestError as exc:
            self._logger.error(
                "%s service request failed",
                self.service_name,
                extra={"path": path, "error": str(exc)},
            )
            raise

    async def _perform_multipart_request(
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
                self._logger.error(
                    "%s service returned server error",
                    self.service_name,
                    extra={"status_code": response.status_code, "path": path},
                )
                response.raise_for_status()

            if response.status_code >= 400:
                self._logger.warning(
                    "%s service returned client error",
                    self.service_name,
                    extra={"status_code": response.status_code, "path": path},
                )
                raise HTTPException(status_code=response.status_code, detail=downstream_error_detail(response))

            if not response.content:
                return {}
            return response.json()
        except httpx.HTTPStatusError as exc:
            self._logger.error(
                "%s service returned HTTP status error",
                self.service_name,
                extra={"status_code": exc.response.status_code, "path": path},
            )
            raise
        except httpx.RequestError as exc:
            self._logger.error(
                "%s service multipart request failed",
                self.service_name,
                extra={"path": path, "error": str(exc)},
            )
            raise
