"""Task management routes."""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
import uuid

from crawler.api.schemas import (
    TaskCreate,
    TaskResponse,
    TaskListResponse,
    TaskRetryRequest,
    TaskRetryResponse,
    BulkRetryResponse,
)
from crawler.models.task import TaskStatus

router = APIRouter()


@router.post("", response_model=TaskResponse, status_code=201)
async def create_task(task: TaskCreate):
    """Create a new task."""
    from fastapi import Request
    request = Request.scope.get("request")
    lpm = request.app.state.lpm if request else None

    if not lpm:
        raise HTTPException(status_code=500, detail="LPM not initialized")

    task_id = str(uuid.uuid4())
    await lpm.add_task(
        url=task.url,
        platform=task.platform,
        priority=task.priority,
        task_id=task_id,
    )

    created_task = await lpm.get_task(task_id)
    if not created_task:
        raise HTTPException(status_code=500, detail="Failed to create task")

    return TaskResponse.model_validate(created_task)


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(task_id: str):
    """Get task by ID."""
    from fastapi import Request
    request = Request.scope.get("request")
    lpm = request.app.state.lpm if request else None

    if not lpm:
        raise HTTPException(status_code=500, detail="LPM not initialized")

    task = await lpm.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    return TaskResponse.model_validate(task)


@router.get("", response_model=TaskListResponse)
async def list_tasks(
    platform: Optional[str] = Query(None, description="Filter by platform"),
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(100, description="Max tasks to return"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    sort_by: str = Query("created_at", description="Sort field (created_at, completed_at, priority)"),
    sort_order: str = Query("desc", description="Sort order (asc, desc)"),
):
    """List all tasks with pagination and sorting."""
    from fastapi import Request
    request = Request.scope.get("request")
    lpm = request.app.state.lpm if request else None

    if not lpm:
        raise HTTPException(status_code=500, detail="LPM not initialized")

    if status:
        status_enum = TaskStatus(status)
        tasks = await lpm.task_repo.get_by_status(status_enum, platform, limit + offset)
    else:
        tasks = await lpm.task_repo.get_all(platform, limit + offset)
    
    # Apply offset and sorting
    tasks = tasks[offset:offset + limit]
    
    # Sort
    if sort_by == "created_at":
        tasks = sorted(tasks, key=lambda t: t.created_at or t.id, reverse=(sort_order == "desc"))
    elif sort_by == "completed_at":
        tasks = sorted(tasks, key=lambda t: t.completed_at or t.id, reverse=(sort_order == "desc"))
    elif sort_by == "priority":
        tasks = sorted(tasks, key=lambda t: t.priority, reverse=(sort_order == "desc"))

    # Get counts
    pending = await lpm.task_repo.count_by_status(TaskStatus.PENDING)
    processing = await lpm.task_repo.count_by_status(TaskStatus.PROCESSING)

    return TaskListResponse(
        tasks=[TaskResponse.model_validate(t) for t in tasks],
        total=len(tasks),
        pending=pending,
        processing=processing,
    )


@router.delete("/{task_id}", status_code=204)
async def delete_task(task_id: str):
    """Delete a task."""
    from fastapi import Request
    request = Request.scope.get("request")
    lpm = request.app.state.lpm if request else None

    if not lpm:
        raise HTTPException(status_code=500, detail="LPM not initialized")

    task = await lpm.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    await lpm.task_repo.delete(task_id)
    return None


@router.post("/{task_id}/retry", response_model=TaskRetryResponse)
async def retry_task(
    task_id: str,
    request_body: Optional[TaskRetryRequest] = None,
):
    """
    Retry a failed task.
    
    Re-queues the task with status 'pending' and increments retry count.
    """
    from fastapi import Request
    request = Request.scope.get("request")
    lpm = request.app.state.lpm if request else None

    if not lpm:
        raise HTTPException(status_code=500, detail="LPM not initialized")

    task = await lpm.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    # Increment retry count
    new_retry_count = await lpm.retry_task(task_id)
    
    # Update priority if requested
    if request_body and request_body.priority is not None:
        task.priority = request_body.priority
        await lpm.task_repo.update(task)

    return TaskRetryResponse(
        task_id=task_id,
        status="pending",
        retry_count=new_retry_count,
        message="Task re-queued successfully",
    )


@router.post("/retry-bulk", response_model=BulkRetryResponse)
async def retry_bulk_tasks(
    status: str = Query("failed", description="Status filter (must be 'failed')"),
    platform: Optional[str] = Query(None, description="Filter by platform"),
    limit: int = Query(100, ge=1, le=1000, description="Max tasks to retry"),
):
    """
    Retry multiple failed tasks.
    
    Re-queues all tasks matching the filters.
    """
    from fastapi import Request
    request = Request.scope.get("request")
    lpm = request.app.state.lpm if request else None

    if not lpm:
        raise HTTPException(status_code=500, detail="LPM not initialized")

    if status != "failed":
        raise HTTPException(status_code=400, detail="Only 'failed' status is supported")

    # Get failed tasks
    failed_tasks = await lpm.task_repo.get_by_status(TaskStatus.FAILED, platform, limit)
    
    # Retry each task
    retried_count = 0
    for task in failed_tasks:
        await lpm.retry_task(task.id)
        retried_count += 1

    return BulkRetryResponse(
        retried_count=retried_count,
        filters={"status": status, "platform": platform, "limit": limit},
        message=f"{retried_count} tasks re-queued successfully",
    )
