"""Navigation API endpoints.

HTTP layer for navigation flows. Calls orchestration layer.
No business logic here — only request/response validation and delegation.

Endpoints:
1. POST /api/navigation/route - calculate route (POI to POI or position to POI)
2. GET /api/navigation/nearby - find nearby POIs (FUTURE)
"""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field

from app.adapters.navigation_adapter import NavigationAdapter
from app.orchestration.navigation_orchestrator import NavigationOrchestrator

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/navigation", tags=["navigation"])


# -------- Request/Response Models --------
class LocationFromModel(BaseModel):
    """Source location (coordinates or POI)."""
    floor_id: str = Field(..., description="Floor UUID")
    lat: float = Field(..., description="Latitude")
    lng: float = Field(..., description="Longitude")


class LocationToModel(BaseModel):
    """Destination location (POI only)."""
    poi_id: str = Field(..., description="POI UUID")


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
    distance_meters: float
    duration_seconds: int
    steps: list[str]
    polyline: list[list[float]]
    waypoints: list[dict] = []
    accessibility: dict = {}
    metadata: dict = {}


# -------- Dependency injection --------
async def get_orchestrator() -> NavigationOrchestrator:
    """Get navigation orchestrator with shared clients.
    
    This function retrieves clients from app state at request time,
    avoiding circular imports at module load time.
    """
    from app.main import redis_client, navigation_client
    
    if not redis_client or not navigation_client:
        raise HTTPException(status_code=503, detail="Service initialization failed")
    return NavigationOrchestrator(redis_client, navigation_client)


# -------- Endpoints --------
@router.post("/route", response_model=CalculateRouteResponse, summary="Calculate Route")
async def calculate_route(
    request: CalculateRouteRequest,
    orchestrator: NavigationOrchestrator = Depends(get_orchestrator),
) -> CalculateRouteResponse:
    """Calculate route between locations.

    Request body (POI to POI):
    ```json
    {
      "from": {
        "floor_id": "f5bb8f0d-ea83-4f30-864c-8d3c738f36f5",
        "lat": 30.02771092227816,
        "lng": 31.201406546960303
      },
      "to": {
        "poi_id": "694b1b35-754e-4086-a8f6-11290edfa56b"
      },
      "options": {
        "accessible": true
      }
    }
    ```

    Returns mobile-optimized route with:
    - distance in meters
    - estimated duration in seconds
    - turn-by-turn navigation steps
    - coordinate polyline (Mapbox format)
    - waypoints along route
    """
    try:
        from_loc = request.from_location
        to_loc = request.to_location
        opts = request.options or RouteOptionsModel()

        # Call orchestration layer
        service_response = await orchestrator.calculate_route(
            from_floor_id=from_loc.floor_id,
            from_lat=from_loc.lat,
            from_lng=from_loc.lng,
            to_poi_id=to_loc.poi_id,
            accessible=opts.accessible,
        )

        # Adapt to mobile format
        adapted = NavigationAdapter.adapt_route(service_response)

        logger.info(
            "Route calculated",
            extra={
                "from_floor": from_loc.floor_id,
                "to_poi": to_loc.poi_id,
                "distance": adapted.get("distance_meters"),
            },
        )

        return CalculateRouteResponse(**adapted)

    except ValueError as e:
        logger.warning(f"Invalid route request: {e}")
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        logger.error(f"Route calculation failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Route calculation failed")


@router.get("/nearby", summary="Find Nearby POIs")
async def find_nearby(
    floor_id: str,
    lat: float,
    lng: float,
    radius_meters: int = 50,
) -> dict:
    """Find POIs near a location.
    
    TODO (phase-2): Implement nearby POI search with caching.
    
    Args:
        floor_id: Floor UUID
        lat: Latitude
        lng: Longitude
        radius_meters: Search radius in meters
        
    Returns:
        List of nearby POIs with distances
    """
    raise HTTPException(status_code=501, detail="Nearby POI search not yet implemented")



