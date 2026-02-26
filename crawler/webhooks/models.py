"""Webhook payload models."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, List, Optional
from enum import Enum


class WebhookEvent(str, Enum):
    """Webhook event types."""
    TASK_COMPLETED = "task.completed"
    TASK_FAILED = "task.failed"
    BULK_COMPLETED = "bulk.completed"
    BULK_FAILED = "bulk.failed"
    TEST = "test"


@dataclass
class WebhookPayload:
    """Webhook payload structure."""
    event: WebhookEvent
    task_id: Optional[str] = None
    job_id: Optional[str] = None
    platform: str = ""
    timestamp: str = ""
    result: Optional[Dict[str, Any]] = None
    raw_paths: Optional[Dict[str, str]] = None
    stats: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    signature: Optional[str] = None

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.utcnow().isoformat()

    @classmethod
    def task_completed(
        cls,
        task_id: str,
        platform: str,
        result: Dict[str, Any],
        raw_paths: Dict[str, str],
    ) -> "WebhookPayload":
        """Create task completed payload."""
        return cls(
            event=WebhookEvent.TASK_COMPLETED,
            task_id=task_id,
            platform=platform,
            result=result,
            raw_paths=raw_paths,
        )

    @classmethod
    def task_failed(
        cls,
        task_id: str,
        platform: str,
        error: str,
    ) -> "WebhookPayload":
        """Create task failed payload."""
        return cls(
            event=WebhookEvent.TASK_FAILED,
            task_id=task_id,
            platform=platform,
            error=error,
        )

    @classmethod
    def bulk_completed(
        cls,
        job_id: str,
        platform: str,
        stats: Dict[str, Any],
    ) -> "WebhookPayload":
        """Create bulk completed payload."""
        return cls(
            event=WebhookEvent.BULK_COMPLETED,
            job_id=job_id,
            platform=platform,
            stats=stats,
        )

    @classmethod
    def bulk_failed(
        cls,
        job_id: str,
        platform: str,
        error: str,
    ) -> "WebhookPayload":
        """Create bulk failed payload."""
        return cls(
            event=WebhookEvent.BULK_FAILED,
            job_id=job_id,
            platform=platform,
            error=error,
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "event": self.event.value,
            "task_id": self.task_id,
            "job_id": self.job_id,
            "platform": self.platform,
            "timestamp": self.timestamp,
            "result": self.result,
            "raw_paths": self.raw_paths,
            "stats": self.stats,
            "error": self.error,
        }
