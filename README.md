# BackendForFrontend-Service

Starter FastAPI BFF skeleton with modular architecture, Lambda readiness, and standardized API responses.

## Architecture

- `app/handlers/`: API endpoint handlers (routing and input/output handling)
- `app/services/`: business logic
- `app/adapters/`: integration layer for backend APIs, navigation/positioning services, and DB clients
- `app/utils/`: shared helpers (responses, errors, structured logging)
- `app/models/`: request/response schemas
- `app/core/`: app configuration

## Implemented Endpoints

- `POST /bff/buildings` create building
- `POST /bff/floors` add floor with GeoJSON
- `GET /bff/poi/{floor_id}` list POI for floor
- `POST /bff/poi` add/update POI
- `GET /bff/navigation/{start}/{end}` get path between nodes
- `GET /bff/position/{device_id}` get current device position
- `GET /health` health check

## Request/Response Pattern

Success

```json
{
  "status": "success",
  "data": {}
}
```

Error

```json
{
  "status": "error",
  "code": "VALIDATION_ERROR",
  "message": "..."
}
```

## Example Flow (Handler -> Service -> Adapter)

### Create Building

1. `app/handlers/buildings.py` validates request and calls `BuildingService`.
2. `app/services/building_service.py` applies business logic and prepares payload.
3. `app/adapters/backend_api_client.py` calls backend API (or mock mode).

### Add Floor with GeoJSON

1. `app/handlers/floors.py` receives floor request.
2. `app/services/floor_service.py` orchestrates metadata + GeoJSON persistence.
3. `app/adapters/backend_api_client.py` creates floor metadata.
4. `app/adapters/database_client.py` stores GeoJSON and returns URL.

## Local Run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

Open Swagger UI at `http://127.0.0.1:8000/docs`.

## AWS Lambda

`app/main.py` exposes a Lambda-compatible handler:

- `handler = Mangum(app)`

Use this handler in Lambda runtime config and route through API Gateway.

## Notes

- Stateless design: no in-memory session state.
- Configure secrets and service URLs via environment variables.
- `MOCK_EXTERNALS=true` allows testing without downstream services.
