import unittest

from app.clients.nav_client_admin import NavigationAdminClient
from app.clients.positioning_admin_client import PositioningAdminClient


class NavigationAdminClientHealthTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.client = NavigationAdminClient(base_url="http://example.com")
        self.addAsyncCleanup(self.client.close)

    async def test_health_methods_target_health_endpoints(self) -> None:
        called_paths = []

        async def fake_request(method, path, *, json=None, headers=None):
            called_paths.append((method, path))
            return {"ok": True, "path": path}

        self.client._request = fake_request  # type: ignore[assignment]

        await self.client.root()
        await self.client.health()
        await self.client.readiness()
        await self.client.liveness()

        self.assertEqual(
            called_paths,
            [
                ("GET", "/"),
                ("GET", "/health"),
                ("GET", "/health/ready"),
                ("GET", "/health/live"),
            ],
        )


class PositioningAdminClientHealthTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.client = PositioningAdminClient(base_url="http://example.com")
        self.addAsyncCleanup(self.client.close)

    async def test_health_methods_target_health_endpoints(self) -> None:
        called_paths = []

        async def fake_request(method, path, *, json=None, headers=None):
            called_paths.append((method, path))
            return {"ok": True, "path": path}

        self.client._request = fake_request  # type: ignore[assignment]

        await self.client.root()
        await self.client.health()
        await self.client.readiness()
        await self.client.liveness()

        self.assertEqual(
            called_paths,
            [
                ("GET", "/"),
                ("GET", "/health"),
                ("GET", "/health/ready"),
                ("GET", "/health/live"),
            ],
        )
