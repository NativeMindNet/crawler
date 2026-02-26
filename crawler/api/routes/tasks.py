"""Task management routes."""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
import uuid

from crawler.api.schemas import TaskCreate, TaskResponse, TaskListResponse
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
):
    """List all tasks."""
    from fastapi import Request
    request = Request.scope.get("request")
    lpm = request.app.state.lpm if request else None

    if not lpm:
        raise HTTPException(status_code=500, detail="LPM not initialized")

    if status:
        status_enum = TaskStatus(status)
        tasks = await lpm.task_repo.get_by_status(status_enum, platform, limit)
    else:
        tasks = await lpm.task_repo.get_all(platform, limit)

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
