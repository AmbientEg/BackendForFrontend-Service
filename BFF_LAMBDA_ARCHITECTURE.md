# BFF as Lambda Serverless Orchestration Gateway

## 🎯 Architecture Overview

The BackendForFrontend-Service is a **serverless orchestration gateway** deployed on AWS Lambda that acts as a single entry point for mobile clients to access multiple backend services.

---

## 📊 System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Mobile Clients                           │
│              (iOS, Android, Web Apps)                       │
└────────────────────────┬────────────────────────────────────┘
                         │
                    HTTPS Requests
                         │
┌────────────────────────▼────────────────────────────────────┐
│              AWS API Gateway                                │
│         (HTTP routing, rate limiting, CORS)                │
└────────────────────────┬────────────────────────────────────┘
                         │
                    Lambda Invocation
                         │
┌────────────────────────▼────────────────────────────────────┐
│         AWS Lambda Function (BFF Service)                   │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │           Orchestration Layer                        │  │
│  │  ┌────────────────────────────────────────────────┐  │  │
│  │  │ • Request validation                           │  │  │
│  │  │ • Request routing                              │  │  │
│  │  │ • Response formatting                          │  │  │
│  │  │ • Error handling                               │  │  │
│  │  │ • Logging and monitoring                       │  │  │
│  │  └────────────────────────────────────────────────┘  │  │
│  │                                                       │  │
│  │  ┌────────────────────────────────────────────────┐  │  │
│  │  │ Service Adapters (HTTP Clients)                │  │  │
│  │  │ • Navigation Service Client                    │  │  │
│  │  │ • Positioning Service Client                  │  │  │
│  │  │ • Chatbot Service Client                      │  │  │
│  │  │ • Backend API Client                          │  │  │
│  │  └────────────────────────────────────────────────┘  │  │
│  │                                                       │  │
│  │  ┌────────────────────────────────────────────────┐  │  │
│  │  │ Caching Layer (Redis)                          │  │  │
│  │  │ • Cache frequently accessed data               │  │  │
│  │  │ • Reduce external service calls                │  │  │
│  │  │ • Improve response times                       │  │  │
│  │  └────────────────────────────────────────────────┘  │  │
│  └──────────────────────────────────────────────────────┘  │
└────────────────────────┬────────────────────────────────────┘
                         │
        ┌────────────────┼────────────────┬──────────────┐
        │                │                │              │
        ▼                ▼                ▼              ▼
   ┌─────────┐    ┌─────────────┐  ┌──────────┐  ┌──────────┐
   │Navigation│    │ Positioning │  │ Chatbot  │  │ Backend  │
   │ Service  │    │  Service    │  │ Service  │  │   API    │
   │(Port8010)│    │(Port 8020)  │  │(Port8030)│  │(Port8040)│
   └────┬────┘    └──────┬──────┘  └────┬─────┘  └────┬─────┘
        │                │              │             │
        └────────────────┼──────────────┴─────────────┘
                         │
        ┌────────────────┼────────────────┐
        │                │                │
        ▼                ▼                ▼
   ┌─────────┐    ┌──────────┐    ┌────────────┐
   │   RDS   │    │ElastiCache│   │ CloudWatch │
   │(Database)    │  (Redis)  │    │  (Logging) │
   └─────────┘    └──────────┘    └────────────┘
```

---

## 🏗️ BFF Role: Orchestration Gateway

### What BFF Does:
1. **Single Entry Point** - Mobile clients call one API instead of multiple services
2. **Request Routing** - Routes requests to appropriate backend services
3. **Response Aggregation** - Combines responses from multiple services if needed
4. **Error Handling** - Handles errors from backend services gracefully
5. **Caching** - Reduces load on backend services with Redis caching
6. **Validation** - Validates requests before forwarding to services
7. **Logging** - Centralized logging for all requests
8. **Rate Limiting** - Protects backend services from overload

### What BFF Does NOT Do:
- ❌ Store data (external services handle persistence)
- ❌ Process complex business logic (services handle logic)
- ❌ Manage databases (services manage their own data)
- ❌ Run long-running tasks (Lambda has 15-minute timeout)

---

## 🔌 Service Integration Points

### Navigation Service (Port 8010)
**Purpose:** Route calculation and graph management
**Endpoints:**
- `POST /api/navigation/route` - Calculate route between points
- `GET /api/graphs/{building_id}/active` - Get active graph version
- `POST /api/graphs/rebuild/{building_id}` - Build graph preview
- `POST /api/graphs/confirm/{building_id}` - Activate new graph version

**BFF Role:** 
- Validates request (coordinates, floor_id)
- Calls navigation service
- Caches active graph versions
- Formats response for mobile client

### Positioning Service (Port 8020)
**Purpose:** Device location tracking
**Endpoints:**
- `GET /api/position/{device_id}` - Get device position
- `POST /api/position` - Update device position

**BFF Role:**
- Validates device_id
- Calls positioning service
- Caches position data
- Formats response for mobile client

### Chatbot Service (Port 8030)
**Purpose:** User assistance and chat
**Endpoints:**
- `POST /api/chat/message` - Send chat message
- `GET /api/chat/history/{user_id}` - Get chat history

**BFF Role:**
- Validates user_id and message
- Calls chatbot service
- Formats response for mobile client

### Backend API (Port 8040)
**Purpose:** Building, floor, and POI management
**Endpoints:**
- `POST /api/buildings` - Create building
- `GET /api/buildings/{id}` - Get building
- `POST /api/floors` - Create floor
- `GET /api/floors/{id}` - Get floor
- `POST /api/poi` - Create POI
- `GET /api/poi/{id}` - Get POI

**BFF Role:**
- Validates requests
- Calls backend API
- Caches building/floor/POI data
- Formats response for mobile client

---

## 📡 API Endpoints (BFF Gateway)

### Navigation Endpoints
```
GET /bff/navigation/{start}/{end}?floor_id=123
  ├─ Validates coordinates and floor_id
  ├─ Checks cache for active graph
  ├─ Calls navigation service
  ├─ Caches result
  └─ Returns route with steps

GET /bff/navigation/nearest-node?lat=40.7128&lon=-74.0060&floor_id=123
  ├─ Validates coordinates and floor_id
  ├─ Calls navigation service
  └─ Returns nearest node
```

### Building Endpoints
```
POST /bff/buildings
  ├─ Validates request
  ├─ Calls backend API
  └─ Returns created building

GET /bff/buildings/{building_id}
  ├─ Checks cache
  ├─ Calls backend API if not cached
  ├─ Caches result
  └─ Returns building details
```

### Floor Endpoints
```
POST /bff/floors
  ├─ Validates request
  ├─ Calls backend API
  └─ Returns created floor

GET /bff/floors/{floor_id}
  ├─ Checks cache
  ├─ Calls backend API if not cached
  ├─ Caches result
  └─ Returns floor details
```

### Position Endpoints
```
GET /bff/position/{device_id}
  ├─ Validates device_id
  ├─ Calls positioning service
  └─ Returns device position

POST /bff/position
  ├─ Validates request
  ├─ Calls positioning service
  └─ Returns updated position
```

### Chat Endpoints
```
POST /bff/chat/message
  ├─ Validates user_id and message
  ├─ Calls chatbot service
  └─ Returns chat response

GET /bff/chat/history/{user_id}
  ├─ Validates user_id
  ├─ Calls chatbot service
  └─ Returns chat history
```

---

## 🚀 AWS Lambda Deployment Architecture

### Lambda Function Configuration
```
Function Name: bff-service
Runtime: Python 3.11
Memory: 512 MB (adjustable)
Timeout: 30 seconds
Handler: app.main.handler
Environment Variables:
  - NAVIGATION_SERVICE_URL
  - POSITIONING_SERVICE_URL
  - CHATBOT_SERVICE_URL
  - BACKEND_API_URL
  - REDIS_URL
  - LOG_LEVEL
```

### API Gateway Configuration
```
API Name: bff-api
Stage: prod
Base Path: /bff
Methods: GET, POST, PUT, DELETE
CORS: Enabled
Rate Limiting: 10,000 requests/second
```

### VPC Configuration
```
Security Groups:
  - Allow outbound to services (ports 8010, 8020, 8030, 8040)
  - Allow outbound to ElastiCache (port 6379)
  - Allow outbound to RDS (port 5432)

Subnets:
  - Private subnets for Lambda
  - Same VPC as ElastiCache and RDS
```

### AWS Services Used
```
Lambda:
  - Compute (serverless)
  - Auto-scaling
  - Pay per invocation

API Gateway:
  - HTTP routing
  - Rate limiting
  - CORS handling
  - Request/response transformation

ElastiCache:
  - Redis cluster
  - Caching layer
  - Managed service

RDS:
  - PostgreSQL database
  - Managed service
  - Backups and replication

CloudWatch:
  - Logging
  - Monitoring
  - Alarms
  - Metrics

IAM:
  - Access control
  - Role-based permissions
  - Service-to-service authentication
```

---

## 🔄 Request Flow Example: Route Calculation

```
1. Mobile Client
   GET /bff/navigation/start/end?floor_id=123
   
2. API Gateway
   ├─ Validates request
   ├─ Applies rate limiting
   └─ Invokes Lambda function
   
3. Lambda Function (BFF)
   ├─ Handler receives event
   ├─ Parses request parameters
   ├─ Validates coordinates and floor_id
   ├─ Checks Redis cache for active graph
   │  ├─ Cache HIT: Use cached graph (~10ms)
   │  └─ Cache MISS: Continue to step 4
   ├─ Calls NavigationService adapter
   │  └─ Makes HTTP call to navigation-service
   ├─ Receives route response
   ├─ Caches result in Redis (1 hour TTL)
   ├─ Formats response
   └─ Returns to API Gateway
   
4. Navigation Service (External)
   ├─ Loads active graph version
   ├─ Calculates route using Dijkstra/A*
   ├─ Generates navigation steps
   └─ Returns route with steps
   
5. API Gateway
   ├─ Receives response from Lambda
   ├─ Applies response transformation
   └─ Returns to mobile client
   
6. Mobile Client
   Receives route with steps, distance, duration
```

---

## 💾 Data Flow: No Local Storage

```
BFF Lambda Function:
├─ NO local database (stateless)
├─ NO local file storage
├─ NO in-memory state persistence
├─ NO session storage
└─ Uses external services for all data

External Services (Persistent):
├─ Navigation Service
│  ├─ Stores floor GeoJSON
│  ├─ Stores navigation graphs
│  └─ Manages graph versions
├─ Positioning Service
│  ├─ Stores device positions
│  └─ Manages location history
├─ Chatbot Service
│  ├─ Stores chat messages
│  └─ Manages conversation history
└─ Backend API
   ├─ Stores buildings
   ├─ Stores floors
   ├─ Stores POIs
   └─ Manages metadata

Caching Layer (Redis):
├─ Caches active graph versions (1 hour)
├─ Caches building data (24 hours)
├─ Caches floor data (24 hours)
└─ Reduces external service calls
```

---

## 🔐 Security Architecture

### API Gateway Security
```
- HTTPS only (TLS 1.2+)
- API key validation
- Rate limiting
- CORS configuration
- Request validation
```

### Lambda Security
```
- IAM role-based access
- Environment variable encryption
- VPC isolation
- Security group restrictions
- CloudWatch logging
```

### Service-to-Service Communication
```
- HTTPS for all external calls
- Timeout configuration (30 seconds)
- Retry logic with exponential backoff
- Error handling and logging
```

### Data Protection
```
- ElastiCache encryption at rest
- RDS encryption at rest
- HTTPS in transit
- No sensitive data in logs
```

---

## 📊 Caching Strategy

### What Gets Cached
```
1. Active Graph Versions
   - Key: graph:active:{building_id}
   - TTL: 1 hour
   - Purpose: Avoid repeated calls to navigation service
   - Performance: ~500ms → ~10ms

2. Building Data
   - Key: building:{building_id}
   - TTL: 24 hours
   - Purpose: Cache building metadata
   - Performance: ~200ms → ~10ms

3. Floor Data
   - Key: floor:{floor_id}
   - TTL: 24 hours
   - Purpose: Cache floor metadata
   - Performance: ~200ms → ~10ms
```

### Cache Invalidation
```
When to invalidate:
- Graph cache: When graph is rebuilt/confirmed/rolled back
- Building cache: When building is created/updated
- Floor cache: When floor is created/updated

Implementation:
- Delete cache key when data is updated
- Use TTL for automatic expiration
- Log cache invalidation events
```

---

## ⚡ Performance Characteristics

### Response Times
```
Without Caching:
- Route calculation: ~500ms
- Building lookup: ~200ms
- Floor lookup: ~200ms

With Caching (80% hit rate):
- Route calculation: ~110ms (4.5x faster)
- Building lookup: ~50ms (4x faster)
- Floor lookup: ~50ms (4x faster)

Lambda Cold Start:
- First invocation: ~1-2 seconds
- Subsequent invocations: ~10-50ms
```

### Scalability
```
Lambda Auto-scaling:
- Automatically scales with demand
- Handles thousands of concurrent requests
- No manual scaling needed

API Gateway Rate Limiting:
- 10,000 requests/second per account
- Configurable per API
- Protects backend services
```

---

## 🔧 Deployment Process

### Prerequisites
```
- AWS account with appropriate permissions
- Python 3.11 runtime
- External services running (navigation, positioning, chatbot, backend)
- ElastiCache Redis cluster
- RDS PostgreSQL database
```

### Deployment Steps
```
1. Package code as ZIP or container image
2. Create Lambda function with handler: app.main.handler
3. Configure environment variables
4. Set up API Gateway with /bff/* routes
5. Configure VPC and security groups
6. Set up CloudWatch logging
7. Configure IAM roles and permissions
8. Test endpoints
9. Monitor with CloudWatch
```

### Deployment Tools
```
Option 1: Serverless Framework
- serverless deploy

Option 2: AWS SAM
- sam deploy

Option 3: AWS CLI
- aws lambda create-function
- aws apigateway create-rest-api

Option 4: AWS Console
- Manual configuration
```

---

## 📈 Monitoring and Logging

### CloudWatch Metrics
```
- Lambda invocations
- Lambda duration
- Lambda errors
- Lambda throttles
- API Gateway requests
- API Gateway latency
- API Gateway errors
```

### CloudWatch Logs
```
- Request logging (method, path, status)
- Error logging (code, message, stack trace)
- Service call logging (URL, duration, status)
- Cache hit/miss logging
- Performance metrics
```

### Alarms
```
- High error rate (> 1%)
- High latency (> 1 second)
- Lambda throttles
- Service unavailability
- Cache failures
```

---

## 💰 Cost Optimization

### Lambda Costs
```
- Pay per invocation (first 1M free)
- Pay for compute time (GB-seconds)
- Optimize memory allocation
- Reduce cold starts with provisioned concurrency
```

### API Gateway Costs
```
- Pay per API call
- Data transfer costs
- Caching reduces backend calls
```

### ElastiCache Costs
```
- Pay for node type and size
- Caching reduces database queries
- Reduces backend service load
```

### Cost Reduction Strategies
```
1. Use caching to reduce external service calls
2. Optimize Lambda memory allocation
3. Use provisioned concurrency for predictable load
4. Monitor and alert on cost anomalies
5. Use reserved capacity for predictable workloads
```

---

## 🚨 Error Handling

### Error Types
```
1. Validation Errors (400)
   - Invalid coordinates
   - Missing required fields
   - Invalid floor_id

2. Not Found Errors (404)
   - Building not found
   - Floor not found
   - Service not found

3. Service Errors (500)
   - Navigation service unavailable
   - Positioning service unavailable
   - Backend API unavailable

4. Timeout Errors (504)
   - Service response timeout
   - Lambda timeout
```

### Error Response Format
```json
{
  "status": "error",
  "code": "SERVICE_UNAVAILABLE",
  "message": "Navigation service is temporarily unavailable"
}
```

### Error Handling Strategy
```
1. Validate input before calling services
2. Handle service timeouts gracefully
3. Return meaningful error messages
4. Log all errors with context
5. Implement retry logic with exponential backoff
6. Fall back to cached data if available
7. Alert on critical errors
```

---

## 📋 Phase 1 Implementation Scope

### What's Included
```
✅ Navigation service integration
✅ Route calculation endpoint
✅ Nearest node endpoint
✅ Redis caching
✅ Error handling
✅ Logging
✅ Request validation
✅ Response formatting
```

### What's NOT Included (Future Phases)
```
❌ Positioning service integration (Phase 2)
❌ Chatbot service integration (Phase 3)
❌ Advanced features (Phase 4)
```

---

## 🎯 Key Principles

1. **Stateless** - No in-memory state persistence
2. **Serverless** - AWS Lambda handles infrastructure
3. **Orchestration** - Routes requests to services
4. **Caching** - Reduces external service calls
5. **Error Handling** - Graceful degradation
6. **Logging** - Centralized monitoring
7. **Security** - HTTPS, IAM, VPC isolation
8. **Scalability** - Auto-scaling with demand

---

## 📚 Related Documentation

- **PHASE1.md** - Phase 1 implementation tasks
- **LAMBDA_DEPLOYMENT_GUIDE.md** - Complete Lambda setup
- **SERVERLESS_FRAMEWORK_SETUP.md** - Serverless Framework guide
- **ARCHITECTURE.md** - System architecture
- **QUICK_REFERENCE.md** - Quick lookup guide

---

*Last Updated: March 2026*
*Status: Ready for Implementation*
