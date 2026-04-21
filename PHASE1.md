# Phase 1: Navigation Integration - What You Need to Do

Based on PLAN.md Phase 1, here's exactly what needs to be implemented for the Navigation feature (without code):

---

## 🎯 Phase 1 Overview

**Goal:** Integrate the Navigation Service into the BFF so mobile clients can calculate routes between points in buildings.

**Duration:** 2-3 weeks

**Deliverables:**
- Fully functional navigation endpoints
- Test coverage > 80%
- API documentation
- Integration guide

---

## 📋 Phase 1 Tasks Breakdown

### Task 1.1: Implement Navigation Service Adapter
**File:** `app/adapters/navigation_client.py`

**What it needs to do:**
- Create an HTTP client that calls the navigation-service (running on port 8010)
- Implement method to call: `POST /api/navigation/route` (for route calculation)
- Implement methods to call graph management endpoints:
  - `GET /api/graphs/{building_id}/active` (get active graph version)
  - `POST /api/graphs/rebuild/{building_id}` (build preview graph)
  - `POST /api/graphs/confirm/{building_id}` (activate new graph version)
- Handle errors and retries
- Transform responses to BFF format

**Key responsibilities:**
- Make HTTP calls to navigation-service
- Handle timeouts and connection errors
- Parse responses
- Return data to NavigationService

---

### Task 1.2: Enhance Navigation Service Business Logic
**File:** `app/services/navigation_service.py`

**What it needs to do:**
- Validate business rules:
  - Start and end points must be in the same building
  - Floor must exist and belong to the building
  - Active graph version must exist for the building
- Call NavigationAdapter to calculate route
- Transform navigation-service response into BFF response format
- Handle errors and provide meaningful messages

**Key responsibilities:**
- Apply business logic
- Validate inputs
- Coordinate between handler and adapter
- Transform data

---

### Task 1.3: Update Navigation Handler
**File:** `app/handlers/navigation.py`

**What it needs to do:**
- Implement endpoint: `GET /bff/navigation/{start}/{end}`
  - Accept query parameters: `floor_id`, `options` (optional)
  - Validate request using Pydantic schemas
  - Call NavigationService
  - Return formatted response
- Implement endpoint: `GET /bff/navigation/nearest-node`
  - Accept query parameters: `lat`, `lon`, `floor_id`
  - Find nearest navigation node
  - Return node details

**Key responsibilities:**
- Parse HTTP requests
- Validate input schemas
- Call services
- Format responses

---

### Task 1.4: Add Navigation Schemas
**File:** `app/models/schemas.py`

**What it needs to do:**
- Create Pydantic request schemas:
  - `RouteRequest` - for route calculation (start, end, floor_id, options)
  - `NearestNodeRequest` - for finding nearest node (lat, lon, floor_id)
- Create Pydantic response schemas:
  - `RouteResponse` - route with steps, distance, duration
  - `NavigationStepResponse` - individual step (instruction, distance, duration)
  - `NodeResponse` - node details (id, coordinates, type, distance)
  - `GraphVersionResponse` - graph version info

**Key responsibilities:**
- Define data structures
- Validate input/output
- Provide type hints

---

### Task 1.5: Write Unit Tests
**File:** `tests/unit/test_navigation_service.py` and `tests/unit/test_handlers/test_navigation.py`

**What it needs to test:**
- NavigationService:
  - Route calculation with valid inputs
  - Route calculation with invalid inputs (different buildings, no graph, etc.)
  - Error handling
  - Response transformation
- NavigationHandler:
  - Route endpoint with valid request
  - Route endpoint with invalid request
  - Nearest node endpoint
  - Error responses

**Key responsibilities:**
- Mock NavigationAdapter
- Test business logic
- Test error handling
- Verify response format

---

### Task 1.6: Write Integration Tests
**File:** `tests/integration/test_workflows/test_navigation_workflow.py`

**What it needs to test:**
- Full request flow: Handler → Service → Adapter
- Mock navigation-service responses
- Verify end-to-end behavior
- Test error scenarios

**Key responsibilities:**
- Test complete workflows
- Mock external services
- Verify response formatting

---

### Task 1.7: Implement Redis Caching
**File:** `app/adapters/cache_client.py` (new file)

**What it needs to do:**
- Create a Redis cache client for caching frequently accessed data
- Implement cache methods:
  - `get_cached(key)` - Retrieve cached data
  - `set_cached(key, value, ttl)` - Store data with TTL (Time To Live)
  - `delete_cached(key)` - Remove cached data
  - `clear_cache()` - Clear all cache
- Cache the following in Phase 1:
  - **Active graph versions** - Cache for 1 hour (3600 seconds)
    - Key: `graph:active:{building_id}`
    - Value: Graph version info
  - **Building data** - Cache for 24 hours (86400 seconds)
    - Key: `building:{building_id}`
    - Value: Building metadata
  - **Floor data** - Cache for 24 hours
    - Key: `floor:{floor_id}`
    - Value: Floor metadata
- Handle cache misses gracefully
- Implement cache invalidation when data is updated

**Key responsibilities:**
- Connect to Redis
- Store and retrieve cached data
- Handle cache expiration
- Invalidate cache when needed

**Integration points:**
- NavigationService: Cache active graph versions before calling adapter
- NavigationAdapter: Check cache before making HTTP calls
- BuildingService: Cache building data
- FloorService: Cache floor data

**Cache Strategy:**
```
Route Calculation Flow:
1. Check if active graph is cached
2. If cached, use it
3. If not cached, call adapter
4. Cache the result with TTL
5. Return to client

Building/Floor Lookup:
1. Check if data is cached
2. If cached, use it
3. If not cached, fetch from backend
4. Cache the result with TTL
5. Return to client
```

---

### Task 1.8: Create API Documentation
**File:** `docs/API.md` (new file)

**What it needs to document:**
- Route calculation endpoint:
  - Request format with example
  - Response format with example
  - Error scenarios
  - Query parameters
- Nearest node endpoint:
  - Request format with example
  - Response format with example
  - Error scenarios
- Integration guide:
  - How to use the endpoints
  - Example workflows
  - Error handling
- Caching strategy:
  - What data is cached
  - Cache TTL values
  - Cache invalidation

**Key responsibilities:**
- Document endpoints
- Provide examples
- Explain error codes
- Document caching behavior

---

## 🔄 Data Flow for Route Calculation

```
1. Mobile Client
   GET /bff/navigation/start/end?floor_id=123

2. Handler (navigation.py)
   ├─ Validates request schema
   ├─ Extracts parameters
   └─ Calls NavigationService.calculate_route()

3. Service (navigation_service.py)
   ├─ Check Redis cache for active graph
   │  ├─ If cached: Use cached graph
   │  └─ If not cached: Continue to step 4
   ├─ Validates business rules
   │  ├─ Check floor exists
   │  ├─ Check building has active graph
   │  └─ Check start/end in same building
   ├─ Calls NavigationAdapter.calculate_route()
   ├─ Cache the result in Redis
   └─ Transforms response

4. Adapter (navigation_client.py)
   ├─ Makes HTTP call to navigation-service
   │  POST /api/navigation/route
   ├─ Handles errors
   └─ Returns response

5. Navigation Service (external, port 8010)
   ├─ Loads active graph version
   ├─ Calculates route using Dijkstra/A*
   ├─ Generates navigation steps
   └─ Returns route with steps

6. Response (reverse flow)
   ├─ Adapter returns response
   ├─ Service transforms response
   ├─ Handler formats response
   └─ Mobile Client receives route
```

---

## 🔴 Redis Caching Flow

```
Route Calculation with Caching:

1. Service receives request
   ↓
2. Check Redis: graph:active:{building_id}
   ├─ Cache HIT → Use cached graph, skip adapter call
   └─ Cache MISS → Continue to step 3
   ↓
3. Call NavigationAdapter
   ↓
4. Adapter calls navigation-service
   ↓
5. Get response from navigation-service
   ↓
6. Store in Redis with TTL (1 hour)
   ├─ Key: graph:active:{building_id}
   └─ Value: Graph version info
   ↓
7. Return response to client

Performance Impact:
- Cache HIT: ~10ms (Redis lookup)
- Cache MISS: ~500ms (HTTP call to navigation-service)
- Average with 80% hit rate: ~110ms
```

---

## 📊 What Each Component Does

### Handler (HTTP Layer)
- **Input:** HTTP request with coordinates and floor_id
- **Output:** Formatted JSON response
- **Responsibility:** Validate request, call service, format response

### Service (Business Logic Layer)
- **Input:** Validated request data
- **Output:** Transformed response
- **Responsibility:** Apply business rules, coordinate adapters

### Adapter (Integration Layer)
- **Input:** Request data from service
- **Output:** Response from navigation-service
- **Responsibility:** Make HTTP calls, handle errors

---

## 🔌 Integration Points

### With Navigation Service (external, port 8010)
- **Endpoint:** `POST /api/navigation/route`
  - Input: `{start, end, floor_id, options}`
  - Output: `{distance, duration, steps}`
- **Endpoint:** `GET /api/graphs/{building_id}/active`
  - Output: Active graph version info
- **Endpoint:** `POST /api/graphs/rebuild/{building_id}`
  - Rebuild graph preview
- **Endpoint:** `POST /api/graphs/confirm/{building_id}`
  - Activate new graph version

### With Backend API (external, port 8030)
- Verify building exists
- Verify floor exists and belongs to building

### With Database
- Store metadata (buildings, floors)
- Query active graph versions

---

## ✅ Success Criteria for Phase 1

- [ ] Navigation adapter implemented and tested
- [ ] Navigation service business logic implemented and tested
- [ ] Navigation handler endpoints implemented and tested
- [ ] Navigation schemas defined and validated
- [ ] Redis cache client implemented and tested
- [ ] Caching integrated into navigation flow
- [ ] Unit tests written (> 80% coverage)
- [ ] Integration tests written
- [ ] API documentation created
- [ ] All endpoints working with navigation-service
- [ ] Caching working correctly (verified with cache hits)
- [ ] Error handling working correctly
- [ ] Response format consistent with BFF standard

---

## 📝 Response Format Examples

### Route Calculation Success
```json
{
  "status": "success",
  "data": {
    "distance": 150.5,
    "duration": 120,
    "steps": [
      {
        "instruction": "Head north",
        "distance": 50,
        "duration": 40
      },
      {
        "instruction": "Turn right",
        "distance": 100,
        "duration": 80
      }
    ]
  }
}
```

### Route Calculation Error
```json
{
  "status": "error",
  "code": "NOT_FOUND",
  "message": "Floor not found"
}
```

---

## 🚀 Implementation Order

1. **First:** Create navigation schemas (models/schemas.py)
2. **Second:** Create Redis cache client (adapters/cache_client.py)
3. **Third:** Create navigation adapter (adapters/navigation_client.py)
4. **Fourth:** Create navigation service (services/navigation_service.py)
5. **Fifth:** Update navigation handler (handlers/navigation.py)
6. **Sixth:** Write unit tests (tests/unit/)
7. **Seventh:** Write integration tests (tests/integration/)
8. **Eighth:** Create API documentation (docs/API.md)

---

## 🔑 Key Points to Remember

1. **Handler validates input** - Use Pydantic schemas
2. **Service applies business logic** - Validate rules, coordinate adapters
3. **Adapter makes external calls** - Handle errors, transform responses
4. **Cache frequently accessed data** - Use Redis for performance
5. **Stateless design** - No in-memory state
6. **Async/await** - All I/O operations are async
7. **Error handling** - Use custom AppError exceptions
8. **Structured logging** - Log all important events
9. **Standardized responses** - Always use success/error format

---

## 🔴 Redis Configuration

### Environment Variables
Add to `.env`:
```
REDIS_URL=redis://localhost:6379
REDIS_DB=0
CACHE_ENABLED=true
CACHE_TTL_GRAPH=3600          # 1 hour for graph versions
CACHE_TTL_BUILDING=86400      # 24 hours for building data
CACHE_TTL_FLOOR=86400         # 24 hours for floor data
```

### Cache Keys
```
graph:active:{building_id}     # Active graph version
building:{building_id}         # Building metadata
floor:{floor_id}               # Floor metadata
```

### Cache TTL Values
- **Graph versions:** 1 hour (3600 seconds) - Changes frequently
- **Building data:** 24 hours (86400 seconds) - Changes rarely
- **Floor data:** 24 hours (86400 seconds) - Changes rarely

### Cache Invalidation
- Invalidate graph cache when graph is rebuilt/confirmed
- Invalidate building cache when building is updated
- Invalidate floor cache when floor is updated

### Local Development
```bash
# Install Redis (macOS)
brew install redis

# Start Redis
redis-server

# Or use Docker
docker run -d -p 6379:6379 redis:latest
```

---

## 📚 Reference Files

- **Navigation Service Overview:** See `navigation-service/PROJECT_OVERVIEW.md`
- **Architecture Patterns:** See `ARCHITECTURE.md` in BFF
- **Implementation Details:** See `PLAN.md` Phase 1 section
- **Code Examples:** See existing handlers/services/adapters

---

## 📦 Dependencies to Add

Add these to `requirements.txt`:

```
# Existing
fastapi>=0.100.0
pydantic>=2.0.0
sqlalchemy>=2.0.0
asyncpg>=0.28.0
httpx>=0.24.0
mangum>=0.20.0

# New for Redis caching
redis>=5.0.0
aioredis>=2.0.0
```

### Installation
```bash
pip install redis aioredis
```

### Async Redis Client
Use `aioredis` for async Redis operations (non-blocking I/O)

---

## 📋 Task Checklist

### Schemas (Task 1.4)
- [ ] RouteRequest schema
- [ ] NearestNodeRequest schema
- [ ] RouteResponse schema
- [ ] NavigationStepResponse schema
- [ ] NodeResponse schema
- [ ] GraphVersionResponse schema

### Cache Client (Task 1.7)
- [ ] CacheClient class
- [ ] Redis connection setup
- [ ] get_cached() method
- [ ] set_cached() method
- [ ] delete_cached() method
- [ ] clear_cache() method
- [ ] Error handling for cache failures
- [ ] Cache key naming conventions

### Adapter (Task 1.1)
- [ ] NavigationClient class
- [ ] calculate_route() method
- [ ] get_active_graph() method
- [ ] rebuild_graph() method
- [ ] confirm_graph() method
- [ ] Error handling and retries
- [ ] Response transformation

### Service (Task 1.2)
- [ ] NavigationService class
- [ ] calculate_route() method
- [ ] Business rule validation
- [ ] Cache integration (check cache before adapter call)
- [ ] Cache invalidation logic
- [ ] Response transformation
- [ ] Error handling

### Handler (Task 1.3)
- [ ] Route calculation endpoint
- [ ] Nearest node endpoint
- [ ] Request validation
- [ ] Response formatting

### Tests (Tasks 1.5 & 1.6)
- [ ] Unit tests for service
- [ ] Unit tests for handler
- [ ] Unit tests for cache client
- [ ] Integration tests for workflow
- [ ] Mock fixtures (including Redis mock)
- [ ] Error scenario tests
- [ ] Cache hit/miss tests

### Documentation (Task 1.8)
- [ ] Route calculation endpoint docs
- [ ] Nearest node endpoint docs
- [ ] Request/response examples
- [ ] Error scenarios
- [ ] Integration guide
- [ ] Caching strategy documentation
- [ ] Cache TTL values documented

---

That's Phase 1! It's all about integrating the Navigation Service into the BFF so mobile clients can calculate routes. No positioning or chatbot in this phase - just navigation.

*Last Updated: March 2026*
