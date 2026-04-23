import unittest

from app.orchestration.navigation_orchestrator import NavigationOrchestrator


class FakeRedisClient:
	async def get(self, key):
		return None

	async def set(self, key, value, ttl=None):
		return None

	async def delete(self, key):
		return None

	async def delete_prefix(self, prefix):
		return 0

	async def delete_pattern(self, pattern):
		return 0


class FakeNavigationClient:
	async def calculate_route(self, payload):
		return {"route": "ok", "payload": payload}


class FakePositioningClient:
	async def predict(self, payload):
		return {"predicted_grid": "60", "payload": payload}

	async def grid_coordinates(self, payload):
		return {"lat": 30.0277, "lng": 31.2014, "payload": payload}


class NavigationOrchestratorTests(unittest.IsolatedAsyncioTestCase):
	async def test_calculate_route_uses_grid_label_coordinates(self) -> None:
		orchestrator = NavigationOrchestrator(
			FakeRedisClient(),
			FakeNavigationClient(),
			FakePositioningClient(),
		)

		response = await orchestrator.calculate_route(
			from_building_id="building-1",
			from_floor_id="floor-1",
			to_poi_id="poi-1",
			user_id="user-1",
			from_files=["sample-1.csv", "sample-2.csv"],
			accessible=True,
		)

		self.assertEqual(response["meta"]["source"], "live")
		self.assertTrue(response["meta"]["usedPositioning"])
		self.assertEqual(response["route"]["route"], "ok")
		self.assertEqual(response["route"]["payload"]["from"]["lat"], 30.0277)
		self.assertEqual(response["route"]["payload"]["from"]["lng"], 31.2014)
