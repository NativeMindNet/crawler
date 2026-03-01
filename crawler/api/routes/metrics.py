"""Metrics routes for system monitoring."""

from fastapi import APIRouter, Depends
from datetime import datetime
import psutil
import time

from crawler.api.schemas import MetricsResponse
from crawler.lpm import LocalPersistenceManager

router = APIRouter()


def get_lpm() -> LocalPersistenceManager:
    """Get LPM from app state."""
    from fastapi import Request
    request = Request.scope.get("request")
    if request:
        return request.app.state.lpm
    return None


def format_uptime(seconds: int) -> str:
    """Format uptime in human-readable format."""
    hours, remainder = divmod(seconds, 3600)
    minutes, secs = divmod(remainder, 60)
    
    if hours > 0:
        return f"{hours}h {minutes}m"
    elif minutes > 0:
        return f"{minutes}m {secs}s"
    else:
        return f"{secs}s"


@router.get("", response_model=MetricsResponse)
async def get_metrics(lpm: LocalPersistenceManager = Depends(get_lpm)) -> MetricsResponse:
    """
    Get system metrics.
    
    Returns CPU, memory, uptime, and task throughput metrics.
    """
    # CPU and memory
    cpu_percent = psutil.cpu_percent(interval=0.1)
    memory = psutil.virtual_memory()
    memory_percent = memory.percent
    memory_mb = memory.used / (1024 * 1024)
    
    # Uptime
    boot_time = psutil.boot_time()
    uptime_seconds = int(time.time() - boot_time)
    uptime_human = format_uptime(uptime_seconds)
    
    # Task metrics from LPM
    tasks_per_minute = 0.0
    tasks_per_hour = 0.0
    success_rate_1h = 0.0
    success_rate_24h = 0.0
    
    if lpm:
        # Get task statistics from LPM
        stats = await lpm.get_task_statistics()
        tasks_per_minute = stats.get('tasks_per_minute', 0.0)
        tasks_per_hour = stats.get('tasks_per_hour', 0.0)
        success_rate_1h = stats.get('success_rate_1h', 0.0)
        success_rate_24h = stats.get('success_rate_24h', 0.0)
    
    # Get worker mode
    from fastapi import Request
    request = Request.scope.get("request")
    mode = "async"
    if request and hasattr(request.app.state, 'mode'):
        mode = request.app.state.mode
    elif request and hasattr(request.app.state, 'config'):
        mode = getattr(request.app.state.config, 'mode', 'async')
    
    return MetricsResponse(
        cpu_percent=cpu_percent,
        memory_percent=memory_percent,
        memory_mb=round(memory_mb, 2),
        uptime_seconds=uptime_seconds,
        uptime_human=uptime_human,
        tasks_per_minute=tasks_per_minute,
        tasks_per_hour=tasks_per_hour,
        success_rate_1h=success_rate_1h,
        success_rate_24h=success_rate_24h,
        mode=mode,
        timestamp=datetime.utcnow(),
    )
