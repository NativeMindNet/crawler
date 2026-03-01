"""Health check routes."""

from fastapi import APIRouter, Depends
from datetime import datetime
from pathlib import Path

from crawler.api.schemas import HealthResponseEnhanced, QueueDetails, LpmStatus
from crawler.lpm import LocalPersistenceManager
from crawler.models.task import TaskStatus

router = APIRouter()


def get_lpm() -> LocalPersistenceManager:
    """Get LPM from app state."""
    from fastapi import Request
    request = Request.scope.get("request")
    if request:
        return request.app.state.lpm
    return None


@router.get("", response_model=HealthResponseEnhanced)
@router.get("/", response_model=HealthResponseEnhanced)
async def health_check(lpm: LocalPersistenceManager = Depends(get_lpm)) -> HealthResponseEnhanced:
    """
    Enhanced health check endpoint.
    
    Returns health status with detailed queue breakdown and LPM storage status.
    """
    from fastapi import Request
    request = Request.scope.get("request")
    
    platform = None
    if request:
        platform = request.app.state.platform
    
    # Get queue depth and breakdown
    queue_depth = 0
    pending = 0
    processing = 0
    failed = 0
    
    if lpm:
        queue_depth = await lpm.get_queue_depth()
        pending = await lpm.task_repo.count_by_status(TaskStatus.PENDING)
        processing = await lpm.task_repo.count_by_status(TaskStatus.PROCESSING)
        failed = await lpm.task_repo.count_by_status(TaskStatus.FAILED)
    
    # Get LPM storage status
    db_size_mb = 0.0
    pending_files = 0
    raw_files = 0
    
    if lpm and hasattr(lpm, 'data_dir'):
        data_dir = Path(lpm.data_dir)
        
        # Database size
        db_path = Path(lpm.db_path)
        if db_path.exists():
            db_size_mb = round(db_path.stat().st_size / (1024 * 1024), 2)
        
        # Count pending files
        pending_dir = data_dir / "results" / "pending"
        if pending_dir.exists():
            pending_files = len(list(pending_dir.glob("*.json")))
        
        # Count raw files
        raw_dir = data_dir / "raw"
        if raw_dir.exists():
            raw_files = sum(1 for _ in raw_dir.rglob("*") if _.is_file())
    
    return HealthResponseEnhanced(
        status="healthy",
        platform=platform,
        queue_depth=queue_depth,
        queue_details=QueueDetails(
            pending=pending,
            processing=processing,
            failed=failed,
        ),
        lpm_status=LpmStatus(
            db_size_mb=db_size_mb,
            pending_files=pending_files,
            raw_files=raw_files,
        ),
        timestamp=datetime.utcnow(),
    )
