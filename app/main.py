import os
import sys
import logging
from contextlib import asynccontextmanager
from datetime import datetime

import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.trustedhost import TrustedHostMiddleware

from app.cache.redis_client import RedisClient
from app.clients.navigation_client import NavigationClient
from app.api import navigation as nav_router


IS_PRODUCTION = os.getenv("ENV", "development").lower() == "production"

# ----------------------------------------------------
# Production Logging Configuration
# ----------------------------------------------------
def setup_logging():
    """Configure production-ready logging with proper formatting and levels."""
    # Determine log level based on environment
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()

    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, log_level, logging.INFO),
        format="%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )

    # Set specific logger levels for third-party libraries
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)

    return logging.getLogger(__name__)


logger = setup_logging()

# Global Redis client instance
redis_client: RedisClient = None
navigation_client: NavigationClient = None

# ----------------------------------------------------
# Lifespan for Startup & Shutdown
# ----------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize redis and AI services on startup, cleanup on shutdown"""
    try:
        global redis_client, navigation_client
        
        # Initialize Redis client
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        redis_client = RedisClient(redis_url)
        logger.info(f"Redis client initialized: {redis_url}")

        # Initialize Navigation client
        navigation_base_url = os.getenv("NAVIGATION_SERVICE_URL", "http://navigation-service:8000")
        navigation_client = NavigationClient(base_url=navigation_base_url)
        logger.info(f"Navigation client initialized: {navigation_base_url}")
        
        logger.info("Application startup completed")
        yield

    except Exception as e:
        logger.error(f"Startup failed: {e}")
        raise

    finally:
        # Shutdown tasks
        try:
            if navigation_client:
                await navigation_client.close()
            if redis_client:
                await redis_client.close()
            logger.info("Connections closed")
        except Exception as e:
            logger.error(f"Shutdown error: {e}")
        logger.info("Application shutdown completed")


app = FastAPI(
    title="Backend For Frontend (BFF) API",
    description="Backend For Frontend, this is an API designed to serve as a backend layer for frontend applications, providing optimized endpoints and handling business logic.",
    version="1.0.0",
    docs_url="/docs" if not IS_PRODUCTION else None,
    redoc_url="/redoc" if not IS_PRODUCTION else None,
    openapi_url="/openapi.json" if not IS_PRODUCTION else None,
    lifespan=lifespan,
    generate_unique_id_function=lambda route: f"{route.tags[0]}-{route.name}" if route.tags else route.name,
    swagger_ui_parameters={
        "defaultModelsExpandDepth": -1,
        "tryItOutEnabled": True,
        "persistAuthorization": True,
    }
)

# ----------------------------------------------------
# Importing Routes
# ----------------------------------------------------
# TODO(phase-2): include routers from api/ layer once endpoints are implemented.
# Example:
# from app.api.routes import router as api_router
# app.include_router(api_router, prefix="/api")

# Mount navigation router
app.include_router(nav_router.router, prefix="/api")


# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all incoming requests for monitoring."""
    start_time = datetime.utcnow()

    # Generate correlation ID for request tracing
    correlation_id = request.headers.get("X-Correlation-ID", f"req_{start_time.timestamp()}")
    request.state.correlation_id = correlation_id

    logger.info(
        f"Incoming request - Method: {request.method}, "
        f"URL: {request.url}, "
        f"Client IP: {request.client.host if request.client else 'unknown'}, "
        f"Correlation ID: {correlation_id}"
    )

    response = await call_next(request)
    process_time = (datetime.utcnow() - start_time).total_seconds()

    logger.info(
        f"Request completed - Status: {response.status_code}, "
        f"Duration: {process_time:.3f}s, "
        f"Correlation ID: {correlation_id}"
    )

    return response


# Trusted Host Middleware (for production)
if IS_PRODUCTION:
    allowed_hosts = os.getenv("ALLOWED_HOSTS", "*").split(",")
    if allowed_hosts != ["*"]:
        app.add_middleware(TrustedHostMiddleware, allowed_hosts=allowed_hosts)

# CORS Configuration
cors_origins = os.getenv("CORS_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=[
        "Accept",
        "Accept-Language",
        "Content-Language",
        "Content-Type",
        "Authorization",
        "X-Correlation-ID",
        "X-Requested-With",
    ],
    expose_headers=["X-Correlation-ID"],
)


# ----------------------------------------------------
# Production Exception Handlers
# ----------------------------------------------------
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions with proper logging and response format."""
    correlation_id = getattr(request.state, 'correlation_id', 'unknown')

    logger.warning(
        f"HTTP Exception - Status: {exc.status_code}, "
        f"Detail: {exc.detail}, "
        f"Path: {request.url.path}, "
        f"Correlation ID: {correlation_id}"
    )

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
            "error": exc.detail,
            "status_code": exc.status_code,
            "timestamp": datetime.utcnow().isoformat(),
            "path": request.url.path,
            "correlation_id": correlation_id,
            "type": "http_error"
        }
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle all unhandled exceptions with proper logging."""
    correlation_id = getattr(request.state, 'correlation_id', 'unknown')

    logger.error(
        f"Unhandled exception - Type: {type(exc).__name__}, "
        f"Message: {str(exc)}, "
        f"Path: {request.url.path}, "
        f"Correlation ID: {correlation_id}",
        exc_info=True
    )

    # Don't expose internal error details in production
    error_detail = "Internal server error" if IS_PRODUCTION else str(exc)

    return JSONResponse(
        status_code=500,
        content={
            "detail": error_detail,
            "error": error_detail,
            "status_code": 500,
            "timestamp": datetime.utcnow().isoformat(),
            "path": request.url.path,
            "correlation_id": correlation_id,
            "type": "internal_error"
        }
    )


@app.get("/")
async def root():
    docs_url = "/docs" if not IS_PRODUCTION else None
    return {
        "message": "Backend for FrontEnd API is running",
        "version": "1.0.0",
        "documentation": docs_url,
        "health": "/health",
        "endpoints": {
            # TODO(phase-2): publish real endpoint map after api routers are mounted.
        }
    }


# ----------------------------------------------------
# Production Health and Monitoring Endpoints
# ----------------------------------------------------
@app.get("/health")
async def health_check():
    """Phase-1 health check: API process/liveness only."""
    try:
        # Service has no database in current phase.
        overall_status = "healthy"

        return {
            "status": overall_status,
            "timestamp": datetime.utcnow().isoformat(),
            "version": "1.0.0",
            "environment": os.getenv("ENVIRONMENT", "unknown"),
            "checks": {
                # TODO(phase-2): add redis connectivity and downstream readiness checks.
                "api": "healthy"
            },
            "production": IS_PRODUCTION
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}", exc_info=True)
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "timestamp": datetime.utcnow().isoformat(),
                "error": "Health check failed"
            }
        )


@app.get("/api/status")
async def get_api_status():
    return {
        "api_status": "operational",
        "timestamp": datetime.utcnow().isoformat(),
        # TODO(phase-2): expose orchestrator/cache metrics and circuit breaker states.
    }

# ----------------------------------------------------
# Run Server
# ----------------------------------------------------
if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=os.getenv("PORT", 8003),
        reload=True,
        log_level="info"

    )
