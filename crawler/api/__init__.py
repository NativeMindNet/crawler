"""API module."""

from crawler.api.app import create_app
from crawler.api.schemas import (
    TaskCreate,
    TaskResponse,
    ScrapeRequest,
    ScrapeResponse,
    BulkIngestRequest,
    BulkStatusResponse,
    HealthResponse,
)
from crawler.api.middleware import LoggingMiddleware, ErrorMiddleware

__all__ = [
    "create_app",
    "TaskCreate",
    "TaskResponse",
    "ScrapeRequest",
    "ScrapeResponse",
    "BulkIngestRequest",
    "BulkStatusResponse",
    "HealthResponse",
    "LoggingMiddleware",
    "ErrorMiddleware",
]
