"""Bulk job repository for database operations."""

from typing import Optional, List
from datetime import datetime

from crawler.models.bulk_job import BulkJob, BulkJobStatus
from crawler.db.connection import DatabaseConnection


class BulkJobRepository:
    """Repository for bulk job database operations."""

    def __init__(self, db: DatabaseConnection):
        self.db = db

    async def create(self, job: BulkJob) -> None:
        """Create a new bulk job."""
        await self.db.execute(
            """
            INSERT INTO bulk_jobs (
                id, source_file, profile_id, status, total_rows,
                processed_rows, error_rows, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                job.id,
                job.source_file,
                job.profile_id,
                job.status.value,
                job.total_rows,
                job.processed_rows,
                job.error_rows,
                job.created_at.isoformat() if job.created_at else None,
            ),
        )
        await self.db.commit()

    async def get(self, job_id: str) -> Optional[BulkJob]:
        """Get job by ID."""
        row = await self.db.fetchone(
            "SELECT * FROM bulk_jobs WHERE id = ?",
            (job_id,),
        )
        if row:
            return self._row_to_job(row)
        return None

    async def update(self, job: BulkJob) -> None:
        """Update bulk job."""
        await self.db.execute(
            """
            UPDATE bulk_jobs SET
                status = ?,
                total_rows = ?,
                processed_rows = ?,
                error_rows = ?,
                state_manifest_path = ?,
                state_index_path = ?,
                completed_at = ?
            WHERE id = ?
            """,
            (
                job.status.value,
                job.total_rows,
                job.processed_rows,
                job.error_rows,
                job.state_manifest_path,
                job.state_index_path,
                job.completed_at.isoformat() if job.completed_at else None,
                job.id,
            ),
        )
        await self.db.commit()

    async def update_progress(
        self, job_id: str, processed_rows: int, error_rows: int
    ) -> None:
        """Update job progress."""
        await self.db.execute(
            """
            UPDATE bulk_jobs SET
                processed_rows = ?,
                error_rows = ?
            WHERE id = ?
            """,
            (processed_rows, error_rows, job_id),
        )
        await self.db.commit()

    async def mark_processing(self, job_id: str) -> None:
        """Mark job as processing."""
        await self.db.execute(
            """
            UPDATE bulk_jobs SET
                status = ?
            WHERE id = ?
            """,
            (BulkJobStatus.PROCESSING.value, job_id),
        )
        await self.db.commit()

    async def mark_completed(self, job_id: str) -> None:
        """Mark job as completed."""
        await self.db.execute(
            """
            UPDATE bulk_jobs SET
                status = ?,
                completed_at = ?
            WHERE id = ?
            """,
            (
                BulkJobStatus.COMPLETED.value,
                datetime.utcnow().isoformat(),
                job_id,
            ),
        )
        await self.db.commit()

    async def mark_failed(self, job_id: str) -> None:
        """Mark job as failed."""
        await self.db.execute(
            """
            UPDATE bulk_jobs SET
                status = ?,
                completed_at = ?
            WHERE id = ?
            """,
            (
                BulkJobStatus.FAILED.value,
                datetime.utcnow().isoformat(),
                job_id,
            ),
        )
        await self.db.commit()

    async def mark_paused(self, job_id: str) -> None:
        """Mark job as paused."""
        await self.db.execute(
            """
            UPDATE bulk_jobs SET
                status = ?
            WHERE id = ?
            """,
            (BulkJobStatus.PAUSED.value, job_id),
        )
        await self.db.commit()

    async def get_by_status(
        self, status: BulkJobStatus, limit: int = 100
    ) -> List[BulkJob]:
        """Get jobs by status."""
        rows = await self.db.fetchall(
            """
            SELECT * FROM bulk_jobs 
            WHERE status = ?
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (status.value, limit),
        )
        return [self._row_to_job(row) for row in rows]

    async def get_all(self, limit: int = 100) -> List[BulkJob]:
        """Get all jobs."""
        rows = await self.db.fetchall(
            """
            SELECT * FROM bulk_jobs 
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (limit,),
        )
        return [self._row_to_job(row) for row in rows]

    async def get_pending_jobs(self) -> List[BulkJob]:
        """Get pending jobs."""
        return await self.get_by_status(BulkJobStatus.PENDING)

    async def get_processing_jobs(self) -> List[BulkJob]:
        """Get processing jobs."""
        return await self.get_by_status(BulkJobStatus.PROCESSING)

    async def delete(self, job_id: str) -> None:
        """Delete job."""
        await self.db.execute("DELETE FROM bulk_jobs WHERE id = ?", (job_id,))
        await self.db.commit()

    def _row_to_job(self, row: aiosqlite.Row) -> BulkJob:
        """Convert database row to BulkJob."""
        return BulkJob(
            id=row["id"],
            source_file=row["source_file"],
            profile_id=row["profile_id"],
            status=BulkJobStatus(row["status"]),
            total_rows=row["total_rows"],
            processed_rows=row["processed_rows"],
            error_rows=row["error_rows"],
            state_manifest_path=row["state_manifest_path"],
            state_index_path=row["state_index_path"],
            created_at=datetime.fromisoformat(row["created_at"]) if row["created_at"] else None,
            completed_at=datetime.fromisoformat(row["completed_at"]) if row["completed_at"] else None,
        )
