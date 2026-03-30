from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from mangum import Mangum
from starlette import status
from starlette.responses import Response

from app.core.config import get_settings
from app.dependencies import shutdown_adapters
from app.handlers import buildings, floors, navigation, poi, position
from app.utils.errors import AppError
from app.utils.logging import configure_logging, log_event_async
from app.utils.responses import error_response

settings = get_settings()
logger = configure_logging(settings.log_level)


@asynccontextmanager
async def lifespan(_: FastAPI):
    yield
    await shutdown_adapters()


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

app.include_router(buildings.router, prefix="/bff")
app.include_router(floors.router, prefix="/bff")
app.include_router(poi.router, prefix="/bff")
app.include_router(navigation.router, prefix="/bff")
app.include_router(position.router, prefix="/bff")


@app.middleware("http")
async def request_logging_middleware(request: Request, call_next):
    response: Response | None = None
    try:
        response = await call_next(request)
        return response
    finally:
        await log_event_async(
            logger=logger,
            level="INFO",
            event="http_request",
            payload={
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code if response else 500,
            },
        )


@app.exception_handler(AppError)
async def app_error_handler(_: Request, exc: AppError):
    await log_event_async(
        logger=logger,
        level="ERROR",
        event="app_error",
        payload={"code": exc.code, "message": exc.message, "status_code": exc.status_code},
    )
    return error_response(code=exc.code, message=exc.message, status_code=exc.status_code)


@app.exception_handler(RequestValidationError)
async def validation_error_handler(_: Request, exc: RequestValidationError):
    return error_response(
        code="VALIDATION_ERROR",
        message=str(exc),
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
    )


@app.exception_handler(Exception)
async def unhandled_error_handler(_: Request, exc: Exception):
    await log_event_async(
        logger=logger,
        level="ERROR",
        event="unhandled_error",
        payload={"error": str(exc)},
    )
    return error_response(
        code="INTERNAL_ERROR",
        message="Unexpected error occurred",
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )


@app.get("/health")
async def health_check():
    return {"status": "ok", "service": settings.app_name, "environment": settings.environment}


handler = Mangum(app)
