# Phase 1: Navigation Integration - Lambda Serverless Edition

## 🎯 Phase 1 Overview

**Goal:** Integrate the Navigation Service into the BFF Lambda function so mobile clients can calculate routes between points in buildings through a serverless gateway.

**Architecture:** BFF as orchestration gateway on AWS Lambda (stateless, serverless)

**Duration:** 2-3 weeks

**Deliverables:**
- Fully functional navigation endpoints on Lambda
- Redis caching integration
- Test coverage > 80%
- API documentation
- Lambda deployment guide

---

## 🏗️ BFF Role: Orchestration Gateway

The BFF is **NOT** a traditional backend service. It's a **serverless orchestration gateway** that:

✅ **Acts as a single entry point** for mobile clients
✅ **Routes requests** to appropriate backend services
✅ **Validates requests** before forwarding
✅ **Caches responses** to reduce backend load
✅ **Formats responses** for mobile clients
✅ **Handles errors** gracefully
✅ **Logs all requests** for monitoring

❌ **Does NOT** store data (external services handle persistence)
❌ **Does NOT** run complex business logic (services handle logic)
❌ **Does NOT** manage databases (services manage their own data)
❌ **Does NOT** maintain state (stateless Lambda functions)

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

**Lambda Considerations:**
- Use async HTTP client (httpx) for non-blocking I/O
- Set appropriate timeouts (Lambda has 30-second limit)
- Implement retry logic with exponential backoff
- Log all external service calls

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
- Integrate with Redis caching

**Key responsibilities:**
- Apply business logic
- Validate inputs
- Coordinate between handler and adapter
- Transform data
- Check cache before calling adapter
- Store results in cache

**Lambda Considerations:**
- Keep logic lightweight (Lambda has 15-minute timeout)
- Use async/await for all I/O operations
- Cache frequently accessed data
- Handle service failures gracefully

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

**Lambda Considerations:**
- Use FastAPI for HTTP handling
- Mangum adapter converts Lambda events to HTTP
- Return responses in Lambda-compatible format
- Handle cold starts efficiently

---

### Task 1.4: Add Navigation Schemas
**File:** `app/models/schemas.py`

**What it needs to do:**
- Create Pydantic request schemas:
  - `Coordinates` - latitude/longitude
  - `RouteOptions` - optional route preferences
- Create Pydantic response schemas:
  - `RouteResponse` - route with steps, distance, duration
  - `NavigationStepResponse` - individual step
  - `NodeResponse` - node details
  - `GraphVersionResponse` - graph version info

**Key responsibilities:**
- Define data structures
- Validate input/output
- Provide type hints

---

### Task 1.5: Implement Redis Caching
**File:** `app/adapters/cache_client.py`

**What it needs to do:**
- Create Redis cache client for caching frequently accessed data
- Implement cache methods:
  - `get_cached(key)` - Retrieve cached data
  - `set_cached(key, value, ttl)` - Store data with TTL
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
- Connect to Redis (ElastiCache in Lambda)
- Store and retrieve cached data
- Handle cache expiration
- Invalidate cache when needed

**Lambda Considerations:**
- Use aioredis for async Redis operations
- ElastiCache must be in same VPC as Lambda
- Configure security groups for communication
- Handle connection failures gracefully

---

### Task 1.6: Write Unit Tests
**File:** `tests/unit/test_navigation_service.py` and `tests/unit/test_handlers/test_navigation.py`

**What it needs to test:**
- NavigationService:
  - Route calculation with valid inputs
  - Route calculation with invalid inputs (different buildings, no graph, etc.)
  - Error handling
  - Response transformation
  - Cache integration
- NavigationHandler:
  - Route endpoint with valid request
  - Route endpoint with invalid request
  - Nearest node endpoint
  - Error responses

**Key responsibilities:**
- Mock NavigationAdapter
- Mock Redis cache
- Test business logic
- Test error handling
- Verify response format

---

### Task 1.7: Write Integration Tests
**File:** `tests/integration/test_workflows/test_navigation_workflow.py`

**What it needs to test:**
- Full request flow: Handler → Service → Adapter
- Mock navigation-service responses
- Verify end-to-end behavior
- Test error scenarios
- Test cache hit/miss behavior

**Key responsibilities:**
- Test complete workflows
- Mock external services
- Verify response formatting
- Test Lambda event handling

---

### Task 1.8: Create API Documentation
**File:** `docs/API.md`

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

## 🔄 Data Flow for Route Calculation (Lambda)

```
1. Mobile Client
   GET /bff/navigation/start/end?floor_id=123
   
2. API Gateway
   ├─ Validates request
   ├─ Applies rate limiting
   └─ Invokes Lambda function
   
3. Lambda Handler (navigation.py)
   ├─ Receives Lambda event
   ├─ Parses request parameters
   ├─ Validates coordinates and floor_id
   └─ Calls NavigationService
   
4. Service (navigation_service.py)
   ├─ Check Redis cache for active graph
   │  ├─ Cache HIT: Use cached graph (~10ms)
   │  └─ Cache MISS: Continue to step 5
   ├─ Validates business rules
   │  ├─ Check floor exists
   │  ├─ Check building has active graph
   │  └─ Check start/end in same building
   ├─ Calls NavigationAdapter
   ├─ Cache the result in Redis
   └─ Transforms response
   
5. Adapter (navigation_client.py)
   ├─ Makes HTTP call to navigation-service
   ├─ Handles errors and retries
   └─ Returns response
   
6. Navigation Service (External, Port 8010)
   ├─ Loads active graph version
   ├─ Calculates route using Dijkstra/A*
   ├─ Generates navigation steps
   └─ Returns route with steps
   
7. Response (reverse flow)
   ├─ Adapter returns response
   ├─ Service transforms response
   ├─ Handler formats response
   ├─ Mangum converts to Lambda response
   └─ API Gateway returns to mobile client
   
8. Mobile Client
   Receives route with steps, distance, duration
```

---

## 📊 What Each Component Does

### Handler (HTTP Layer)
- **Input:** HTTP request with coordinates and floor_id
- **Output:** Formatted JSON response
- **Responsibility:** Validate request, call service, format response
- **Lambda:** Receives Lambda event, returns Lambda response

### Service (Business Logic Layer)
- **Input:** Validated request data
- **Output:** Transformed response
- **Responsibility:** Apply business rules, coordinate adapters, manage cache
- **Lambda:** Lightweight logic, no state persistence

### Adapter (Integration Layer)
- **Input:** Request data from service
- **Output:** Response from navigation-service
- **Responsibility:** Make HTTP calls, handle errors, transform responses
- **Lambda:** Async HTTP calls, timeout handling

### Cache (Redis Layer)
- **Input:** Cache key and value
- **Output:** Cached data or cache miss
- **Responsibility:** Store/retrieve cached data, handle expiration
- **Lambda:** ElastiCache in same VPC, async operations

---

## 🔌 Integration Points

### With Navigation Service (External, Port 8010)
- **Endpoint:** `POST /api/navigation/route`
  - Input: `{start, end, floor_id, options}`
  - Output: `{distance, duration, steps}`
- **Endpoint:** `GET /api/graphs/{building_id}/active`
  - Output: Active graph version info
- **Endpoint:** `POST /api/graphs/rebuild/{building_id}`
  - Rebuild graph preview
- **Endpoint:** `POST /api/graphs/confirm/{building_id}`
  - Activate new graph version

### With Backend API (External, Port 8040)
- Verify building exists
- Verify floor exists and belongs to building

### With Redis Cache (ElastiCache)
- Cache active graph versions
- Cache building data
- Cache floor data

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
- [ ] Lambda deployment tested locally (SAM CLI)
- [ ] Lambda deployment to AWS verified

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

1. **BFF is a gateway** - Routes requests to services, doesn't store data
2. **Stateless design** - No in-memory state, Lambda-compatible
3. **Async/await** - All I/O operations are async
4. **Error handling** - Use custom AppError exceptions
5. **Structured logging** - Log all important events
6. **Standardized responses** - Always use success/error format
7. **Caching strategy** - Reduce external service calls
8. **Lambda constraints** - 30-second timeout, 512MB memory
9. **VPC configuration** - Lambda must access ElastiCache and services
10. **Security** - HTTPS, IAM roles, security groups

---

## 🔴 Redis Configuration for Lambda

### Environment Variables
```
REDIS_URL=redis://your-elasticache-endpoint:6379
REDIS_DB=0
CACHE_ENABLED=true
CACHE_TTL_GRAPH=3600          # 1 hour for graph versions
CACHE_TTL_BUILDING=86400      # 24 hours for building data
CACHE_TTL_FLOOR=86400         # 24 hours for floor data
```

### ElastiCache Setup
```
- Create Redis cluster in AWS ElastiCache
- Place in same VPC as Lambda
- Configure security group to allow Lambda access
- Note the endpoint (e.g., my-cache.abc123.ng.0001.use1.cache.amazonaws.com:6379)
- Set REDIS_URL environment variable in Lambda
```

### Cache Keys
```
graph:active:{building_id}     # Active graph version (1 hour)
building:{building_id}         # Building metadata (24 hours)
floor:{floor_id}               # Floor metadata (24 hours)
```

---

## 📚 Reference Files

- **BFF_LAMBDA_ARCHITECTURE.md** - Complete Lambda architecture guide
- **LAMBDA_DEPLOYMENT_GUIDE.md** - Step-by-step Lambda deployment
- **SERVERLESS_FRAMEWORK_SETUP.md** - Serverless Framework guide
- **ARCHITECTURE.md** - System architecture
- **PLAN.md** - Overall implementation roadmap

---

## 📋 Task Checklist

### Schemas (Task 1.4)
- [ ] Coordinates schema
- [ ] RouteOptions schema
- [ ] RouteResponse schema
- [ ] NavigationStepResponse schema
- [ ] NodeResponse schema
- [ ] GraphVersionResponse schema

### Cache Client (Task 1.5)
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

### Tests (Tasks 1.6 & 1.7)
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

## 🎯 Lambda Deployment Checklist

- [ ] Code written and tested locally
- [ ] All dependencies in requirements.txt
- [ ] Environment variables configured
- [ ] ElastiCache Redis cluster created
- [ ] Lambda function created
- [ ] API Gateway configured
- [ ] VPC and security groups configured
- [ ] IAM roles and permissions set
- [ ] CloudWatch logging configured
- [ ] Lambda tested with SAM CLI
- [ ] Lambda deployed to AWS
- [ ] API Gateway endpoints tested
- [ ] Cache working correctly
- [ ] Monitoring and alarms configured

---

*Last Updated: March 2026*
*Status: Ready for Implementation*
