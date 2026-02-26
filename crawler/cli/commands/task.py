"""Task CLI commands."""

from typing import Optional
import uuid

from crawler.lpm import LocalPersistenceManager
from crawler.models.task import TaskStatus


async def task_add_command(
    url: str,
    platform: str,
    priority: int,
) -> None:
    """Add a task to the queue."""
    import os

    db_path = os.environ.get("DB_PATH", "/data/state/crawler.db")

    lpm = LocalPersistenceManager(db_path, "/data")
    await lpm.initialize()

    try:
        task_id = await lpm.add_task(url, platform, priority)
        print(f"✓ Task added: {task_id}")
        print(f"  URL: {url}")
        print(f"  Platform: {platform}")
        print(f"  Priority: {priority}")
    finally:
        await lpm.close()


async def task_status_command(
    task_id: str,
    db_path: str,
) -> None:
    """Get task status."""
    lpm = LocalPersistenceManager(db_path, "/data")
    await lpm.initialize()

    try:
        task = await lpm.get_task(task_id)

        if not task:
            print(f"✗ Task not found: {task_id}")
            return

        print(f"Task: {task_id}")
        print(f"  Status: {task.status.value}")
        print(f"  URL: {task.url}")
        print(f"  Platform: {task.platform}")
        print(f"  Priority: {task.priority}")
        print(f"  Created: {task.created_at}")
        if task.started_at:
            print(f"  Started: {task.started_at}")
        if task.completed_at:
            print(f"  Completed: {task.completed_at}")
        if task.error:
            print(f"  Error: {task.error}")
        if task.result_path:
            print(f"  Result: {task.result_path}")
    finally:
        await lpm.close()


async def task_list_command(
    platform: Optional[str],
    status: Optional[str],
    limit: int,
    db_path: str,
) -> None:
    """List all tasks."""
    from rich.console import Console
    from rich.table import Table

    console = Console()

    lpm = LocalPersistenceManager(db_path, "/data")
    await lpm.initialize()

    try:
        # Get tasks
        if status:
            status_enum = TaskStatus(status)
            tasks = await lpm.task_repo.get_by_status(status_enum, platform, limit)
        else:
            tasks = await lpm.task_repo.get_all(platform, limit)

        if not tasks:
            print("No tasks found")
            return

        # Display table
        table = Table(title=f"Tasks ({len(tasks)})")
        table.add_column("ID", style="cyan", no_wrap=True)
        table.add_column("Status", style="green")
        table.add_column("Platform", style="yellow")
        table.add_column("URL", style="white", no_wrap=True)
        table.add_column("Priority", justify="right")
        table.add_column("Created", style="dim")

        for task in tasks:
            table.add_row(
                task.id[:8] + "...",
                task.status.value,
                task.platform,
                task.url[:50] + "..." if len(task.url) > 50 else task.url,
                str(task.priority),
                str(task.created_at),
            )

        console.print(table)

    finally:
        await lpm.close()
