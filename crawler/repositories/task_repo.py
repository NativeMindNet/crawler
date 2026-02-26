"""Task repository for database operations."""

import asyncio
from typing import Optional, List
from datetime import datetime

from crawler.models.task import Task, TaskStatus
from crawler.db.connection import DatabaseConnection


class TaskRepository:
    """Repository for task database operations."""

    def __init__(self, db: DatabaseConnection):
        self.db = db

    async def create(self, task: Task) -> None:
        """Create a new task."""
        await self.db.execute(
            """
            INSERT INTO tasks (id, url, platform, status, priority, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                task.id,
                task.url,
                task.platform,
                task.status.value,
                task.priority,
                task.created_at.isoformat() if task.created_at else None,
            ),
        )
        await self.db.commit()

    async def get(self, task_id: str) -> Optional[Task]:
        """Get task by ID."""
        row = await self.db.fetchone(
            "SELECT * FROM tasks WHERE id = ?",
            (task_id,),
        )
        if row:
            return self._row_to_task(row)
        return None

    async def get_next_pending(self, platform: Optional[str] = None) -> Optional[Task]:
        """Get next pending task ordered by priority."""
        if platform:
            row = await self.db.fetchone(
                """
                SELECT * FROM tasks 
                WHERE status = ? AND platform = ?
                ORDER BY priority DESC, created_at ASC
                LIMIT 1
                """,
                (TaskStatus.PENDING.value, platform),
            )
        else:
            row = await self.db.fetchone(
                """
                SELECT * FROM tasks 
                WHERE status = ?
                ORDER BY priority DESC, created_at ASC
                LIMIT 1
                """,
                (TaskStatus.PENDING.value,),
            )

        if row:
            return self._row_to_task(row)
        return None

    async def update(self, task: Task) -> None:
        """Update task."""
        await self.db.execute(
            """
            UPDATE tasks SET
                status = ?,
                priority = ?,
                started_at = ?,
                completed_at = ?,
                result_path = ?,
                error = ?,
                retry_count = ?,
                discovered_links_count = ?
            WHERE id = ?
            """,
            (
                task.status.value,
                task.priority,
                task.started_at.isoformat() if task.started_at else None,
                task.completed_at.isoformat() if task.completed_at else None,
                task.result_path,
                task.error,
                task.retry_count,
                task.discovered_links_count,
                task.id,
            ),
        )
        await self.db.commit()

    async def mark_processing(self, task_id: str) -> bool:
        """Mark task as processing. Returns True if successful."""
        await self.db.execute(
            """
            UPDATE tasks SET
                status = ?,
                started_at = ?
            WHERE id = ? AND status = ?
            """,
            (
                TaskStatus.PROCESSING.value,
                datetime.utcnow().isoformat(),
                task_id,
                TaskStatus.PENDING.value,
            ),
        )
        await self.db.commit()
        return self.db.connection.total_changes > 0

    async def mark_completed(self, task_id: str, result_path: str) -> None:
        """Mark task as completed."""
        await self.db.execute(
            """
            UPDATE tasks SET
                status = ?,
                completed_at = ?,
                result_path = ?
            WHERE id = ?
            """,
            (
                TaskStatus.COMPLETED.value,
                datetime.utcnow().isoformat(),
                result_path,
                task_id,
            ),
        )
        await self.db.commit()

    async def mark_failed(self, task_id: str, error: str) -> None:
        """Mark task as failed."""
        await self.db.execute(
            """
            UPDATE tasks SET
                status = ?,
                completed_at = ?,
                error = ?
            WHERE id = ?
            """,
            (
                TaskStatus.FAILED.value,
                datetime.utcnow().isoformat(),
                error,
                task_id,
            ),
        )
        await self.db.commit()

    async def increment_retry(self, task_id: str) -> int:
        """Increment retry count and return new count."""
        await self.db.execute(
            """
            UPDATE tasks SET
                retry_count = retry_count + 1,
                status = ?
            WHERE id = ?
            """,
            (TaskStatus.PENDING.value, task_id),
        )
        await self.db.commit()

        row = await self.db.fetchone(
            "SELECT retry_count FROM tasks WHERE id = ?",
            (task_id,),
        )
        return row["retry_count"] if row else 0

    async def get_by_status(
        self, status: TaskStatus, platform: Optional[str] = None, limit: int = 100
    ) -> List[Task]:
        """Get tasks by status."""
        if platform:
            rows = await self.db.fetchall(
                """
                SELECT * FROM tasks 
                WHERE status = ? AND platform = ?
                ORDER BY priority DESC, created_at ASC
                LIMIT ?
                """,
                (status.value, platform, limit),
            )
        else:
            rows = await self.db.fetchall(
                """
                SELECT * FROM tasks 
                WHERE status = ?
                ORDER BY priority DESC, created_at ASC
                LIMIT ?
                """,
                (status.value, limit),
            )

        return [self._row_to_task(row) for row in rows]

    async def get_all(self, platform: Optional[str] = None, limit: int = 1000) -> List[Task]:
        """Get all tasks."""
        if platform:
            rows = await self.db.fetchall(
                """
                SELECT * FROM tasks 
                WHERE platform = ?
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (platform, limit),
            )
        else:
            rows = await self.db.fetchall(
                """
                SELECT * FROM tasks 
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (limit,),
            )

        return [self._row_to_task(row) for row in rows]

    async def count_by_status(self, status: TaskStatus) -> int:
        """Count tasks by status."""
        row = await self.db.fetchone(
            "SELECT COUNT(*) as count FROM tasks WHERE status = ?",
            (status.value,),
        )
        return row["count"] if row else 0

    async def count_pending(self) -> int:
        """Count pending tasks."""
        return await self.count_by_status(TaskStatus.PENDING)

    async def delete(self, task_id: str) -> None:
        """Delete task."""
        await self.db.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        await self.db.commit()

    def _row_to_task(self, row: aiosqlite.Row) -> Task:
        """Convert database row to Task."""
        return Task(
            id=row["id"],
            url=row["url"],
            platform=row["platform"],
            status=TaskStatus(row["status"]),
            priority=row["priority"],
            created_at=datetime.fromisoformat(row["created_at"]) if row["created_at"] else None,
            started_at=datetime.fromisoformat(row["started_at"]) if row["started_at"] else None,
            completed_at=datetime.fromisoformat(row["completed_at"]) if row["completed_at"] else None,
            result_path=row["result_path"],
            error=row["error"],
            retry_count=row["retry_count"],
            discovered_links_count=row["discovered_links_count"],
        )
