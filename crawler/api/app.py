"""FastAPI application."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
import logging

from crawler.api.routes import health, tasks, scrape, bulk, config, webhooks
from crawler.api.middleware import LoggingMiddleware, ErrorMiddleware
from crawler.lpm import LocalPersistenceManager
from crawler.config_loader import ConfigLoader

logger = logging.getLogger(__name__)


def create_app(
    db_path: str = "/data/state/crawler.db",
    data_dir: str = "/data",
    config_dir: str = "/config",
    platform: Optional[str] = None,
) -> FastAPI:
    """
    Create FastAPI application.
    
    Args:
        db_path: SQLite database path
        data_dir: Data directory
        config_dir: Configuration directory
        platform: Platform name (optional)
    
    Returns:
        FastAPI application
    """
    app = FastAPI(
        title="Universal Single-Platform Crawler",
        description="API for crawling and parsing platform data",
        version="1.0.0",
    )

    # Add middleware
    app.add_middleware(ErrorMiddleware)
    app.add_middleware(LoggingMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Initialize shared resources
    app.state.lpm = LocalPersistenceManager(db_path, data_dir)
    app.state.config_loader = ConfigLoader(config_dir)
    app.state.platform = platform
    app.state.config_dir = config_dir

    @app.on_event("startup")
    async def startup():
        """Initialize on startup."""
        await app.state.lpm.initialize()
        logger.info("Crawler API started")

    @app.on_event("shutdown")
    async def shutdown():
        """Cleanup on shutdown."""
        await app.state.lpm.close()
        logger.info("Crawler API stopped")

    # Register routes
    app.include_router(health.router, prefix="/health", tags=["Health"])
    app.include_router(tasks.router, prefix="/tasks", tags=["Tasks"])
    app.include_router(scrape.router, prefix="/scrape", tags=["Scrape"])
    app.include_router(bulk.router, prefix="/bulk", tags=["Bulk"])
    app.include_router(config.router, prefix="/config", tags=["Config"])
    app.include_router(webhooks.router, prefix="/webhooks", tags=["Webhooks"])

    return app
