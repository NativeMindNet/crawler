"""Health check routes."""

from fastapi import APIRouter, Depends
from datetime import datetime

from crawler.api.schemas import HealthResponse
from crawler.lpm import LocalPersistenceManager

router = APIRouter()


def get_lpm() -> LocalPersistenceManager:
    """Get LPM from app state."""
    from fastapi import Request
    # This is a simplified version - in production use proper dependency injection
    return None


@router.get("", response_model=HealthResponse)
@router.get("/", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Health check endpoint."""
    from fastapi import Request
    request = Request.scope.get("request")
    if request:
        lpm = request.app.state.lpm
        platform = request.app.state.platform
    else:
        # Fallback for testing
        lpm = None
        platform = None

    queue_depth = 0
    if lpm:
        queue_depth = await lpm.get_queue_depth()

    return HealthResponse(
        status="healthy",
        platform=platform,
        queue_depth=queue_depth,
        timestamp=datetime.utcnow(),
    )
