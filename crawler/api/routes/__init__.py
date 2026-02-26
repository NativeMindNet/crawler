"""API routes package."""

from crawler.api.routes.health import router as health_router
from crawler.api.routes.tasks import router as tasks_router
from crawler.api.routes.scrape import router as scrape_router
from crawler.api.routes.bulk import router as bulk_router
from crawler.api.routes.config import router as config_router
from crawler.api.routes.webhooks import router as webhooks_router

__all__ = [
    "health_router",
    "tasks_router",
    "scrape_router",
    "bulk_router",
    "config_router",
    "webhooks_router",
]
