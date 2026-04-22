import os
from typing import Any, Dict, Iterable, List, Optional, Tuple

from fastapi import HTTPException
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

    @staticmethod
    def _build_multipart_files(file_paths: Iterable[str]) -> List[Tuple[str, Tuple[str, bytes, str]]]:
        multipart_files: List[Tuple[str, Tuple[str, bytes, str]]] = []

        for raw_path in file_paths:
            file_path = str(raw_path)
            if not os.path.isfile(file_path):
                raise HTTPException(
                    status_code=400,
                    detail=(
                        "Positioning fallback requires multipart file uploads. "
                        f"Invalid file path: {file_path}"
                    ),
                )

            with open(file_path, "rb") as f:
                content = f.read()

            multipart_files.append(("files", (os.path.basename(file_path), content, "application/octet-stream")))

        return multipart_files

    async def predict(
        self,
        payload: Optional[Dict[str, Any]] = None,
        *,
        files: Optional[List[Tuple[str, Tuple[str, bytes, str]]]] = None,
    ) -> Dict[str, Any]:
        if files:
            return await self._multipart_request("POST", "/position/predict", files=files)

        candidate_payload = payload or {}
        payload_files = candidate_payload.get("files")
        if isinstance(payload_files, list) and payload_files:
            multipart_files = self._build_multipart_files(payload_files)
            return await self._multipart_request("POST", "/position/predict", files=multipart_files)

        return await self._request("POST", "/position/predict", json=candidate_payload)

