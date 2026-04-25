"""Positioning API endpoints.

HTTP layer for positioning-service integration.
"""

from typing import Any, Dict, List, Tuple

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, ConfigDict

from app.clients.positioning_client import PositioningClient
from app.orchestration.positioning_orchestrator import PositioningOrchestrator

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


@router.post("/predict", summary="Predict Position")
async def predict_position(
	request: Request,
	client: PositioningClient = Depends(get_positioning_client),
	orchestrator=None,
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

	if orchestrator is None:
		from app.main import redis_client

		orchestrator = PositioningOrchestrator(redis_client, client)

	return await orchestrator.resolve_position(
		payload,
		multipart_files=multipart_files or None,
		user_id=str(user_id) if user_id is not None else None,
		floor_id=str(floor_id) if floor_id is not None else None,
	)


