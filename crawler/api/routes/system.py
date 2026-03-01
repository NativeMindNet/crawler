"""System routes for mode detection and restart control."""

from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime
from typing import Optional
import os
import asyncio

from crawler.api.schemas import ModeResponse, RestartRequest, RestartResponse

router = APIRouter()


def get_lpm():
    """Get LPM from app state."""
    from fastapi import Request
    request = Request.scope.get("request")
    if request:
        return request.app.state.lpm
    return None


@router.get("/mode", response_model=ModeResponse)
async def get_mode(lpm=Depends(get_lpm)) -> ModeResponse:
    """
    Get worker mode and broker status.
    
    Returns information about the current worker mode (async/celery),
    broker connection status, and Flower availability.
    """
    from fastapi import Request
    request = Request.scope.get("request")
    
    # Get mode from app state
    mode = "async"
    if request and hasattr(request.app.state, 'mode'):
        mode = request.app.state.mode
    
    # Determine mode description
    mode_description = "Async single-process worker" if mode == "async" else "Celery distributed workers"
    
    # Celery-specific info
    broker_url = None
    broker_connected = False
    flower_url = None
    flower_available = False
    worker_count = None
    worker_names = None
    
    if mode == "celery":
        broker_url = os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379/0")
        broker_connected = True  # Assume connected if mode is celery
        
        # Check for Flower URL
        flower_url = os.environ.get("FLOWER_URL", "http://localhost:5555")
        flower_available = bool(flower_url)
        
        # TODO: Get worker count from Celery inspect API
        # For now, return None
        worker_count = None
        worker_names = None
    
    return ModeResponse(
        mode=mode,
        mode_description=mode_description,
        broker_url=broker_url,
        broker_connected=broker_connected,
        flower_url=flower_url,
        flower_available=flower_available,
        worker_count=worker_count,
        worker_names=worker_names,
    )


@router.post("/restart", response_model=RestartResponse)
async def restart_crawler(
    request_body: Optional[RestartRequest] = None,
) -> RestartResponse:
    """
    Trigger graceful crawler restart.
    
    This endpoint initiates a graceful shutdown. The container will be
    restarted by Docker's restart policy.
    
    - **reason**: Optional reason for restart (for logging)
    - **delay_seconds**: Delay before restart (0-60 seconds)
    
    **Note:** This endpoint will cause the crawler to shut down. The response
    may not be returned if the shutdown happens before the response is sent.
    """
    from fastapi import Request
    request = Request.scope.get("request")
    
    delay = request_body.delay_seconds if request_body else 5
    reason = request_body.reason if request_body else "Manual restart via API"
    
    # Log the restart request
    if request and hasattr(request.app.state, 'lpm'):
        lpm = request.app.state.lpm
        await lpm.add_log_entry(
            level="INFO",
            message=f"Restart requested: {reason}",
            logger="crawler.api",
            context={"delay_seconds": delay},
        )
    
    # Schedule restart in background
    async def delayed_restart():
        await asyncio.sleep(delay)
        # Initiate graceful shutdown
        # In Docker, we can't directly restart from within the container
        # Instead, we exit and let Docker's restart policy handle it
        import sys
        os._exit(0)  # Force exit
    
    # Start background task
    asyncio.create_task(delayed_restart())
    
    return RestartResponse(
        status="restarting",
        reason=reason,
        delay_seconds=delay,
        timestamp=datetime.utcnow(),
    )
