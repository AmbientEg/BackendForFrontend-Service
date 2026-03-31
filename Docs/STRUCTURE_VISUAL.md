# BFF Service - Visual Structure Guide

## 📊 Complete Project Structure with Descriptions

```
BackendForFrontend-Service/
│
├── 📄 .env.example
│   └─ Template for environment variables (copy to .env and configure)
│
├── 📄 README.md
│   └─ Original quick start guide and architecture overview
│
├── 📄 requirements.txt
│   └─ Python dependencies (FastAPI, Mangum, httpx, etc.)
│
├── 📁 .git/
│   └─ Git version control directory
│
├── 📁 app/                                    ← MAIN APPLICATION
│   │
│   ├── 📄 __init__.py
│   │   └─ Package initialization
│   │
│   ├── 📄 main.py                            ← ENTRY POINT
│   │   ├─ FastAPI app initialization
│   │   ├─ Middleware setup (logging, exception handling)
│   │   ├─ Router registration
│   │   ├─ Exception handlers
│   │   ├─ Health check endpoint
│   │   └─ Lambda handler (Mangum)
│   │
│   ├── 📄 dependencies.py
│   │   ├─ Dependency injection setup
│   │   ├─ Adapter initialization
│   │   └─ Lifecycle management
│   │
│   ├── 📁 core/                              ← CONFIGURATION
│   │   ├── 📄 __init__.py
│   │   └── 📄 config.py
│   │       ├─ Environment-based settings
│   │       ├─ Service URLs
│   │       ├─ Database configuration
│   │       ├─ Feature flags
│   │       └─ Logging configuration
│   │
│   ├── 📁 models/                            ← DATA VALIDATION
│   │   ├── 📄 __init__.py
│   │   └── 📄 schemas.py
│   │       ├─ Pydantic request schemas
│   │       ├─ Pydantic response schemas
│   │       ├─ Building schemas
│   │       ├─ Floor schemas
│   │       ├─ Navigation schemas
│   │       ├─ POI schemas
│   │       └─ Position schemas
│   │
│   ├── 📁 handlers/                          ← HTTP ENDPOINTS
│   │   ├── 📄 __init__.py
│   │   ├── 📄 buildings.py
│   │   │   ├─ POST /bff/buildings
│   │   │   ├─ GET /bff/buildings/{id}
│   │   │   └─ GET /bff/buildings
│   │   ├── 📄 floors.py
│   │   │   ├─ POST /bff/floors
│   │   │   ├─ GET /bff/floors/{id}
│   │   │   └─ PUT /bff/floors/{id}
│   │   ├── 📄 navigation.py
│   │   │   ├─ GET /bff/navigation/{start}/{end}
│   │   │   └─ GET /bff/navigation/nearest-node
│   │   ├── 📄 poi.py
│   │   │   ├─ POST /bff/poi
│   │   │   ├─ GET /bff/poi/{floor_id}
│   │   │   └─ GET /bff/poi/{id}
│   │   └── 📄 position.py
│   │       ├─ GET /bff/position/{device_id}
│   │       └─ POST /bff/position
│   │
│   ├── 📁 services/                          ← BUSINESS LOGIC
│   │   ├── 📄 __init__.py
│   │   ├── 📄 building_service.py
│   │   │   ├─ Building creation logic
│   │   │   ├─ Building validation
│   │   │   └─ Building metadata management
│   │   ├── 📄 floor_service.py
│   │   │   ├─ Floor creation logic
│   │   │   ├─ GeoJSON processing
│   │   │   └─ Floor storage coordination
│   │   ├── 📄 navigation_service.py
│   │   │   ├─ Route calculation orchestration
│   │   │   ├─ Business rule validation
│   │   │   └─ Response transformation
│   │   ├── 📄 poi_service.py
│   │   │   ├─ POI CRUD operations
│   │   │   ├─ Floor association logic
│   │   │   └─ POI validation
│   │   └── 📄 position_service.py
│   │       ├─ Device positioning logic
│   │       ├─ Location tracking
│   │       └─ Position validation
│   │
│   ├── 📁 adapters/                          ← EXTERNAL INTEGRATION
│   │   ├── 📄 __init__.py
│   │   ├── 📄 backend_api_client.py
│   │   │   ├─ HTTP client for backend API
│   │   │   ├─ Building endpoints
│   │   │   ├─ Floor endpoints
│   │   │   ├─ POI endpoints
│   │   │   └─ Error handling
│   │   ├── 📄 navigation_client.py
│   │   │   ├─ HTTP client for navigation service
│   │   │   ├─ Route calculation endpoint
│   │   │   ├─ Graph management endpoints
│   │   │   └─ Error handling & retries
│   │   ├── 📄 positioning_client.py
│   │   │   ├─ HTTP client for positioning service
│   │   │   ├─ Device position endpoints
│   │   │   └─ Error handling
│   │   └── 📄 database_client.py
│   │       ├─ Database operations
│   │       ├─ GeoJSON storage
│   │       ├─ Metadata persistence
│   │       └─ Query operations
│   │
│   └── 📁 utils/                             ← SHARED UTILITIES
│       ├── 📄 __init__.py
│       ├── 📄 errors.py
│       │   ├─ AppError (custom exception)
│       │   ├─ ValidationError
│       │   ├─ NotFoundError
│       │   ├─ UnauthorizedError
│       │   ├─ ForbiddenError
│       │   ├─ ConflictError
│       │   └─ ServiceUnavailableError
│       ├── 📄 logging.py
│       │   ├─ Structured logging configuration
│       │   ├─ Log event helpers
│       │   └─ Correlation ID management
│       ├── 📄 responses.py
│       │   ├─ success_response() builder
│       │   ├─ error_response() builder
│       │   └─ Response formatting utilities
│       └── 📄 auth.py
│           ├─ Authentication helpers
│           ├─ Token validation
│           └─ Permission checking
│
├── 📁 tests/                                 ← TEST SUITE (TO ADD)
│   ├── 📄 conftest.py
│   │   ├─ Pytest configuration
│   │   ├─ Fixtures for mocking
│   │   ├─ Test data builders
│   │   └─ Database fixtures
│   ├── 📁 unit/
│   │   ├── 📁 test_handlers/
│   │   │   ├─ test_buildings.py
│   │   │   ├─ test_floors.py
│   │   │   ├─ test_navigation.py
│   │   │   ├─ test_poi.py
│   │   │   └─ test_position.py
│   │   ├── 📁 test_services/
│   │   │   ├─ test_building_service.py
│   │   │   ├─ test_floor_service.py
│   │   │   ├─ test_navigation_service.py
│   │   │   ├─ test_poi_service.py
│   │   │   └─ test_position_service.py
│   │   └── 📁 test_adapters/
│   │       ├─ test_backend_api_client.py
│   │       ├─ test_navigation_client.py
│   │       └─ test_positioning_client.py
│   └── 📁 integration/
│       └── 📁 test_workflows/
│           ├─ test_building_workflow.py
│           ├─ test_navigation_workflow.py
│           └─ test_position_workflow.py
│
├── 📁 docs/                                  ← DOCUMENTATION (TO ADD)
│   ├── 📄 API.md
│   │   ├─ Endpoint documentation
│   │   ├─ Request/response examples
│   │   └─ Error scenarios
│   ├── 📄 INTEGRATION.md
│   │   ├─ Service integration guide
│   │   ├─ Configuration examples
│   │   └─ Troubleshooting
│   └── 📄 ARCHITECTURE.md
│       ├─ Architecture decisions
│       ├─ Design patterns
│       └─ Best practices
│
├── 📁 scripts/                               ← UTILITY SCRIPTS (TO ADD)
│   ├── 📄 setup_db.py
│   │   └─ Database initialization
│   └── 📄 seed_data.py
│       └─ Test data generation
│
├── 📁 docker/                                ← DOCKER CONFIG (TO ADD)
│   ├── 📄 Dockerfile
│   │   └─ Container image definition
│   └── 📄 docker-compose.yml
│       └─ Local development stack
│
├── 📁 .github/                               ← CI/CD (TO ADD)
│   └── 📁 workflows/
│       ├── 📄 test.yml
│       │   └─ Automated testing
│       └── 📄 deploy.yml
│           └─ Automated deployment
│
├── 📄 pytest.ini                             ← PYTEST CONFIG (TO ADD)
│   └─ Pytest configuration
│
├── 📄 Dockerfile                             ← CONTAINER (TO ADD)
│   └─ Production container image
│
├── 📄 docker-compose.yml                     ← LOCAL DEV (TO ADD)
│   └─ Local development stack
│
├── 📄 PROJECT_STRUCTURE.md                   ← DOCUMENTATION (NEW)
│   └─ Complete directory tree with descriptions
│
├── 📄 PLAN.md                                ← DOCUMENTATION (NEW)
│   └─ Detailed implementation roadmap
│
├── 📄 STRUCTURE_ASSESSMENT.md                ← DOCUMENTATION (NEW)
│   └─ Architecture evaluation and recommendations
│
├── 📄 ARCHITECTURE.md                        ← DOCUMENTATION (NEW)
│   └─ System architecture and design patterns
│
├── 📄 SUMMARY.md                             ← DOCUMENTATION (NEW)
│   └─ Documentation summary and next steps
│
├── 📄 QUICK_REFERENCE.md                     ← DOCUMENTATION (NEW)
│   └─ One-page quick reference guide
│
├── 📄 README_DOCUMENTATION.md                ← DOCUMENTATION (NEW)
│   └─ Documentation index and reading guide
│
└── 📄 STRUCTURE_VISUAL.md                    ← DOCUMENTATION (NEW)
    └─ This file - visual structure guide
```

---

## 🎯 Layer Visualization

```
┌─────────────────────────────────────────────────────────────┐
│                    HTTP Requests                            │
│                  (Mobile Clients)                           │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────┐
│  HANDLERS LAYER (app/handlers/)                             │
│  ├─ buildings.py      ├─ floors.py        ├─ navigation.py │
│  ├─ poi.py            └─ position.py                        │
│  └─ Validates requests, calls services                      │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────┐
│  SERVICES LAYER (app/services/)                             │
│  ├─ building_service.py    ├─ floor_service.py             │
│  ├─ navigation_service.py   ├─ poi_service.py              │
│  ├─ position_service.py                                    │
│  └─ Applies business logic, calls adapters                 │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────┐
│  ADAPTERS LAYER (app/adapters/)                             │
│  ├─ backend_api_client.py   ├─ navigation_client.py        │
│  ├─ positioning_client.py    └─ database_client.py         │
│  └─ Integrates with external services                      │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────┐
│  EXTERNAL SERVICES & DATABASE                              │
│  ├─ Navigation Service      ├─ Positioning Service         │
│  ├─ Backend API             └─ PostgreSQL Database         │
└─────────────────────────────────────────────────────────────┘
```

---

## 📊 Data Flow Diagram

```
Mobile Client Request
        │
        ▼
┌──────────────────────┐
│  Handler             │
│  (validates input)   │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│  Service             │
│  (business logic)    │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│  Adapter             │
│  (external call)     │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│  External Service    │
│  (processes request) │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│  Response            │
│  (formatted)         │
└──────────┬───────────┘
           │
           ▼
Mobile Client Response
```

---

## 🔄 Request/Response Flow

```
REQUEST:
Mobile Client
    │
    ├─ POST /bff/navigation/route
    ├─ Headers: Content-Type: application/json
    └─ Body: {start, end, floor_id, options}
            │
            ▼
    Handler (navigation.py)
            │
            ├─ Validate schema (Pydantic)
            ├─ Call NavigationService
            │
            ▼
    Service (navigation_service.py)
            │
            ├─ Validate business rules
            ├─ Call NavigationAdapter
            │
            ▼
    Adapter (navigation_client.py)
            │
            ├─ Make HTTP call to navigation-service
            ├─ Handle errors
            │
            ▼
    Navigation Service (external)
            │
            ├─ Calculate route
            ├─ Generate steps
            │
            ▼
    Response (reverse flow)
            │
            ├─ Adapter returns response
            ├─ Service transforms response
            ├─ Handler formats response
            │
            ▼
Mobile Client
    │
    ├─ Status: 200 OK
    ├─ Headers: Content-Type: application/json
    └─ Body: {status, data: {distance, duration, steps}}
```

---

## 📁 File Organization by Concern

### By Domain
```
Buildings Domain:
├─ app/handlers/buildings.py
├─ app/services/building_service.py
├─ app/adapters/backend_api_client.py (shared)
└─ app/models/schemas.py (BuildingRequest, BuildingResponse)

Floors Domain:
├─ app/handlers/floors.py
├─ app/services/floor_service.py
├─ app/adapters/backend_api_client.py (shared)
├─ app/adapters/database_client.py (shared)
└─ app/models/schemas.py (FloorRequest, FloorResponse)

Navigation Domain:
├─ app/handlers/navigation.py
├─ app/services/navigation_service.py
├─ app/adapters/navigation_client.py
└─ app/models/schemas.py (RouteRequest, RouteResponse)

POI Domain:
├─ app/handlers/poi.py
├─ app/services/poi_service.py
├─ app/adapters/backend_api_client.py (shared)
└─ app/models/schemas.py (POIRequest, POIResponse)

Position Domain:
├─ app/handlers/position.py
├─ app/services/position_service.py
├─ app/adapters/positioning_client.py
└─ app/models/schemas.py (PositionRequest, PositionResponse)
```

### By Layer
```
Handlers Layer:
├─ app/handlers/buildings.py
├─ app/handlers/floors.py
├─ app/handlers/navigation.py
├─ app/handlers/poi.py
└─ app/handlers/position.py

Services Layer:
├─ app/services/building_service.py
├─ app/services/floor_service.py
├─ app/services/navigation_service.py
├─ app/services/poi_service.py
└─ app/services/position_service.py

Adapters Layer:
├─ app/adapters/backend_api_client.py
├─ app/adapters/navigation_client.py
├─ app/adapters/positioning_client.py
└─ app/adapters/database_client.py

Models Layer:
└─ app/models/schemas.py

Utils Layer:
├─ app/utils/errors.py
├─ app/utils/logging.py
├─ app/utils/responses.py
└─ app/utils/auth.py

Core Layer:
└─ app/core/config.py
```

---

## 🔌 Service Integration Map

```
BFF Service
    │
    ├─ Navigation Service (Port 8010)
    │   ├─ POST /api/navigation/route
    │   ├─ GET /api/graphs/{building_id}/active
    │   ├─ POST /api/graphs/rebuild/{building_id}
    │   └─ POST /api/graphs/confirm/{building_id}
    │
    ├─ Positioning Service (Port 8020)
    │   ├─ GET /api/position/{device_id}
    │   └─ POST /api/position
    │
    ├─ Backend API (Port 8030)
    │   ├─ POST /api/buildings
    │   ├─ GET /api/buildings/{id}
    │   ├─ POST /api/floors
    │   ├─ GET /api/floors/{id}
    │   ├─ POST /api/poi
    │   └─ GET /api/poi/{id}
    │
    └─ PostgreSQL Database
        ├─ buildings table
        ├─ floors table
        ├─ pois table
        └─ metadata tables
```

---

## 📊 Status Summary

### ✅ Implemented
- [x] Handler/Service/Adapter architecture
- [x] Modular domain organization
- [x] Standardized response format
- [x] Exception handling
- [x] Dependency injection
- [x] Configuration management
- [x] Logging infrastructure
- [x] Health check endpoint
- [x] Lambda readiness

### ⚠️ Needs Implementation
- [ ] Navigation service integration (adapters, services)
- [ ] Positioning service integration (adapters, services)
- [ ] Chatbot service integration (new handlers, services, adapters)
- [ ] Comprehensive test suite
- [ ] API documentation
- [ ] Docker configuration
- [ ] CI/CD pipelines

### 🔄 Recommended Additions
- [ ] tests/ directory with test suite
- [ ] docs/ directory with documentation
- [ ] scripts/ directory with utility scripts
- [ ] docker/ directory with Docker config
- [ ] .github/ directory with CI/CD workflows
- [ ] pytest.ini configuration
- [ ] Dockerfile for production
- [ ] docker-compose.yml for local development

---

## 🎯 Quick Navigation

### Find a File
- **HTTP Endpoints?** → `app/handlers/`
- **Business Logic?** → `app/services/`
- **External Integration?** → `app/adapters/`
- **Data Validation?** → `app/models/schemas.py`
- **Shared Utilities?** → `app/utils/`
- **Configuration?** → `app/core/config.py`
- **Tests?** → `tests/` (to be created)
- **Documentation?** → `docs/` (to be created)

### Find a Function
- **Route Calculation?** → `app/services/navigation_service.py`
- **Building Creation?** → `app/services/building_service.py`
- **Error Handling?** → `app/utils/errors.py`
- **Logging?** → `app/utils/logging.py`
- **Response Formatting?** → `app/utils/responses.py`

### Find an Endpoint
- **Buildings?** → `app/handlers/buildings.py`
- **Floors?** → `app/handlers/floors.py`
- **Navigation?** → `app/handlers/navigation.py`
- **POI?** → `app/handlers/poi.py`
- **Position?** → `app/handlers/position.py`

---

## 📈 Complexity by Layer

```
Handlers Layer:
├─ Complexity: LOW
├─ Responsibility: HTTP handling
└─ Lines of Code: 50-100 per file

Services Layer:
├─ Complexity: MEDIUM
├─ Responsibility: Business logic
└─ Lines of Code: 100-200 per file

Adapters Layer:
├─ Complexity: MEDIUM
├─ Responsibility: External integration
└─ Lines of Code: 100-200 per file

Models Layer:
├─ Complexity: LOW
├─ Responsibility: Data validation
└─ Lines of Code: 200-300 total

Utils Layer:
├─ Complexity: LOW
├─ Responsibility: Shared utilities
└─ Lines of Code: 50-100 per file

Core Layer:
├─ Complexity: LOW
├─ Responsibility: Configuration
└─ Lines of Code: 50-100 total
```

---

## 🚀 Getting Started Path

```
1. Read QUICK_REFERENCE.md (5 min)
   ↓
2. Read PROJECT_STRUCTURE.md (15 min)
   ↓
3. Read ARCHITECTURE.md (30 min)
   ↓
4. Review app/ directory structure
   ↓
5. Read PLAN.md Phase 1 (15 min)
   ↓
6. Start implementing Phase 1
```

---

*Last Updated: March 2026*
*Status: Ready for Implementation*
