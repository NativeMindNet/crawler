"""Logs routes for log viewing and searching."""

from fastapi import APIRouter, Depends, Query
from datetime import datetime
from typing import Optional

from crawler.api.schemas import LogListResponse, LogEntry

router = APIRouter()


def get_lpm():
    """Get LPM from app state."""
    from fastapi import Request
    request = Request.scope.get("request")
    if request:
        return request.app.state.lpm
    return None


@router.get("", response_model=LogListResponse)
async def get_logs(
    level: Optional[str] = Query(None, description="Filter by log level (INFO, WARN, ERROR)"),
    search: Optional[str] = Query(None, description="Full-text search in message"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=200, description="Items per page"),
    since: Optional[datetime] = Query(None, description="Only return logs after this timestamp"),
    lpm=Depends(get_lpm),
) -> LogListResponse:
    """
    Get paginated log entries with filters.
    
    - **level**: Filter by log level (DEBUG, INFO, WARN, ERROR, CRITICAL)
    - **search**: Full-text search in message
    - **page**: Page number (1-based)
    - **page_size**: Items per page (max 200)
    - **since**: Only return logs after this timestamp
    """
    if not lpm:
        return LogListResponse(
            entries=[],
            total=0,
            page=page,
            page_size=page_size,
            total_pages=0,
        )
    
    # Get logs from LPM
    result = await lpm.get_logs(
        level=level,
        search=search,
        page=page,
        page_size=page_size,
        since=since,
    )
    
    # Convert to Pydantic models
    entries = [
        LogEntry(
            id=e["id"],
            timestamp=e["timestamp"],
            level=e["level"],
            message=e["message"],
            logger=e["logger"],
            context=e["context"],
        )
        for e in result["entries"]
    ]
    
    return LogListResponse(
        entries=entries,
        total=result["total"],
        page=result["page"],
        page_size=result["page_size"],
        total_pages=result["total_pages"],
    )
