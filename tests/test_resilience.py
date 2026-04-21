import os
import unittest
from unittest.mock import patch

import httpx
from fastapi import HTTPException

from app.clients.navigation_client import NavigationClient
from app.core.resilience import build_admin_http_resilience_policy, build_http_resilience_policy


class ResiliencePolicyTests(unittest.TestCase):
    def test_build_http_resilience_policy_includes_retry_circuit_breaker_and_bulkhead(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            policy = build_http_resilience_policy("navigation")

        self.assertIn("retry", policy)
        self.assertIn("circuit_breaker", policy)
        self.assertIn("bulkhead", policy)
        self.assertEqual(policy["retry"].max_attempts, 3)
        self.assertEqual(policy["bulkhead"].max_concurrent, 20)

    def test_build_admin_http_resilience_policy_uses_reserved_bulkhead(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            policy = build_admin_http_resilience_policy("navigation")

        self.assertIn("bulkhead", policy)
        self.assertEqual(policy["bulkhead"].max_concurrent, 5)


class NavigationClientResilienceTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.client = NavigationClient(base_url="http://example.com")
        self.addAsyncCleanup(self.client.close)

    async def test_health_retries_transient_request_errors(self) -> None:
        request = httpx.Request("GET", "http://example.com/health")
        response = httpx.Response(200, request=request, json={"status": "ok"})

        async def request_side_effect(*args, **kwargs):
            if request_side_effect.calls < 2:
                request_side_effect.calls += 1
                raise httpx.ConnectError("temporary failure", request=request)
            request_side_effect.calls += 1
            return response

        request_side_effect.calls = 0
        self.client._client.request = request_side_effect  # type: ignore[assignment]

        result = await self.client.health()

        self.assertEqual(result, {"status": "ok"})
        self.assertEqual(request_side_effect.calls, 3)

    async def test_health_propagates_downstream_client_errors(self) -> None:
        request = httpx.Request("GET", "http://example.com/health")
        response = httpx.Response(404, request=request, json={"detail": "not found"})

        async def request_side_effect(*args, **kwargs):
            return response

        self.client._client.request = request_side_effect  # type: ignore[assignment]

        with self.assertRaises(HTTPException) as captured:
            await self.client.health()

        self.assertEqual(captured.exception.status_code, 404)
        self.assertEqual(captured.exception.detail, '{"detail":"not found"}')
