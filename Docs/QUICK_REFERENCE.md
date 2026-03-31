# BFF Service - Quick Reference Guide

## 📋 One-Page Overview

### What is BFF?
Backend-for-Frontend Service is an orchestration layer that aggregates multiple backend services (Navigation, Positioning, Chatbot) into unified APIs for mobile clients.

### Current Status
✅ **Structure is EXCELLENT** - No major changes needed
⚠️ **Implementation needed** - Navigation, Positioning, Chatbot integration

---

## 🏗️ Architecture at a Glance

```
Mobile Client
    ↓
Handler (validates request)
    ↓
Service (applies business logic)
    ↓
Adapter (calls external service)
    ↓
External Service / Database
```

---

## 📁 Directory Structure

```
app/
├── handlers/          ← HTTP endpoints (one per domain)
├── services/          ← Business logic (one per domain)
├── adapters/          ← External integration (one per system)
├── models/            ← Data validation (Pydantic)
├── utils/             ← Shared utilities
└── core/              ← Configuration
```

---

## 🔌 Service Integration Points

| Service | Adapter | Purpose |
|---------|---------|---------|
| **Navigation** | `navigation_client.py` | Route calculation, graph management |
| **Positioning** | `positioning_client.py` | Device location tracking |
| **Chatbot** | `chatbot_client.py` | User assistance (future) |
| **Backend API** | `backend_api_client.py` | Building/floor/POI management |
| **Database** | `database_client.py` | GeoJSON and metadata storage |

---

## 🔄 Data Flow Example: Route Calculation

```
1. Mobile Client
   GET /bff/navigation/start/end?floor_id=123

2. Handler (navigation.py)
   ├─ Validates request
   └─ Calls NavigationService

3. Service (navigation_service.py)
   ├─ Validates business rules
   └─ Calls NavigationAdapter

4. Adapter (navigation_client.py)
   ├─ Makes HTTP call to navigation-service
   └─ Returns response

5. Response
   {
     "status": "success",
     "data": {
       "distance": 150.5,
       "duration": 120,
       "steps": [...]
     }
   }
```

---

## 📡 API Endpoints

### Buildings
```
POST   /bff/buildings              Create building
GET    /bff/buildings/{id}         Get building
GET    /bff/buildings              List buildings
```

### Floors
```
POST   /bff/floors                 Create floor with GeoJSON
GET    /bff/floors/{id}            Get floor
PUT    /bff/floors/{id}            Update floor
```

### Navigation
```
GET    /bff/navigation/{start}/{end}    Calculate route
GET    /bff/navigation/nearest-node     Find nearest node
```

### POI
```
POST   /bff/poi                    Create/update POI
GET    /bff/poi/{floor_id}         List POIs
GET    /bff/poi/{id}               Get POI
```

### Position
```
GET    /bff/position/{device_id}   Get device position
POST   /bff/position               Update device position
```

### Health
```
GET    /health                     Health check
```

---

## 📝 Response Format

### Success
```json
{
  "status": "success",
  "data": { /* response data */ }
}
```

### Error
```json
{
  "status": "error",
  "code": "ERROR_CODE",
  "message": "Human-readable message"
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

## 🚀 Quick Start

### Local Development
```bash
# Setup
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Configure
cp .env.example .env
# Edit .env with service URLs

# Run
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

### Docker
```bash
docker build -t bff-service .
docker run -p 8000:8000 --env-file .env bff-service
```

### AWS Lambda
```python
# In main.py
handler = Mangum(app)
```

---

## ⚙️ Configuration

### Key Environment Variables
```
NAVIGATION_SERVICE_URL=http://localhost:8010
POSITIONING_SERVICE_URL=http://localhost:8020
BACKEND_API_URL=http://localhost:8030
DATABASE_URL=postgresql://user:pass@localhost/bff_db
ENVIRONMENT=development
LOG_LEVEL=INFO
```

---

## 🧪 Testing

### Run Tests
```bash
pytest                          # Run all tests
pytest --cov=.                  # With coverage
pytest tests/unit/              # Unit tests only
pytest tests/integration/       # Integration tests only
```

### Test Structure
```
tests/
├── conftest.py                 # Fixtures
├── unit/                       # Unit tests
│   ├── test_handlers/
│   ├── test_services/
│   └── test_adapters/
└── integration/                # Integration tests
    └── test_workflows/
```

---

## 🔐 Security

### Authentication
- API token validation for admin endpoints
- JWT support for future user authentication

### Authorization
- Role-based access control (RBAC)
- Resource-level permissions

### Data Protection
- HTTPS for all communications
- Input validation (Pydantic)
- SQL injection prevention (SQLAlchemy ORM)

---

## 📊 Implementation Phases

### Phase 1: Navigation (2-3 weeks)
- [ ] Navigation service integration
- [ ] Comprehensive tests
- [ ] API documentation

### Phase 2: Positioning (1-2 weeks)
- [ ] Positioning service integration
- [ ] Real-time position tracking
- [ ] Tests

### Phase 3: Chatbot (2-3 weeks)
- [ ] Chatbot service integration
- [ ] Context-aware responses
- [ ] Tests

### Phase 4: Advanced (2-3 weeks)
- [ ] Caching layer (Redis)
- [ ] Error recovery (circuit breaker)
- [ ] Monitoring and tracing

---

## 📚 Documentation Files

| File | Purpose |
|------|---------|
| **PROJECT_STRUCTURE.md** | Complete directory tree with descriptions |
| **PLAN.md** | Detailed implementation roadmap |
| **STRUCTURE_ASSESSMENT.md** | Architecture evaluation and recommendations |
| **ARCHITECTURE.md** | System architecture and design patterns |
| **SUMMARY.md** | Documentation summary and next steps |
| **QUICK_REFERENCE.md** | This file - one-page overview |

---

## ✅ Checklist: Before You Start

- [ ] Read PROJECT_STRUCTURE.md
- [ ] Read PLAN.md
- [ ] Review ARCHITECTURE.md
- [ ] Setup local development environment
- [ ] Configure .env file
- [ ] Verify external services are accessible
- [ ] Run health check: `GET /health`

---

## 🎯 Key Principles

1. **Single Responsibility** - Each layer has one job
2. **Stateless** - No in-memory state persistence
3. **Async** - Non-blocking I/O throughout
4. **Testable** - Easy to mock and test
5. **Extensible** - Easy to add new features
6. **Maintainable** - Clear code organization
7. **Secure** - Input validation and error handling
8. **Observable** - Structured logging and tracing

---

## 🚨 Common Issues & Solutions

### Issue: Service unavailable
**Solution:** Check service URL in .env, verify service is running

### Issue: Database connection error
**Solution:** Check DATABASE_URL in .env, verify PostgreSQL is running

### Issue: Route calculation fails
**Solution:** Verify navigation-service is running, check floor_id is valid

### Issue: Tests fail
**Solution:** Run `pytest -v` for detailed output, check fixtures in conftest.py

---

## 📞 Support

### Documentation
- See PROJECT_STRUCTURE.md for directory organization
- See PLAN.md for implementation roadmap
- See ARCHITECTURE.md for system design

### Debugging
- Check logs: `LOG_LEVEL=DEBUG`
- Use Swagger UI: `http://localhost:8000/docs`
- Use Postman collection in `/postman`

---

## 🔗 External Services

### Navigation Service
- **URL:** `http://localhost:8010`
- **Purpose:** Route calculation, graph management
- **Endpoints:** `/api/navigation/route`, `/api/graphs/*`

### Positioning Service
- **URL:** `http://localhost:8020`
- **Purpose:** Device location tracking
- **Endpoints:** `/api/position/*`

### Backend API
- **URL:** `http://localhost:8030`
- **Purpose:** Building/floor/POI management
- **Endpoints:** `/api/buildings/*`, `/api/floors/*`, `/api/poi/*`

### Database
- **Type:** PostgreSQL + PostGIS
- **URL:** `postgresql://user:pass@localhost/bff_db`
- **Purpose:** Metadata and GeoJSON storage

---

## 📈 Performance Targets

- **Response Time:** < 500ms
- **Error Rate:** < 0.1%
- **Availability:** > 99.9%
- **Test Coverage:** > 80%

---

## 🎓 Learning Path

1. **Start Here:** QUICK_REFERENCE.md (this file)
2. **Understand Structure:** PROJECT_STRUCTURE.md
3. **Learn Architecture:** ARCHITECTURE.md
4. **Review Plan:** PLAN.md
5. **Deep Dive:** STRUCTURE_ASSESSMENT.md
6. **Start Coding:** Follow PLAN.md Phase 1

---

## 💡 Pro Tips

1. **Use Swagger UI** - Test endpoints at `http://localhost:8000/docs`
2. **Use Postman** - Import collection from `/postman` directory
3. **Enable Debug Logging** - Set `LOG_LEVEL=DEBUG` in .env
4. **Mock External Services** - Set `MOCK_EXTERNALS=true` for testing
5. **Use Type Hints** - All functions should have type hints
6. **Write Tests First** - Follow TDD approach
7. **Document APIs** - Add docstrings to all endpoints
8. **Monitor Logs** - Use structured logging for debugging

---

## 🔄 Typical Development Workflow

```
1. Read requirements in PLAN.md
2. Review architecture in ARCHITECTURE.md
3. Create handler in app/handlers/
4. Create service in app/services/
5. Create adapter in app/adapters/
6. Add schemas to app/models/schemas.py
7. Write unit tests in tests/unit/
8. Write integration tests in tests/integration/
9. Test with Swagger UI or Postman
10. Document in docs/
```

---

## 📞 Questions?

Refer to the appropriate documentation:
- **"How is the code organized?"** → PROJECT_STRUCTURE.md
- **"What should I build next?"** → PLAN.md
- **"How does the system work?"** → ARCHITECTURE.md
- **"Is the structure good?"** → STRUCTURE_ASSESSMENT.md
- **"What's the summary?"** → SUMMARY.md

---

*Last Updated: March 2026*
*Status: Ready for Implementation*
