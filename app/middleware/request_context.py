import time
import uuid
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.logging import get_logger

logger = get_logger(__name__)


class RequestContextMiddleware(BaseHTTPMiddleware):
    """
    Adds a request_id to every request and logs
    request + response lifecycle.
    """

    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())
        start_time = time.time()

        # Attach request_id to request state
        request.state.request_id = request_id

        logger.info(
            "Incoming request",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
            },
        )

        response = await call_next(request)

        duration_ms = round((time.time() - start_time) * 1000, 2)

        logger.info(
            "Outgoing response",
            extra={
                "request_id": request_id,
                "status_code": response.status_code,
                "duration_ms": duration_ms,
            },
        )

        # Expose request_id to client (useful for debugging)
        response.headers["X-Request-ID"] = request_id

        return response
