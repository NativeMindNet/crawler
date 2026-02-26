"""API middleware."""

import logging
import time
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """Logs request/response information."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and log."""
        start_time = time.time()

        # Log request
        logger.info(
            f"Request: {request.method} {request.url.path}",
            extra={
                "method": request.method,
                "path": request.url.path,
                "client": request.client.host if request.client else "unknown",
            },
        )

        # Process request
        response = await call_next(request)

        # Log response
        duration = time.time() - start_time
        logger.info(
            f"Response: {request.method} {request.url.path} - {response.status_code} ({duration:.3f}s)",
            extra={
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration": duration,
            },
        )

        return response


class ErrorMiddleware(BaseHTTPMiddleware):
    """Handles errors and returns consistent error responses."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and handle errors."""
        try:
            return await call_next(request)
        except Exception as e:
            logger.error(f"Unhandled error: {e}", exc_info=True)

            from fastapi.responses import JSONResponse
            return JSONResponse(
                status_code=500,
                content={
                    "error": "Internal server error",
                    "detail": str(e) if logging.getLogger().level == logging.DEBUG else None,
                },
            )
