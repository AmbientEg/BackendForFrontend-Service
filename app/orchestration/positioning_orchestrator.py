"""Positioning orchestration layer.

Combines predict -> grid-coordinate resolution and caches the resolved result.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from fastapi import HTTPException

from app.cache.position_cache import PositionCache
from app.cache.redis_client import RedisClient
from app.clients.positioning_client import PositioningClient


class PositioningOrchestrator:
	"""Orchestrator for positioning flows.

	This class keeps the HTTP route thin while owning the combined positioning
	workflow used by the BFF.
	"""

	def __init__(self, redis_client: Optional[RedisClient], positioning_client: PositioningClient):
		self.redis = redis_client
		self.position_cache = PositionCache(redis_client) if redis_client else None
		self.positioning_client = positioning_client

	@staticmethod
	def _extract_grid_label(payload: Dict[str, Any]) -> Optional[str]:
		for key in ("grid_label", "predicted_grid", "gridLabel"):
			value = payload.get(key)
			if value not in (None, ""):
				return str(value)

		data_obj = payload.get("data")
		if isinstance(data_obj, dict):
			for key in ("grid_label", "predicted_grid", "gridLabel"):
				value = data_obj.get(key)
				if value not in (None, ""):
					return str(value)

		return None

	@staticmethod
	def _extract_coordinates(payload: Dict[str, Any]) -> Dict[str, Any]:
		data_obj = payload.get("data")
		if isinstance(data_obj, dict):
			return data_obj
		return payload

	@staticmethod
	def _extract_cached_floor_id(payload: Dict[str, Any]) -> Optional[str]:
		for key in ("floorId", "floor_id"):
			value = payload.get(key)
			if value not in (None, ""):
				return str(value)

		data_obj = payload.get("data")
		if isinstance(data_obj, dict):
			for key in ("floorId", "floor_id"):
				value = data_obj.get(key)
				if value not in (None, ""):
					return str(value)

		return None

	@staticmethod
	def _build_position_response(grid_label: str, coordinates: Dict[str, Any]) -> Dict[str, Any]:
		return {
			"grid_label": grid_label,
			"data": coordinates,
		}

	async def resolve_position(
		self,
		payload: Dict[str, Any],
		*,
		multipart_files: Optional[List[Tuple[str, Tuple[str, bytes, str]]]] = None,
		user_id: Optional[str] = None,
		floor_id: Optional[str] = None,
	) -> Dict[str, Any]:
		position_cache = self.position_cache if self.position_cache is not None and user_id else None

		if position_cache is not None:
			cached_position = await position_cache.get(str(user_id))
			if cached_position is not None:
				cached_floor_id = self._extract_cached_floor_id(cached_position)
				if floor_id is not None and cached_floor_id is not None and str(floor_id) != str(cached_floor_id):
					await position_cache.delete(str(user_id))
				else:
					cached_grid_label = self._extract_grid_label(cached_position)
					cached_coordinates = self._extract_coordinates(cached_position)
					if cached_grid_label and cached_coordinates:
						return {
							"data": self._build_position_response(cached_grid_label, cached_coordinates),
							"meta": {
								"source": "cache",
								"ttlSeconds": 1,
							},
						}

		prediction = await self.positioning_client.predict(payload, files=multipart_files or None)
		grid_label = self._extract_grid_label(prediction)
		if not grid_label:
			raise HTTPException(status_code=400, detail="Predict response did not include a grid label")

		coordinates_response = await self.positioning_client.grid_coordinates({"grid_label": grid_label})
		coordinates = self._extract_coordinates(coordinates_response)
		result = self._build_position_response(grid_label, coordinates)

		if position_cache is not None:
			cache_value: Dict[str, Any] = {
				"floorId": floor_id,
				"grid_label": grid_label,
				"data": coordinates,
			}
			await position_cache.set(str(user_id), cache_value)

		return {
			"data": result,
			"meta": {
				"source": "live",
				"ttlSeconds": 1,
			},
		}