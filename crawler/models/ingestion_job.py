"""Ingestion job model and status enum."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any


class IngestionJobStatus(str, Enum):
    """Ingestion job status values."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"


@dataclass
class IngestionJob:
    """Represents a data ingestion job."""
    id: str
    source_file: str
    profile_id: str
    status: IngestionJobStatus = IngestionJobStatus.PENDING
    total_rows: int = 0
    processed_rows: int = 0
    error_rows: int = 0
    state: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if isinstance(self.status, str):
            self.status = IngestionJobStatus(self.status)

    def mark_processing(self) -> None:
        """Mark job as processing."""
        self.status = IngestionJobStatus.PROCESSING

    def mark_completed(self) -> None:
        """Mark job as completed."""
        self.status = IngestionJobStatus.COMPLETED
        self.completed_at = datetime.utcnow()

    def mark_failed(self) -> None:
        """Mark job as failed."""
        self.status = IngestionJobStatus.FAILED
        self.completed_at = datetime.utcnow()

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
            "state": self.state,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "progress_percent": self.progress_percent,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "IngestionJob":
        """Create from dictionary."""
        return cls(
            id=data["id"],
            source_file=data["source_file"],
            profile_id=data["profile_id"],
            status=IngestionJobStatus(data["status"]),
            total_rows=data.get("total_rows", 0),
            processed_rows=data.get("processed_rows", 0),
            error_rows=data.get("error_rows", 0),
            state=data.get("state"),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else None,
            completed_at=datetime.fromisoformat(data["completed_at"]) if data.get("completed_at") else None,
        )
