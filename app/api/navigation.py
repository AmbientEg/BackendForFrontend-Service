"""Navigation API endpoints."""

import json
import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel, Field

from app.orchestration.navigation_orchestrator import NavigationOrchestrator
from app.clients.navigation_client import NavigationClient

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/navigation", tags=["navigation"])


# -------- Request/Response Models --------
class LocationFromModel(BaseModel):
    """Source location (coordinates or POI)."""
    user_id: Optional[str] = Field(None, alias="userId", description="User identifier")
    building_id: str = Field(..., alias="buildingId", description="Building UUID")
    floor_id: str = Field(..., alias="floorId", description="Floor UUID")
    lat: Optional[float] = Field(None, description="Latitude")
    lng: Optional[float] = Field(None, description="Longitude")
    files: Optional[list[Any]] = Field(None, description="File references for positioning fallback")


    class Config:
        populate_by_name = True

async def get_navigation_client() -> NavigationClient:
    """Get user navigation client for health/status probes."""
    from app.main import navigation_client
    
    if not navigation_client:
        raise HTTPException(status_code=503, detail="Service initialization failed")
    
    return navigation_client




@router.get("/", summary="Navigation Service Root")
async def navigation_root(client: Any = Depends(get_navigation_client)) -> Dict[str, Any]:
    return {"data": await client.root()}


@router.get("/health", summary="Navigation Health")
async def navigation_health(client: Any = Depends(get_navigation_client)) -> Dict[str, Any]:
    return {"data": await client.health()}


@router.get("/health/ready", summary="Navigation Readiness")
async def navigation_readiness(client: Any = Depends(get_navigation_client)) -> Dict[str, Any]:
    return {"data": await client.readiness()}


@router.get("/health/live", summary="Navigation Liveness")
async def navigation_liveness(client: Any = Depends(get_navigation_client)) -> Dict[str, Any]:
    return {"data": await client.liveness()}


@router.get("/status", summary="Navigation Service Status")
async def navigation_status(client: Any = Depends(get_navigation_client)) -> Dict[str, Any]:
    return {"data": await client.api_status()}



class LocationToModel(BaseModel):
    """Destination location (POI only)."""
    poi_id: str = Field(..., alias="poiId", description="POI UUID")

    class Config:
        populate_by_name = True


class RouteOptionsModel(BaseModel):
    """Route calculation options."""
    accessible: bool = Field(False, description="Require wheelchair accessible route")


class CalculateRouteRequest(BaseModel):
    """Calculate route request."""
    from_location: LocationFromModel = Field(..., alias="from")
    to_location: LocationToModel = Field(..., alias="to")
    options: Optional[RouteOptionsModel] = None

    class Config:
        populate_by_name = True


class RouteStepModel(BaseModel):
    """Single navigation step."""
    instruction: str
    distance_meters: Optional[float] = None


class WaypointModel(BaseModel):
    """POI waypoint along route."""
    id: str
    name: str
    type: str
    distance: Optional[float] = None
    sequence: int


class CalculateRouteResponse(BaseModel):
    """Route calculation response (mobile-optimized)."""
    route: Dict[str, Any]
    meta: Dict[str, Any]
    warning: Optional[str] = None


# -------- Dependency injection --------
async def get_orchestrator() -> NavigationOrchestrator:
    """Get navigation orchestrator with shared clients.
    
    This function retrieves clients from app state at request time,
    avoiding circular imports at module load time.
    """
    from app.main import redis_client, navigation_client, positioning_client
    
    if not redis_client or not navigation_client or not positioning_client:
        raise HTTPException(status_code=503, detail="Service initialization failed")
    return NavigationOrchestrator(redis_client, navigation_client, positioning_client)


# -------- Endpoints --------
@router.post("/get/route", summary="Calculate Route")
async def calculate_route(
    request: Request,
    orchestrator: NavigationOrchestrator = Depends(get_orchestrator),
) -> CalculateRouteResponse:
    try:
        payload_data: Dict[str, Any]
        multipart_files = None

        content_type = request.headers.get("content-type", "")
        if content_type.startswith("multipart/form-data"):
            form_data = await request.form()
            from_payload: Dict[str, Any] = {}
            to_payload: Dict[str, Any] = {}
            options_payload: Dict[str, Any] = {}

            if "from" in form_data:
                raw_from = form_data.get("from")
                if isinstance(raw_from, str):
                    parsed_from = json.loads(raw_from)
                    if isinstance(parsed_from, dict):
                        from_payload = parsed_from

            if "to" in form_data:
                raw_to = form_data.get("to")
                if isinstance(raw_to, str):
                    parsed_to = json.loads(raw_to)
                    if isinstance(parsed_to, dict):
                        to_payload = parsed_to

            if "options" in form_data:
                raw_options = form_data.get("options")
                if isinstance(raw_options, str):
                    parsed_options = json.loads(raw_options)
                    if isinstance(parsed_options, dict):
                        options_payload = parsed_options

            if not from_payload:
                from_payload = {
                    "userId": form_data.get("userId"),
                    "buildingId": form_data.get("buildingId"),
                    "floorId": form_data.get("floorId"),
                    "lat": form_data.get("lat"),
                    "lng": form_data.get("lng"),
                }

            if not to_payload:
                to_payload = {
                    "poiId": form_data.get("poiId") or form_data.get("toPoiId"),
                }

            if not options_payload and "accessible" in form_data:
                raw_accessible = str(form_data.get("accessible")).strip().lower()
                options_payload = {"accessible": raw_accessible in {"1", "true", "yes", "on"}}

            payload_data = {
                "from": from_payload,
                "to": to_payload,
                "options": options_payload or None,
            }

            upload_files = form_data.getlist("files")
            built_multipart_files = []
            for file_obj in upload_files:
                if not (hasattr(file_obj, "filename") and hasattr(file_obj, "read")):
                    continue
                content = await file_obj.read()
                built_multipart_files.append(
                    (
                        "files",
                        (
                            file_obj.filename or "beacon.csv",
                            content,
                            file_obj.content_type or "application/octet-stream",
                        ),
                    )
                )

            multipart_files = built_multipart_files or None
        else:
            json_payload = await request.json()
            if not isinstance(json_payload, dict):
                raise HTTPException(status_code=400, detail="Invalid JSON payload")
            payload_data = json_payload

        parsed_request = CalculateRouteRequest.model_validate(payload_data)
        from_loc = parsed_request.from_location
        to_loc = parsed_request.to_location
        opts = parsed_request.options or RouteOptionsModel()

        effective_files = multipart_files or from_loc.files

        response = await orchestrator.calculate_route(
            from_building_id=from_loc.building_id,
            from_floor_id=from_loc.floor_id,
            to_poi_id=to_loc.poi_id,
            user_id=from_loc.user_id,
            from_lat=from_loc.lat,
            from_lng=from_loc.lng,
            from_files=effective_files,
            accessible=opts.accessible,
        )

        logger.info(
            "Route calculated",
            extra={
                "from_floor": from_loc.floor_id,
                "to_poi": to_loc.poi_id,
            },
        )

        return CalculateRouteResponse(**response)

    except (ValueError, json.JSONDecodeError) as e:
        logger.warning(f"Invalid route request: {e}")
        raise HTTPException(status_code=400, detail=str(e))



