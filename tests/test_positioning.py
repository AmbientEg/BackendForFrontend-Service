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


class DummyRequest:
    def __init__(self, payload, content_type="application/json"):
        self._payload = payload
        self.headers = {"content-type": content_type}

    async def json(self):
        return self._payload


class FakePositioningClient:
    def __init__(self):
        self.predict_calls = []
        self.grid_coordinates_calls = []

    async def grid_coordinates(self, payload):
        self.grid_coordinates_calls.append(payload)
        return {"latitude": 30.027778981652506, "longitude": 31.201395972907505}

    async def predict(self, payload, files=None):
        self.predict_calls.append(payload)
        return {"data": {"predicted_grid": "60", "floorId": "95278620-3149-43d6-8875-37bdeda08bca"}}


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

        self.assertEqual(
            result,
            {"data": {"latitude": 30.027778981652506, "longitude": 31.201395972907505}},
        )

    async def test_predict_orchestrates_grid_coordinates(self) -> None:
        fake_client = FakePositioningClient()
        fake_redis = FakeRedisClient()

        with patch("app.main.positioning_client", fake_client), patch("app.main.redis_client", fake_redis):
            result = await positioning_api.predict_position(
                request=DummyRequest({"userId": "user-1", "floorId": "95278620-3149-43d6-8875-37bdeda08bca"}),
                client=fake_client,
            )

        self.assertEqual(result["data"]["grid_label"], "60")
        self.assertEqual(result["data"]["data"]["latitude"], 30.027778981652506)
        self.assertEqual(result["data"]["data"]["longitude"], 31.201395972907505)
        self.assertEqual(len(fake_client.predict_calls), 1)
        self.assertEqual(len(fake_client.grid_coordinates_calls), 1)
        self.assertEqual(fake_client.grid_coordinates_calls[0], {"grid_label": "60"})

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
                request=DummyRequest({"userId": "user-1"}),
                client=fake_client,
            )

        self.assertEqual(result["meta"]["source"], "live")
        self.assertEqual(result["meta"]["ttlSeconds"], 1)
        self.assertEqual(result["data"]["grid_label"], "60")
        self.assertEqual(result["data"]["data"]["latitude"], 30.027778981652506)

    async def test_predict_uses_cache_when_available(self) -> None:
        fake_client = FakePositioningClient()
        fake_redis = FakeRedisClient()
        fake_redis.store["position:user-1"] = "{\"floorId\": \"95278620-3149-43d6-8875-37bdeda08bca\", \"grid_label\": \"60\", \"data\": {\"latitude\": 10.0, \"longitude\": 20.0}}"

        with patch("app.main.positioning_client", fake_client), patch("app.main.redis_client", fake_redis):
            result = await positioning_api.predict_position(
                request=DummyRequest({"userId": "user-1"}),
                client=fake_client,
            )

        self.assertEqual(result["meta"]["source"], "cache")
        self.assertEqual(result["meta"]["ttlSeconds"], 1)
        self.assertEqual(result["data"]["grid_label"], "60")
        self.assertEqual(result["data"]["data"]["latitude"], 10.0)
        self.assertEqual(result["data"]["data"]["longitude"], 20.0)
