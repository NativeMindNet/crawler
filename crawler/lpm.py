"""Local Persistence Manager - Core state and persistence layer."""

import asyncio
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime
import uuid

from crawler.db.connection import DatabaseConnection, init_database
from crawler.repositories.task_repo import TaskRepository
from crawler.repositories.bulk_job_repo import BulkJobRepository
from crawler.repositories.link_repo import LinkRepository
from crawler.models.task import Task, TaskStatus
from crawler.models.bulk_job import BulkJob, BulkJobStatus
from crawler.models.parsed_result import DiscoveredLink, RelationshipType
from crawler.models.ingestion_job import IngestionJob, IngestionJobStatus


class LocalPersistenceManager:
    """
    Central persistence manager for crawler state.
    
    Handles:
    - Task queue management
    - Bulk job tracking
    - Discovered link management
    - Result storage coordination
    """

    def __init__(self, db_path: str, data_dir: str):
        self.db_path = db_path
        self.data_dir = Path(data_dir)
        self.db: Optional[DatabaseConnection] = None
        self.task_repo: Optional[TaskRepository] = None
        self.bulk_job_repo: Optional[BulkJobRepository] = None
        self.link_repo: Optional[LinkRepository] = None
        self._lock = asyncio.Lock()

    async def initialize(self) -> None:
        """Initialize database connection and repositories."""
        self.db = await init_database(self.db_path)
        self.task_repo = TaskRepository(self.db)
        self.bulk_job_repo = BulkJobRepository(self.db)
        self.link_repo = LinkRepository(self.db)

        # Ensure data directories exist
        (self.data_dir / "results").mkdir(parents=True, exist_ok=True)
        (self.data_dir / "raw").mkdir(parents=True, exist_ok=True)
        (self.data_dir / "state").mkdir(parents=True, exist_ok=True)

    async def close(self) -> None:
        """Close database connection."""
        if self.db:
            await self.db.close()

    # === Task Queue Operations ===

    async def add_task(
        self,
        url: str,
        platform: str,
        priority: int = 0,
        task_id: Optional[str] = None,
    ) -> str:
        """Add a task to the queue. Returns task ID."""
        if task_id is None:
            task_id = str(uuid.uuid4())

        task = Task(
            id=task_id,
            url=url,
            platform=platform,
            priority=priority,
        )
        await self.task_repo.create(task)
        return task_id

    async def get_next_task(self, platform: Optional[str] = None) -> Optional[Task]:
        """Get next pending task."""
        return await self.task_repo.get_next_pending(platform)

    async def complete_task(self, task_id: str, result_path: str) -> None:
        """Mark task as completed."""
        await self.task_repo.mark_completed(task_id, result_path)

    async def fail_task(self, task_id: str, error: str) -> None:
        """Mark task as failed."""
        await self.task_repo.mark_failed(task_id, error)

    async def start_task(self, task_id: str) -> bool:
        """Mark task as processing. Returns False if task not found."""
        return await self.task_repo.mark_processing(task_id)

    async def retry_task(self, task_id: str) -> int:
        """Increment retry count. Returns new retry count."""
        return await self.task_repo.increment_retry(task_id)

    async def get_task(self, task_id: str) -> Optional[Task]:
        """Get task by ID."""
        return await self.task_repo.get(task_id)

    async def get_pending_tasks(self, limit: int = 100) -> List[Task]:
        """Get pending tasks."""
        return await self.task_repo.get_by_status(TaskStatus.PENDING, limit=limit)

    async def get_queue_depth(self) -> int:
        """Get count of pending tasks."""
        return await self.task_repo.count_pending()

    # === Discovered Link Operations ===

    async def add_discovered_links(
        self, source_task_id: str, links: List[DiscoveredLink]
    ) -> int:
        """Add discovered links. Returns count added."""
        return await self.link_repo.add_batch(links)

    async def get_unprocessed_links(
        self, source_task_id: Optional[str] = None
    ) -> List[DiscoveredLink]:
        """Get unprocessed discovered links."""
        return await self.link_repo.get_unprocessed(source_task_id)

    async def mark_link_processed(self, url: str) -> None:
        """Mark a link as processed."""
        await self.link_repo.mark_processed_by_url(url)

    # === Bulk Job Operations ===

    async def create_bulk_job(
        self,
        source_file: str,
        profile_id: str,
        total_rows: int = 0,
        job_id: Optional[str] = None,
    ) -> str:
        """Create a bulk ingestion job. Returns job ID."""
        if job_id is None:
            job_id = str(uuid.uuid4())

        job = BulkJob(
            id=job_id,
            source_file=source_file,
            profile_id=profile_id,
            total_rows=total_rows,
        )
        await self.bulk_job_repo.create(job)
        return job_id

    async def get_bulk_job(self, job_id: str) -> Optional[BulkJob]:
        """Get bulk job by ID."""
        return await self.bulk_job_repo.get(job_id)

    async def update_bulk_progress(
        self, job_id: str, processed: int, errors: int
    ) -> None:
        """Update bulk job progress."""
        await self.bulk_job_repo.update_progress(job_id, processed, errors)

    async def complete_bulk_job(self, job_id: str) -> None:
        """Mark bulk job as completed."""
        await self.bulk_job_repo.mark_completed(job_id)

    async def fail_bulk_job(self, job_id: str) -> None:
        """Mark bulk job as failed."""
        await self.bulk_job_repo.mark_failed(job_id)

    async def pause_bulk_job(self, job_id: str) -> None:
        """Mark bulk job as paused."""
        await self.bulk_job_repo.mark_paused(job_id)

    # === Result Storage ===

    def get_result_path(self, task_id: str, platform: str) -> Path:
        """Get path for task result JSON."""
        return self.data_dir / "results" / platform / f"{task_id}.json"

    def get_raw_html_path(self, task_id: str, platform: str) -> Path:
        """Get path for raw HTML."""
        return self.data_dir / "raw" / platform / "html" / f"{task_id}.html"

    def get_raw_screenshot_path(self, task_id: str, platform: str) -> Path:
        """Get path for screenshot."""
        return self.data_dir / "raw" / platform / "screenshots" / f"{task_id}.png"

    def get_image_path(
        self, task_id: str, platform: str, image_name: str
    ) -> Path:
        """Get path for downloaded image."""
        images_dir = self.data_dir / "raw" / platform / "images" / task_id
        images_dir.mkdir(parents=True, exist_ok=True)
        return images_dir / image_name

    async def save_result(
        self, task_id: str, platform: str, data: Dict[str, Any]
    ) -> str:
        """Save task result to JSON. Returns result path."""
        import json

        result_path = self.get_result_path(task_id, platform)
        result_path.parent.mkdir(parents=True, exist_ok=True)

        with open(result_path, "w") as f:
            json.dump(data, f, indent=2, default=str)

        return str(result_path)

    async def get_result(
        self, task_id: str, platform: str
    ) -> Optional[Dict[str, Any]]:
        """Get task result from JSON."""
        import json

        result_path = self.get_result_path(task_id, platform)
        if not result_path.exists():
            return None

        with open(result_path, "r") as f:
            return json.load(f)

    # === State Serialization ===

    def get_state_path(self, name: str, extension: str = "json") -> Path:
        """Get path for state file."""
        return self.data_dir / "state" / f"{name}.{extension}"

    async def save_state(
        self, name: str, data: Any, format: str = "json"
    ) -> str:
        """Save state to file. Returns path."""
        state_path = self.get_state_path(name, format)
        state_path.parent.mkdir(parents=True, exist_ok=True)

        if format == "json":
            import json
            with open(state_path, "w") as f:
                json.dump(data, f, indent=2, default=str)
        elif format == "msgpack":
            import msgpack
            with open(state_path, "wb") as f:
                msgpack.pack(data, f)
        elif format == "pickle":
            import pickle
            with open(state_path, "wb") as f:
                pickle.dump(data, f)
        else:
            raise ValueError(f"Unknown format: {format}")

        return str(state_path)

    async def load_state(self, name: str, format: str = "json") -> Optional[Any]:
        """Load state from file."""
        state_path = self.get_state_path(name, format)
        if not state_path.exists():
            return None

        if format == "json":
            import json
            with open(state_path, "r") as f:
                return json.load(f)
        elif format == "msgpack":
            import msgpack
            with open(state_path, "rb") as f:
                return msgpack.unpack(f)
        elif format == "pickle":
            import pickle
            with open(state_path, "rb") as f:
                return pickle.load(f)
        else:
            raise ValueError(f"Unknown format: {format}")

    # === Utility Methods ===

    async def get_stats(self) -> Dict[str, Any]:
        """Get queue and job statistics."""
        pending = await self.task_repo.count_by_status(TaskStatus.PENDING)
        processing = await self.task_repo.count_by_status(TaskStatus.PROCESSING)
        completed = await self.task_repo.count_by_status(TaskStatus.COMPLETED)
        failed = await self.task_repo.count_by_status(TaskStatus.FAILED)

        return {
            "tasks": {
                "pending": pending,
                "processing": processing,
                "completed": completed,
                "failed": failed,
                "total": pending + processing + completed + failed,
            },
            "discovered_links_unprocessed": await self.link_repo.count_unprocessed(),
        }
