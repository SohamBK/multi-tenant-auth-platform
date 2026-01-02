from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from app.middleware.cors import setup_cors
from app.core.exceptions import AppException
from app.api.v1.api import api_router
from app.core.config import settings
from app.core.openapi import custom_openapi
from app.infrastructure.db.session import engine
from app.infrastructure.clients.redis_client import redis_client
from app.core.responses import ErrorResponse, ErrorDetail
from app.middleware.request_context import RequestContextMiddleware
from app.core.logging import setup_logging, get_logger

setup_logging()
logger = get_logger(__name__)

app = FastAPI(
    docs_url="/docs" if settings.ENABLE_DOCS else None,          # Swagger UI
    redoc_url="/redoc" if settings.ENABLE_DOCS else None,        # ReDoc UI
    openapi_url="/openapi.json",
)

# ---- Middleware ----
app.add_middleware(RequestContextMiddleware)
setup_cors(app)

app.openapi = lambda: custom_openapi(app)

@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    """
    Handles all known, expected application errors.
    """
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error=ErrorDetail(
                code=exc.error_code,
                message=exc.message,
            )
        ).model_dump(),
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    """
    Handles unexpected errors safely (no stacktrace leakage).
    """
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error=ErrorDetail(
                code="INTERNAL_SERVER_ERROR",
                message="An unexpected error occurred",
            )
        ).model_dump(),
    )


@app.on_event("shutdown")
async def shutdown_event():
    await engine.dispose()
    await redis_client.close()

app.include_router(api_router, prefix="/api/v1")
