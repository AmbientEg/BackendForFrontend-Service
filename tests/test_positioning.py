import unittest
from unittest.mock import patch

from app.api import admin as admin_api
from app.api import positioning as positioning_api


class DummyUploadFile:
    def __init__(self, content: bytes, filename: str = "grid.geojson", content_type: str = "application/geo+json"):
        self._content = content
        self.filename = filename
        self.content_type = content_type

    async def read(self) -> bytes:
        return self._content


class FakePositioningClient:
    async def grid_coordinates(self, payload):
        return {"grid": [1, 2], "payload": payload}

    async def predict(self, payload):
        return {"lat": 30.1, "lng": 31.2, "payload": payload}


class FakeRedisClient:
    def __init__(self):
        self.store = {}

    async def get(self, key):
        return self.store.get(key)

    async def set(self, key, value, ttl=None):
        self.store[key] = value


class FakePositioningAdminClient:
    def __init__(self):
        self.calls = []

    async def import_geojson_gridpoints(self, filename, content, content_type="application/geo+json"):
        self.calls.append((filename, content, content_type))
        return {"status": "ok"}


class PositioningApiTests(unittest.IsolatedAsyncioTestCase):
    async def test_grid_coordinates_uses_positioning_client(self) -> None:
        fake_client = FakePositioningClient()

        with patch("app.main.positioning_client", fake_client):
            result = await positioning_api.grid_coordinates(
                request=positioning_api.GridCoordinatesRequest(),
                client=fake_client,
            )

        self.assertEqual(result, {"data": {"grid": [1, 2], "payload": {}}})

    async def test_admin_grid_import_forwards_multipart_payload(self) -> None:
        fake_client = FakePositioningAdminClient()
        upload = DummyUploadFile(b"{\"type\":\"FeatureCollection\"}")

        with patch("app.main.positioning_admin_client", fake_client):
            result = await admin_api.import_grid_points(file=upload, client=fake_client)

        self.assertEqual(result, {"data": {"status": "ok"}})
        self.assertEqual(len(fake_client.calls), 1)
        filename, content, content_type = fake_client.calls[0]
        self.assertEqual(filename, "grid.geojson")
        self.assertEqual(content, b"{\"type\":\"FeatureCollection\"}")
        self.assertEqual(content_type, "application/geo+json")

    async def test_predict_uses_live_and_sets_cache(self) -> None:
        fake_client = FakePositioningClient()
        fake_redis = FakeRedisClient()

        with patch("app.main.positioning_client", fake_client), patch("app.main.redis_client", fake_redis):
            result = await positioning_api.predict_position(
                request=positioning_api.PredictRequest(userId="user-1"),
                client=fake_client,
            )

        self.assertEqual(result["meta"]["source"], "live")
        self.assertEqual(result["meta"]["ttlSeconds"], 1)
        self.assertEqual(result["data"]["lat"], 30.1)

    async def test_predict_uses_cache_when_available(self) -> None:
        fake_client = FakePositioningClient()
        fake_redis = FakeRedisClient()
        fake_redis.store["position:user-1"] = "{\"lat\": 10.0, \"lng\": 20.0}"

        with patch("app.main.positioning_client", fake_client), patch("app.main.redis_client", fake_redis):
            result = await positioning_api.predict_position(
                request=positioning_api.PredictRequest(userId="user-1"),
                client=fake_client,
            )

        self.assertEqual(result["meta"]["source"], "cache")
        self.assertEqual(result["meta"]["ttlSeconds"], 1)
        self.assertEqual(result["data"]["lat"], 10.0)
        self.assertEqual(result["data"]["lng"], 20.0)
