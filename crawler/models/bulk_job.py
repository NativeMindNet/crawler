"""Bulk job model and status enum."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class BulkJobStatus(str, Enum):
    """Bulk job status values."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"


@dataclass
class BulkJob:
    """Represents a bulk ingestion job."""
    id: str
    source_file: str
    profile_id: str
    status: BulkJobStatus = BulkJobStatus.PENDING
    total_rows: int = 0
    processed_rows: int = 0
    error_rows: int = 0
    state_manifest_path: Optional[str] = None
    state_index_path: Optional[str] = None
    created_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if isinstance(self.status, str):
            self.status = BulkJobStatus(self.status)

    def mark_processing(self) -> None:
        """Mark job as processing."""
        self.status = BulkJobStatus.PROCESSING

    def mark_completed(self) -> None:
        """Mark job as completed."""
        self.status = BulkJobStatus.COMPLETED
        self.completed_at = datetime.utcnow()

    def mark_failed(self) -> None:
        """Mark job as failed."""
        self.status = BulkJobStatus.FAILED
        self.completed_at = datetime.utcnow()

    def mark_paused(self) -> None:
        """Mark job as paused."""
        self.status = BulkJobStatus.PAUSED

    def update_progress(self, processed: int, error_rows: int) -> None:
        """Update job progress."""
        self.processed_rows = processed
        self.error_rows = error_rows

    @property
    def progress_percent(self) -> float:
        """Get progress as percentage."""
        if self.total_rows == 0:
            return 0.0
        return (self.processed_rows / self.total_rows) * 100

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "source_file": self.source_file,
            "profile_id": self.profile_id,
            "status": self.status.value,
            "total_rows": self.total_rows,
            "processed_rows": self.processed_rows,
            "error_rows": self.error_rows,
            "state_manifest_path": self.state_manifest_path,
            "state_index_path": self.state_index_path,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "progress_percent": self.progress_percent,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "BulkJob":
        """Create BulkJob from dictionary."""
        return cls(
            id=data["id"],
            source_file=data["source_file"],
            profile_id=data["profile_id"],
            status=BulkJobStatus(data["status"]),
            total_rows=data.get("total_rows", 0),
            processed_rows=data.get("processed_rows", 0),
            error_rows=data.get("error_rows", 0),
            state_manifest_path=data.get("state_manifest_path"),
            state_index_path=data.get("state_index_path"),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else None,
            completed_at=datetime.fromisoformat(data["completed_at"]) if data.get("completed_at") else None,
        )
