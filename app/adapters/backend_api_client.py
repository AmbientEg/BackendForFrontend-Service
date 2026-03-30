import uuid

import httpx

from app.core.config import get_settings
from app.utils.errors import IntegrationError


class BackendApiClient:
    def __init__(self) -> None:
        self.settings = get_settings()
        self._client = httpx.AsyncClient(
            base_url=self.settings.backend_api_url,
            timeout=self.settings.request_timeout_seconds,
        )

    async def close(self) -> None:
        await self._client.aclose()

    async def get_poi_by_floor(self, floor_id: str) -> list[dict]:
        try:
            response = await self._client.get(f"/poi/floor/{floor_id}")
            response.raise_for_status()
            return response.json().get("pois", [])
        except httpx.HTTPError as exc:
            raise IntegrationError(f"Backend API failed: {exc}") from exc

    async def upsert_poi(self, payload: dict) -> dict:
        try:
            response = await self._client.post("/poi/upsert", json=payload)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as exc:
            raise IntegrationError(f"Backend API failed: {exc}") from exc