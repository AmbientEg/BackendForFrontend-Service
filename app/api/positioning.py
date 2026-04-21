"""Positioning API endpoints.

HTTP layer for positioning-service integration.
"""

from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict

from app.cache.position_cache import PositionCache
from app.clients.positioning_client import PositioningClient

router = APIRouter(prefix="/position", tags=["positioning"])


class GridCoordinatesRequest(BaseModel):
	model_config = ConfigDict(extra="allow")


class PredictRequest(BaseModel):
	model_config = ConfigDict(extra="allow")


async def get_positioning_client() -> PositioningClient:
	from app.main import positioning_client

	if not positioning_client:
		raise HTTPException(status_code=503, detail="Service initialization failed")

	return positioning_client


@router.get("/", summary="Positioning Service Root")
async def positioning_root(client: PositioningClient = Depends(get_positioning_client)) -> Dict[str, Any]:
	return {"data": await client.root()}


@router.get("/health", summary="Positioning Health")
async def positioning_health(client: PositioningClient = Depends(get_positioning_client)) -> Dict[str, Any]:
	return {"data": await client.health()}


@router.get("/health/live", summary="Positioning Liveness")
async def positioning_liveness(client: PositioningClient = Depends(get_positioning_client)) -> Dict[str, Any]:
	return {"data": await client.liveness()}


@router.get("/health/ready", summary="Positioning Readiness")
async def positioning_readiness(client: PositioningClient = Depends(get_positioning_client)) -> Dict[str, Any]:
	return {"data": await client.readiness()}


@router.post("/grid/coordinates", summary="Resolve Grid Coordinates")
async def grid_coordinates(
	request: GridCoordinatesRequest,
	client: PositioningClient = Depends(get_positioning_client),
) -> Dict[str, Any]:
	return {"data": await client.grid_coordinates(request.model_dump(exclude_none=True))}


@router.post("/predict", summary="Predict Position")
async def predict_position(
	request: PredictRequest,
	client: PositioningClient = Depends(get_positioning_client),
) -> Dict[str, Any]:
	payload = request.model_dump(exclude_none=True)
	user_id = payload.get("userId") or payload.get("user_id")

	from app.main import redis_client
	position_cache = PositionCache(redis_client) if redis_client and user_id else None

	if position_cache is not None:
		cached_position = await position_cache.get(str(user_id))
		if cached_position is not None:
			return {
				"data": cached_position,
				"meta": {
					"source": "cache",
					"ttlSeconds": 1,
				},
			}

	prediction = await client.predict(payload)

	if position_cache is not None:
		await position_cache.set(str(user_id), prediction)

	return {
		"data": prediction,
		"meta": {
			"source": "live",
			"ttlSeconds": 1,
		},
	}


