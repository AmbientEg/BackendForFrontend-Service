from typing import Any, Dict, Optional

from pyresilience import resilient

from app.clients.nav_client_base import _NavigationClientBase
from app.core.resilience import build_http_resilience_policy


class NavigationClient(_NavigationClientBase):
    """HTTP client for user-facing navigation-service APIs."""

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

    # -------- Navigation --------
    async def calculate_route(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return await self._request("POST", "/api/navigation/route", json=payload)