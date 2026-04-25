# Backend For Frontend Service

Version 1 of the Backend For Frontend service for the indoor navigation stack. This service sits in front of the navigation and positioning APIs, shapes responses for mobile clients, adds resilience, and uses Redis-backed caching for the flows that need it most.

## What this service does

- Proxies and orchestrates requests to the downstream navigation and positioning services.
- Exposes mobile-focused read endpoints for floor maps and POIs.
- Caches expensive or fast-changing data such as routes, floor maps, and position lookups.
- Applies resilience policies around downstream HTTP calls.
- Adds request tracing, structured error responses, CORS, and optional trusted-host enforcement.

## Repository layout

- `app/main.py` creates the FastAPI app, wires middleware, and initializes shared clients.
- `app/api/navigation.py` exposes route calculation and navigation health endpoints.
- `app/api/positioning.py` exposes positioning health and prediction endpoints.
- `app/api/admin.py` forwards admin operations for buildings, floors, graphs, POIs, and grid import.
- `app/api/client_map.py` serves mobile map reads for floors, floor maps, and POIs.
- `app/clients/` contains the downstream HTTP clients.
- `app/orchestration/` contains the orchestration logic.
- `app/cache/` contains Redis access and route/position cache helpers.
- `tests/` contains the current automated test suite.

## Runtime behavior

- FastAPI app title: `Backend For Frontend (BFF) API`
- Default app version: `1.0.0`
- Default server host: `0.0.0.0`
- Default server port: `8003`
- Production mode disables the interactive docs and enables trusted-host checks when configured.
- Requests include an `X-Correlation-ID` header if provided, or a generated request ID otherwise.

## Environment variables

The service reads the following variables:

- `ENV` or `ENVIRONMENT` - set to `production` to enable production-only behavior.
- `LOG_LEVEL` - logging level, default `INFO`.
- `REDIS_URL` - Redis connection string, default `redis://localhost:6379/0`.
- `NAVIGATION_SERVICE_URL` - navigation service base URL, default `http://navigation-service:8000`.
- `POSITIONING_SERVICE_URL` - positioning service base URL, default `http://positioning-service:8000`.
- `ALLOWED_HOSTS` - comma-separated host list for trusted-host middleware.
- `CORS_ORIGINS` - comma-separated allowed CORS origins.
- `HOST` - host used by the `__main__` launcher, default `0.0.0.0`.
- `PORT` - port used by the `__main__` launcher, default `8003`.

## Local development

Install dependencies from `requirements.txt`, then run the app from the repository root:

```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8003 --reload
```

If you prefer the module entrypoint, the app also supports direct execution through `python app/main.py`.

## Docker

The repository includes two Docker-related entrypoints:

- `Dockerfile` builds the BFF image from the repository root.
- `docker/docker-compose.yml` starts the BFF together with Redis, navigation, and positioning containers.

Compose expects environment files next to it:

- `docker/bff.env`
- `docker/navigation.env`
- `docker/positioning.env`

To run the stack with Docker Compose, use the compose file under `docker/` and expose the BFF on host port `8003`.

## API surface

### App-level endpoints

- `GET /` - service status and docs link in non-production mode.
- `GET /health` - liveness-style health check for the API process.
- `GET /api/status` - lightweight operational status endpoint.

### Navigation endpoints

- `GET /api/navigation/` - navigation service root proxy.
- `GET /api/navigation/health` - navigation health proxy.
- `GET /api/navigation/health/ready` - navigation readiness proxy.
- `GET /api/navigation/health/live` - navigation liveness proxy.
- `GET /api/navigation/status` - navigation status proxy.
- `POST /api/navigation/get/route` - calculate a route, including multipart uploads when needed.

### Positioning endpoints

- `GET /api/position/` - positioning service root proxy.
- `GET /api/position/health` - positioning health proxy.
- `GET /api/position/health/live` - positioning liveness proxy.
- `GET /api/position/health/ready` - positioning readiness proxy.
- `POST /api/position/predict` - predict positioning from JSON or multipart form data.

### Admin endpoints

- `POST /api/admin/buildings/create`
- `GET /api/admin/buildings/get/{building_id}`
- `GET /api/admin/buildings/get/{building_id}/floors`
- `POST /api/admin/floors/create`
- `PUT /api/admin/floors/{floor_id}`
- `POST /api/admin/graphs/rebuild/{building_id}`
- `POST /api/admin/graphs/confirm/{building_id}`
- `POST /api/admin/graphs/rollback/{building_id}`
- `PUT /api/admin/pois/{poi_id}`
- `DELETE /api/admin/pois/{poi_id}`
- `POST /api/admin/position/grid/import`

### Mobile map endpoints

- `GET /api/buildings/get/{building_id}/floors`
- `GET /api/floors/get/{floor_id}/map`
- `GET /api/pois/floor/{floor_id}`

## Caching and resilience

- Route responses can be cached in Redis through the route cache helpers.
- Floor map and floor POI reads use short-lived Redis cache entries.
- Positioning flows can fall back to cached data when the live service is unavailable.
- Downstream clients use resilience policies and normalized error handling for HTTP failures.

## Testing

Run the test suite from the repository root:

```bash
pytest
```

The current tests cover positioning orchestration, admin multipart forwarding, downstream client health paths, and resilience-related behavior.

## Notes for contributors

- Keep `.env` values and local machine state out of version control.
- Prefer small, focused changes in `app/` when adjusting endpoint behavior.
- Update this README when new routes, environment variables, or runtime entrypoints are added.
