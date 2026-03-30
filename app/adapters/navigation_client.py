import httpx

from app.core.config import get_settings
from app.utils.errors import IntegrationError


class NavigationClient:
    def __init__(self) -> None:
        self.settings = get_settings()
        self._client = httpx.AsyncClient(
            base_url=self.settings.navigation_service_url,
            timeout=self.settings.request_timeout_seconds,
        )

    async def close(self) -> None:
        await self._client.aclose()

    async def get_path(self, start: str, end: str) -> list[str]:
        if self.settings.mock_externals:
            return [start, "node-mid-1", "node-mid-2", end]

        try:
            response = await self._client.get(f"/path/{start}/{end}")
            response.raise_for_status()
            body = response.json()
            return body.get("path", [])
        except httpx.HTTPError as exc:
            raise IntegrationError(f"Navigation service failed: {exc}") from exc
