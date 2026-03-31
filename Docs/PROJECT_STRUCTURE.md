# BackendForFrontend-Service Project Structure

## Overview
The BFF (Backend-for-Frontend) Service is an orchestration layer that aggregates multiple backend services (Navigation, Positioning, Chatbot) and exposes unified APIs for mobile clients. It follows a clean architecture pattern with clear separation of concerns.

---

## Directory Tree with Descriptions

```
BackendForFrontend-Service/
│
├── .env.example                          # Template for environment variables (DATABASE_URL, service URLs, API tokens)
├── .git/                                 # Git version control directory
├── README.md                             # Quick start guide and architecture overview
├── requirements.txt                      # Python dependencies (FastAPI, Mangum, etc.)
│
└── app/                                  # Main application package
    │
    ├── __init__.py                       # Package initialization
    ├── main.py                           # FastAPI app entry point with middleware, exception handlers, Lambda handler
    ├── dependencies.py                   # Dependency injection and lifecycle management (adapter initialization/shutdown)
    │
    ├── core/                             # Application configuration and settings
    │   ├── __init__.py
    │   └── config.py                     # Environment-based configuration (log level, service URLs, feature flags)
    │
    ├── models/                           # Request/Response schemas (Pydantic models)
    │   ├── __init__.py
    │   └── schemas.py                    # Data validation schemas for all endpoints
    │
    ├── handlers/                         # API endpoint handlers (routing layer)
    │   ├── __init__.py
    │   ├── buildings.py                  # POST/GET endpoints for building management
    │   ├── floors.py                     # POST/GET endpoints for floor management with GeoJSON
    │   ├── navigation.py                 # GET endpoints for route calculation and pathfinding
    │   ├── poi.py                        # POST/GET endpoints for Points of Interest management
    │   └── position.py                   # GET endpoints for device positioning and location tracking
    │
    ├── services/                         # Business logic layer (orchestration and validation)
    │   ├── __init__.py
    │   ├── building_service.py           # Building creation, validation, and metadata management
    │   ├── floor_service.py              # Floor management, GeoJSON processing, and storage coordination
    │   ├── navigation_service.py         # Route calculation orchestration, calls navigation adapter
    │   ├── poi_service.py                # POI CRUD operations and floor association logic
    │   └── position_service.py           # Device positioning logic, calls positioning adapter
    │
    ├── adapters/                         # External service integration layer
    │   ├── __init__.py
    │   ├── backend_api_client.py         # HTTP client for backend API calls (buildings, floors, POIs)
    │   ├── database_client.py            # Database operations for GeoJSON and metadata persistence
    │   ├── navigation_client.py          # HTTP client for navigation service (routing, graph management)
    │   └── positioning_client.py         # HTTP client for positioning service (device location tracking)
    │
    └── utils/                            # Shared utilities and helpers
        ├── __init__.py
        ├── auth.py                       # Authentication and authorization helpers (token validation, permissions)
        ├── errors.py                     # Custom exception classes (AppError, ValidationError, etc.)
        ├── logging.py                    # Structured logging configuration and utilities
        └── responses.py                  # Standardized response formatting (success/error response builders)
```

---

## Architecture Layers

### 1. **Handlers Layer** (`app/handlers/`)
- **Purpose:** HTTP request/response handling and routing
- **Responsibility:** Validate input, call services, format responses
- **Pattern:** Each handler file corresponds to a domain (buildings, floors, navigation, etc.)
- **No business logic** - delegates to services

### 2. **Services Layer** (`app/services/`)
- **Purpose:** Business logic and orchestration
- **Responsibility:** Validate business rules, coordinate between adapters, apply transformations
- **Pattern:** Service per domain entity
- **Stateless** - no in-memory state persistence

### 3. **Adapters Layer** (`app/adapters/`)
- **Purpose:** External service integration
- **Responsibility:** HTTP calls to backend services, database operations, error handling
- **Pattern:** Adapter per external system (backend API, navigation service, positioning service, database)
- **Abstraction:** Hides implementation details of external services

### 4. **Models Layer** (`app/models/`)
- **Purpose:** Data validation and serialization
- **Responsibility:** Pydantic schemas for request/response validation
- **Pattern:** Schemas organized by domain

### 5. **Utils Layer** (`app/utils/`)
- **Purpose:** Shared utilities and cross-cutting concerns
- **Responsibility:** Logging, error handling, response formatting, authentication
- **Pattern:** Utility modules for specific concerns

### 6. **Core Layer** (`app/core/`)
- **Purpose:** Application configuration
- **Responsibility:** Environment-based settings, feature flags, service URLs
- **Pattern:** Centralized configuration management

---

## Data Flow Example: Route Calculation

```
Mobile Client
    ↓
[Handler] navigation.py
    ├─ Validates request (start, end coordinates)
    ├─ Calls NavigationService
    ↓
[Service] navigation_service.py
    ├─ Applies business logic (same building check, etc.)
    ├─ Calls NavigationAdapter
    ↓
[Adapter] navigation_client.py
    ├─ Makes HTTP call to navigation-service
    ├─ Handles errors and retries
    ↓
[Response] Formatted via responses.py
    ↓
Mobile Client (route with steps, distance, duration)
```

---

## Key Design Patterns

### 1. **Dependency Injection**
- Adapters initialized in `dependencies.py`
- Injected into handlers via FastAPI dependency system
- Enables easy mocking for testing

### 2. **Standardized Responses**
- All endpoints return consistent format:
  ```json
  {
    "status": "success|error",
    "data": {},
    "code": "ERROR_CODE",
    "message": "Human-readable message"
  }
  ```

### 3. **Error Handling**
- Custom `AppError` exception for business logic errors
- Global exception handlers in `main.py`
- Structured error logging with correlation IDs

### 4. **Middleware**
- Request logging middleware for tracing
- Exception handlers for graceful error responses
- CORS and security headers (configurable)

### 5. **Lambda Readiness**
- `Mangum` adapter for AWS Lambda compatibility
- Stateless design (no in-memory session state)
- Environment-based configuration

---

## Service Integration Points

### Navigation Service
- **Adapter:** `navigation_client.py`
- **Endpoints Used:**
  - `POST /api/graphs/rebuild/{building_id}` - Build graph preview
  - `POST /api/graphs/confirm/{building_id}` - Activate graph version
  - `GET /api/navigation/route` - Calculate route
  - `GET /api/graphs/{building_id}/active` - Get active graph

### Positioning Service
- **Adapter:** `positioning_client.py`
- **Endpoints Used:**
  - `GET /api/position/{device_id}` - Get device location
  - `POST /api/position` - Update device position

### Backend API
- **Adapter:** `backend_api_client.py`
- **Endpoints Used:**
  - Building CRUD operations
  - Floor metadata management
  - POI management

### Database
- **Adapter:** `database_client.py`
- **Operations:**
  - GeoJSON storage and retrieval
  - Metadata persistence
  - Query operations

---

## Configuration

### Environment Variables (.env)
```
# Service URLs
NAVIGATION_SERVICE_URL=http://localhost:8010
POSITIONING_SERVICE_URL=http://localhost:8020
BACKEND_API_URL=http://localhost:8030

# Database
DATABASE_URL=postgresql://user:pass@localhost/bff_db

# Application
APP_NAME=BackendForFrontend-Service
APP_VERSION=1.0.0
ENVIRONMENT=development
LOG_LEVEL=INFO

# Feature Flags
MOCK_EXTERNALS=false
ENABLE_CACHING=true

# Security
ADMIN_API_TOKEN=your-secret-token
CORS_ORIGINS=*
```

---

## Running the Application

### Local Development
```bash
# Setup
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -r requirements.txt

# Configure
cp .env.example .env
# Edit .env with your service URLs and database connection

# Run
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

### AWS Lambda
- Use `handler = Mangum(app)` from `main.py`
- Configure Lambda runtime with handler: `app.main.handler`
- Route through API Gateway with `/bff/*` path

### Docker
```bash
docker build -t bff-service .
docker run -p 8000:8000 --env-file .env bff-service
```

---

## API Endpoints Summary

### Buildings
- `POST /bff/buildings` - Create building
- `GET /bff/buildings/{building_id}` - Get building details
- `GET /bff/buildings` - List buildings

### Floors
- `POST /bff/floors` - Create floor with GeoJSON
- `GET /bff/floors/{floor_id}` - Get floor details
- `PUT /bff/floors/{floor_id}` - Update floor GeoJSON

### Navigation
- `GET /bff/navigation/{start}/{end}` - Calculate route between points
- `GET /bff/navigation/nearest-node` - Find nearest navigation node

### POI (Points of Interest)
- `POST /bff/poi` - Create/update POI
- `GET /bff/poi/{floor_id}` - List POIs for floor
- `GET /bff/poi/{poi_id}` - Get POI details

### Position
- `GET /bff/position/{device_id}` - Get device position
- `POST /bff/position` - Update device position

### Health
- `GET /health` - Health check

---

## Testing Strategy

### Unit Tests
- Test services in isolation with mocked adapters
- Test handlers with mocked services
- Test utility functions

### Integration Tests
- Test full request flow (handler → service → adapter)
- Mock external services
- Verify response formatting

### E2E Tests
- Test against real services (navigation, positioning, backend)
- Verify end-to-end workflows

---

## Deployment Checklist

- [ ] Environment variables configured
- [ ] Database migrations run
- [ ] External services accessible
- [ ] Logging configured
- [ ] Error handling tested
- [ ] Security headers configured
- [ ] CORS origins configured
- [ ] Lambda handler tested (if deploying to AWS)
- [ ] Health checks passing
- [ ] Load testing completed

---

## Future Enhancements

1. **Caching Layer** - Redis for frequently accessed data
2. **Rate Limiting** - Prevent abuse and ensure fair usage
3. **API Versioning** - Support multiple API versions
4. **GraphQL** - Alternative query interface
5. **WebSocket Support** - Real-time position updates
6. **Analytics** - Track usage patterns and performance
7. **Circuit Breaker** - Graceful degradation when services fail
8. **Request Tracing** - Distributed tracing with correlation IDs

---

*Last Updated: March 2026*
