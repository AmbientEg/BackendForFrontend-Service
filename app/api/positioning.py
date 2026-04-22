"""Positioning API endpoints.

HTTP layer for positioning-service integration.
"""

from typing import Any, Dict, List, Tuple

from fastapi import APIRouter, Depends, HTTPException, Request
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
	request: Request,
	client: PositioningClient = Depends(get_positioning_client),
) -> Dict[str, Any]:
	payload: Dict[str, Any] = {}
	multipart_files: List[Tuple[str, Tuple[str, bytes, str]]] = []

	content_type = request.headers.get("content-type", "")
	if content_type.startswith("multipart/form-data"):
		form_data = await request.form()
		payload = {
			k: v
			for k, v in form_data.items()
			if not (hasattr(v, "filename") and hasattr(v, "read"))
		}
		upload_files = form_data.getlist("files")

		for file_obj in upload_files:
			if not (hasattr(file_obj, "filename") and hasattr(file_obj, "read")):
				continue
			content = await file_obj.read()
			multipart_files.append(
				(
					"files",
					(
						file_obj.filename or "beacon.csv",
						content,
						file_obj.content_type or "application/octet-stream",
					),
				)
			)

		if not multipart_files:
			raise HTTPException(status_code=400, detail="files are required in multipart/form-data")
	else:
		json_payload = await request.json()
		if not isinstance(json_payload, dict):
			raise HTTPException(status_code=400, detail="Invalid JSON payload")
		payload = json_payload

	user_id = payload.get("userId") or payload.get("user_id")
	floor_id = payload.get("floorId") or payload.get("floor_id")

	from app.main import redis_client
	position_cache = PositionCache(redis_client) if redis_client and user_id else None

	if position_cache is not None:
		cached_position = await position_cache.get(str(user_id))
		if cached_position is not None:
			cached_floor_id = cached_position.get("floorId") or cached_position.get("floor_id")
			if floor_id is not None and cached_floor_id is not None and str(floor_id) != str(cached_floor_id):
				await position_cache.delete(str(user_id))
			else:
				return {
					"data": cached_position,
					"meta": {
						"source": "cache",
						"ttlSeconds": 1,
					},
				}

	prediction = await client.predict(payload, files=multipart_files or None)
	if floor_id is not None and isinstance(prediction, dict) and "floorId" not in prediction and "floor_id" not in prediction:
		prediction = {
			**prediction,
			"floorId": floor_id,
		}

	if position_cache is not None:
		await position_cache.set(str(user_id), prediction)

	return {
		"data": prediction,
		"meta": {
			"source": "live",
			"ttlSeconds": 1,
		},
	}


