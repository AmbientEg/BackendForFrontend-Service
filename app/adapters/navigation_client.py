import httpx
from typing import Any, Dict, Optional
from app.core.config import get_settings
from app.utils.errors import IntegrationError


class NavigationClient:
    def __init__(
        self,
        base_url: str = "http://localhost:8010",
        timeout: float = 5.0,
        max_retries: int = 3,
    ):
        self.base_url = base_url
        self.timeout = timeout
        self.max_retries = max_retries

    async def _request(
        self,
        method: str,
        endpoint: str,
        json: Optional[Doct] = None,
    ) -> Dict[str,Any]:
        url = f"{self.base_url}{endpoint}"

        for attempt in range ()