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
