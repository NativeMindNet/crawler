"""Task model and status enum."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class TaskStatus(str, Enum):
    """Task status values."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class Task:
    """Represents a crawling task."""
    id: str
    url: str
    platform: str
    status: TaskStatus = TaskStatus.PENDING
    priority: int = 0
    created_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result_path: Optional[str] = None
    error: Optional[str] = None
    retry_count: int = 0
    discovered_links_count: int = 0

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if isinstance(self.status, str):
            self.status = TaskStatus(self.status)

    def mark_processing(self) -> None:
        """Mark task as processing."""
        self.status = TaskStatus.PROCESSING
        self.started_at = datetime.utcnow()

    def mark_completed(self, result_path: str) -> None:
        """Mark task as completed."""
        self.status = TaskStatus.COMPLETED
        self.completed_at = datetime.utcnow()
        self.result_path = result_path

    def mark_failed(self, error: str) -> None:
        """Mark task as failed."""
        self.status = TaskStatus.FAILED
        self.completed_at = datetime.utcnow()
        self.error = error

    def increment_retry(self) -> None:
        """Increment retry count."""
        self.retry_count += 1

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "url": self.url,
            "platform": self.platform,
            "status": self.status.value,
            "priority": self.priority,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "result_path": self.result_path,
            "error": self.error,
            "retry_count": self.retry_count,
            "discovered_links_count": self.discovered_links_count,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Task":
        """Create Task from dictionary."""
        return cls(
            id=data["id"],
            url=data["url"],
            platform=data["platform"],
            status=TaskStatus(data["status"]),
            priority=data.get("priority", 0),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else None,
            started_at=datetime.fromisoformat(data["started_at"]) if data.get("started_at") else None,
            completed_at=datetime.fromisoformat(data["completed_at"]) if data.get("completed_at") else None,
            result_path=data.get("result_path"),
            error=data.get("error"),
            retry_count=data.get("retry_count", 0),
            discovered_links_count=data.get("discovered_links_count", 0),
        )
