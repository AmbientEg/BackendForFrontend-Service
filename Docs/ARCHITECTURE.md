# BFF Service Architecture

## System Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          Mobile Clients                                 │
│                    (iOS, Android, Web)                                  │
└────────────────────────────┬────────────────────────────────────────────┘
                             │
                    HTTP/REST API Calls
                             │
┌────────────────────────────▼────────────────────────────────────────────┐
│                    API Gateway / Load Balancer                          │
│                    (Routes /bff/* requests)                             │
└────────────────────────────┬────────────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────────────┐
│                  BackendForFrontend-Service (FastAPI)                   │
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │                    Middleware Layer                              │  │
│  │  ┌─────────────────────────────────────────────────────────┐    │  │
│  │  │ • Request Logging (correlation IDs)                    │    │  │
│  │  │ • Exception Handling (global error handlers)           │    │  │
│  │  │ • CORS & Security Headers                             │    │  │
│  │  │ • Request Validation                                  │    │  │
│  │  └─────────────────────────────────────────────────────────┘    │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │                    Handlers Layer (HTTP)                         │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐           │  │
│  │  │ Buildings    │  │ Floors       │  │ Navigation   │           │  │
│  │  │ Handler      │  │ Handler      │  │ Handler      │           │  │
│  │  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘           │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐           │  │
│  │  │ POI          │  │ Position     │  │ Chatbot      │           │  │
│  │  │ Handler      │  │ Handler      │  │ Handler      │           │  │
│  │  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘           │  │
│  │         │                 │                 │                   │  │
│  │         └─────────────────┼─────────────────┘                   │  │
│  │                           │                                     │  │
│  └───────────────────────────┼─────────────────────────────────────┘  │
│                              │                                        │
│  ┌───────────────────────────▼─────────────────────────────────────┐  │
│  │                    Services Layer (Business Logic)              │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐           │  │
│  │  │ Building     │  │ Floor        │  │ Navigation   │           │  │
│  │  │ Service      │  │ Service      │  │ Service      │           │  │
│  │  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘           │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐           │  │
│  │  │ POI          │  │ Position     │  │ Chatbot      │           │  │
│  │  │ Service      │  │ Service      │  │ Service      │           │  │
│  │  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘           │  │
│  │         │                 │                 │                   │  │
│  │         └─────────────────┼─────────────────┘                   │  │
│  │                           │                                     │  │
│  └───────────────────────────┼─────────────────────────────────────┘  │
│                              │                                        │
│  ┌───────────────────────────▼─────────────────────────────────────┐  │
│  │                    Adapters Layer (Integration)                 │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐           │  │
│  │  │ Backend API  │  │ Navigation   │  │ Positioning  │           │  │
│  │  │ Client       │  │ Client       │  │ Client       │           │  │
│  │  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘           │  │
│  │  ┌──────────────┐  ┌──────────────┐                             │  │
│  │  │ Database     │  │ Chatbot      │                             │  │
│  │  │ Client       │  │ Client       │                             │  │
│  │  └──────┬───────┘  └──────┬───────┘                             │  │
│  │         │                 │                                     │  │
│  │         └─────────────────┼─────────────────────────────────────┘  │
│  │                           │                                        │
│  └───────────────────────────┼────────────────────────────────────────┘  │
│                              │                                        │
└──────────────────────────────┼────────────────────────────────────────┘
                               │
                ┌──────────────┼──────────────┬──────────────┐
                │              │              │              │
        ┌───────▼────┐  ┌──────▼──────┐  ┌──▼──────────┐  ┌─▼──────────┐
        │ Navigation │  │ Positioning │  │  Backend    │  │ Database   │
        │ Service    │  │  Service    │  │   API       │  │ (PostGIS)  │
        │ (Port 8010)│  │ (Port 8020) │  │ (Port 8030) │  │            │
        └────────────┘  └─────────────┘  └─────────────┘  └────────────┘
```

---

## Layered Architecture Detail

### 1. Handler Layer (HTTP Interface)

**Purpose:** Handle HTTP requests and responses

**Responsibilities:**
- Parse and validate incoming requests
- Call appropriate service
- Format and return responses
- Handle HTTP-specific concerns (status codes, headers)

**Files:**
- `app/handlers/buildings.py` - Building endpoints
- `app/handlers/floors.py` - Floor endpoints
- `app/handlers/navigation.py` - Navigation endpoints
- `app/handlers/poi.py` - POI endpoints
- `app/handlers/position.py` - Position endpoints

**Example Flow:**
```python
@router.get("/navigation/{start}/{end}")
async def get_route(
    start: str,
    end: str,
    floor_id: int,
    service: NavigationService = Depends(get_navigation_service)
):
    # 1. Parse and validate input
    # 2. Call service
    route = await service.calculate_route(start, end, floor_id)
    # 3. Format response
    return success_response(route)
```

---

### 2. Service Layer (Business Logic)

**Purpose:** Implement business logic and orchestration

**Responsibilities:**
- Validate business rules
- Coordinate between adapters
- Transform data
- Apply domain logic

**Files:**
- `app/services/building_service.py` - Building business logic
- `app/services/floor_service.py` - Floor business logic
- `app/services/navigation_service.py` - Navigation business logic
- `app/services/poi_service.py` - POI business logic
- `app/services/position_service.py` - Position business logic

**Example Flow:**
```python
class NavigationService:
    async def calculate_route(self, start, end, floor_id):
        # 1. Validate business rules
        building = await self.backend_adapter.get_building(floor_id)
        if not building:
            raise AppError("Building not found")
        
        # 2. Call adapters
        route = await self.navigation_adapter.calculate_route(
            start, end, floor_id
        )
        
        # 3. Transform response
        return self._format_route(route)
```

---

### 3. Adapter Layer (External Integration)

**Purpose:** Integrate with external services and databases

**Responsibilities:**
- Make HTTP calls to external services
- Handle database operations
- Error handling and retries
- Response transformation

**Files:**
- `app/adapters/backend_api_client.py` - Backend API integration
- `app/adapters/navigation_client.py` - Navigation service integration
- `app/adapters/positioning_client.py` - Positioning service integration
- `app/adapters/database_client.py` - Database operations

**Example Flow:**
```python
class NavigationClient:
    async def calculate_route(self, start, end, floor_id):
        # 1. Prepare request
        payload = {
            "start": start,
            "end": end,
            "floor_id": floor_id
        }
        
        # 2. Make HTTP call
        response = await self.http_client.post(
            f"{self.base_url}/api/navigation/route",
            json=payload
        )
        
        # 3. Handle errors
        if response.status_code != 200:
            raise AppError(f"Navigation service error: {response.text}")
        
        # 4. Return response
        return response.json()
```

---

### 4. Models Layer (Data Validation)

**Purpose:** Define and validate data structures

**Responsibilities:**
- Define request/response schemas
- Validate input data
- Serialize/deserialize data

**Files:**
- `app/models/schemas.py` - All Pydantic schemas

**Example:**
```python
class RouteRequest(BaseModel):
    start: Coordinates
    end: Coordinates
    floor_id: int
    options: Optional[RouteOptions] = None

class RouteResponse(BaseModel):
    distance: float
    duration: int
    steps: List[NavigationStep]
```

---

### 5. Utils Layer (Shared Utilities)

**Purpose:** Provide shared utilities and cross-cutting concerns

**Responsibilities:**
- Error handling
- Logging
- Response formatting
- Authentication

**Files:**
- `app/utils/errors.py` - Custom exceptions
- `app/utils/logging.py` - Structured logging
- `app/utils/responses.py` - Response formatting
- `app/utils/auth.py` - Authentication helpers

---

### 6. Core Layer (Configuration)

**Purpose:** Application configuration and settings

**Responsibilities:**
- Environment-based configuration
- Feature flags
- Service URLs
- Database connection

**Files:**
- `app/core/config.py` - Configuration management

---

## Data Flow Examples

### Example 1: Route Calculation

```
1. Mobile Client
   POST /bff/navigation/route
   {
     "start": {"lat": 40.7128, "lon": -74.0060},
     "end": {"lat": 40.7130, "lon": -74.0061},
     "floor_id": 123
   }

2. Handler (navigation.py)
   ├─ Validates request schema
   ├─ Calls NavigationService.calculate_route()
   └─ Returns formatted response

3. Service (navigation_service.py)
   ├─ Validates business rules (same building, etc.)
   ├─ Calls NavigationAdapter.calculate_route()
   └─ Transforms response

4. Adapter (navigation_client.py)
   ├─ Makes HTTP call to navigation-service
   ├─ Handles errors and retries
   └─ Returns raw response

5. Navigation Service (external)
   ├─ Loads active graph version
   ├─ Calculates route using Dijkstra/A*
   ├─ Generates navigation steps
   └─ Returns route with steps

6. Response Flow (reverse)
   ├─ Adapter returns response
   ├─ Service transforms response
   ├─ Handler formats response
   └─ Mobile Client receives route

Response:
{
  "status": "success",
  "data": {
    "distance": 150.5,
    "duration": 120,
    "steps": [...]
  }
}
```

### Example 2: Create Floor with GeoJSON

```
1. Mobile Client
   POST /bff/floors
   {
     "building_id": 1,
     "floor_number": 3,
     "geojson": {...}
   }

2. Handler (floors.py)
   ├─ Validates request schema
   ├─ Calls FloorService.create_floor()
   └─ Returns formatted response

3. Service (floor_service.py)
   ├─ Validates business rules
   ├─ Calls BackendAdapter.create_floor_metadata()
   ├─ Calls DatabaseAdapter.store_geojson()
   └─ Triggers graph rebuild

4. Adapters
   ├─ BackendAdapter: Creates floor metadata
   ├─ DatabaseAdapter: Stores GeoJSON
   └─ NavigationAdapter: Rebuilds graph

5. Response
   ├─ Service returns floor with metadata
   ├─ Handler formats response
   └─ Mobile Client receives floor details
```

---

## Request/Response Pattern

### Success Response
```json
{
  "status": "success",
  "data": {
    "id": 123,
    "name": "Floor 3",
    "building_id": 1
  }
}
```

### Error Response
```json
{
  "status": "error",
  "code": "VALIDATION_ERROR",
  "message": "Floor number must be positive"
}
```

### Error Codes
- `VALIDATION_ERROR` - Input validation failed
- `NOT_FOUND` - Resource not found
- `UNAUTHORIZED` - Authentication failed
- `FORBIDDEN` - Authorization failed
- `CONFLICT` - Resource conflict
- `INTERNAL_ERROR` - Server error
- `SERVICE_UNAVAILABLE` - External service unavailable

---

## Dependency Injection

### Current Implementation

```python
# app/dependencies.py
async def get_navigation_service() -> NavigationService:
    adapter = NavigationClient(base_url=settings.navigation_service_url)
    return NavigationService(adapter)

# app/handlers/navigation.py
@router.get("/navigation/{start}/{end}")
async def get_route(
    service: NavigationService = Depends(get_navigation_service)
):
    # Use service
    pass
```

### Benefits
- Easy to mock for testing
- Centralized dependency management
- Easy to swap implementations
- Supports async initialization

---

## Error Handling Strategy

### Exception Hierarchy
```
Exception
├── AppError (custom)
│   ├── ValidationError
│   ├── NotFoundError
│   ├── UnauthorizedError
│   ├── ForbiddenError
│   ├── ConflictError
│   └── ServiceUnavailableError
└── Other exceptions (caught by global handler)
```

### Error Handling Flow
```
1. Handler receives request
2. Validates input (Pydantic)
   └─ ValidationError → 422 Unprocessable Entity
3. Calls service
   └─ AppError → Formatted error response
4. Calls adapter
   └─ HTTP error → Retry or AppError
5. Returns response
   └─ Unhandled exception → 500 Internal Server Error
```

---

## Logging Strategy

### Structured Logging
```python
await log_event_async(
    logger=logger,
    level="INFO",
    event="route_calculated",
    payload={
        "building_id": 1,
        "floor_id": 3,
        "distance": 150.5,
        "duration": 120,
        "correlation_id": "abc123"
    }
)
```

### Log Levels
- `DEBUG` - Detailed information for debugging
- `INFO` - General informational messages
- `WARNING` - Warning messages for potential issues
- `ERROR` - Error messages for failures
- `CRITICAL` - Critical errors requiring immediate attention

---

## Security Architecture

### Authentication
- API token validation for admin endpoints
- JWT support for future user authentication
- Token passed in `Authorization` header

### Authorization
- Role-based access control (RBAC)
- Resource-level permissions
- Audit logging for sensitive operations

### Data Protection
- HTTPS for all communications
- Input validation (Pydantic)
- Output sanitization
- SQL injection prevention (SQLAlchemy ORM)

### API Security
- CORS configuration
- Security headers (CSP, X-Frame-Options, etc.)
- Rate limiting (future)
- Request signing (future)

---

## Scalability Architecture

### Horizontal Scaling
- Stateless design (no in-memory state)
- Load balancing across instances
- Shared database (PostgreSQL)
- Shared cache (Redis, optional)

### Vertical Scaling
- Async/await for non-blocking I/O
- Connection pooling
- Query optimization
- Response compression

### Caching Strategy
- Cache frequently accessed data (buildings, floors)
- Cache active graph versions
- Cache POI data
- Implement cache invalidation

---

## Deployment Architecture

### Local Development
```
Developer Machine
├─ BFF Service (uvicorn)
├─ Navigation Service (uvicorn)
├─ Positioning Service (uvicorn)
├─ Backend API (mock or real)
└─ PostgreSQL (local or Docker)
```

### Docker Deployment
```
Docker Host
├─ BFF Service Container
├─ Navigation Service Container
├─ Positioning Service Container
├─ PostgreSQL Container
└─ Redis Container (optional)
```

### AWS Lambda Deployment
```
AWS
├─ Lambda Function (BFF Service)
├─ API Gateway (routing)
├─ RDS (PostgreSQL)
├─ ElastiCache (Redis, optional)
└─ External Services (Navigation, Positioning, Backend)
```

### Kubernetes Deployment
```
Kubernetes Cluster
├─ BFF Service Deployment
├─ Navigation Service Deployment
├─ Positioning Service Deployment
├─ PostgreSQL StatefulSet
├─ Redis StatefulSet (optional)
└─ Ingress (routing)
```

---

## Monitoring & Observability

### Metrics
- Request count and latency
- Error rate and types
- Service availability
- Database connection pool stats
- Cache hit/miss rates

### Logging
- Structured logging with correlation IDs
- Request/response logging
- Error logging with full context
- Performance logging

### Tracing
- Distributed tracing with correlation IDs
- Trace requests across services
- Track latency at each layer

### Alerting
- Alert on high error rates
- Alert on service unavailability
- Alert on high latency
- Alert on database issues

---

## Technology Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Framework** | FastAPI | Async Python web framework |
| **Server** | Uvicorn | ASGI server |
| **HTTP Client** | httpx | Async HTTP client |
| **Database** | PostgreSQL + PostGIS | Spatial database |
| **ORM** | SQLAlchemy | Database abstraction |
| **Validation** | Pydantic | Data validation |
| **Logging** | Python logging | Structured logging |
| **Testing** | pytest | Test framework |
| **Deployment** | Mangum | Lambda adapter |
| **Containerization** | Docker | Container image |
| **Orchestration** | Kubernetes | Container orchestration |

---

## Future Enhancements

### Short Term (1-2 months)
- [ ] Comprehensive test suite
- [ ] API documentation
- [ ] Docker configuration
- [ ] CI/CD pipelines

### Medium Term (2-4 months)
- [ ] Caching layer (Redis)
- [ ] Error recovery (circuit breaker)
- [ ] Request tracing
- [ ] API versioning

### Long Term (4+ months)
- [ ] GraphQL interface
- [ ] WebSocket support
- [ ] Analytics dashboard
- [ ] Advanced monitoring

---

*Last Updated: March 2026*
