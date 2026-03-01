"""API schemas (Pydantic models)."""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum


class TaskStatusEnum(str, Enum):
    """Task status values."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


# === Task Schemas ===

class TaskCreate(BaseModel):
    """Request to create a task."""
    url: str = Field(..., description="URL to scrape")
    platform: str = Field(..., description="Platform name")
    priority: int = Field(default=0, description="Task priority")


class TaskResponse(BaseModel):
    """Task response."""
    id: str
    url: str
    platform: str
    status: TaskStatusEnum
    priority: int
    created_at: Optional[datetime]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    result_path: Optional[str]
    error: Optional[str]
    retry_count: int

    class Config:
        from_attributes = True


class TaskListResponse(BaseModel):
    """List of tasks."""
    tasks: List[TaskResponse]
    total: int
    pending: int
    processing: int


# === Scrape Schemas ===

class ScrapeRequest(BaseModel):
    """Request to scrape a URL."""
    url: str = Field(..., description="URL to scrape")
    platform: str = Field(..., description="Platform name")
    parse: bool = Field(default=True, description="Whether to parse after scraping")
    priority: int = Field(default=0, description="Task priority")


class ScrapeResponse(BaseModel):
    """Scrape result."""
    task_id: str
    status: str
    parcel_id: Optional[str]
    data: Optional[Dict[str, Any]]
    image_urls: List[str]
    external_links: Dict[str, str]
    raw_paths: Dict[str, str]
    error: Optional[str]


# === Bulk Schemas ===

class BulkIngestRequest(BaseModel):
    """Request to start bulk ingestion."""
    file_path: str = Field(..., description="Path to source file")
    profile: str = Field(..., description="Mapping profile name")
    platform: str = Field(..., description="Platform name")


class BulkStatusResponse(BaseModel):
    """Bulk job status."""
    id: str
    source_file: str
    profile_id: str
    status: str
    total_rows: int
    processed_rows: int
    error_rows: int
    progress_percent: float
    created_at: Optional[datetime]
    completed_at: Optional[datetime]


# === Health Schema ===

class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    platform: Optional[str]
    queue_depth: int
    timestamp: datetime


# === Config Schemas ===

class PlatformConfigResponse(BaseModel):
    """Platform configuration info."""
    platform: str
    name: str
    version: str
    is_valid: bool
    selectors_count: int
    has_mapping: bool
    has_discovery: bool


class ConfigListResponse(BaseModel):
    """List of platform configurations."""
    platforms: List[PlatformConfigResponse]
    total: int


# === Webhook Schemas ===

class WebhookTestRequest(BaseModel):
    """Request to test webhook."""
    url: str = Field(..., description="Webhook URL to test")
    secret: Optional[str] = Field(default=None, description="HMAC secret")


class WebhookTestResponse(BaseModel):
    """Webhook test result."""
    success: bool
    status_code: Optional[int]
    response_body: Optional[str]
    error: Optional[str]


# === Metrics Schemas ===

class MetricsResponse(BaseModel):
    """System metrics response."""
    cpu_percent: float
    memory_percent: float
    memory_mb: float
    uptime_seconds: int
    uptime_human: str
    tasks_per_minute: float
    tasks_per_hour: float
    success_rate_1h: float
    success_rate_24h: float
    mode: str
    timestamp: datetime


# === Logs Schemas ===

class LogEntry(BaseModel):
    """Single log entry."""
    id: int
    timestamp: datetime
    level: str
    message: str
    logger: Optional[str]
    context: Optional[Dict[str, Any]]


class LogListResponse(BaseModel):
    """Log list response."""
    entries: List[LogEntry]
    total: int
    page: int
    page_size: int
    total_pages: int


# === Mode Schemas ===

class ModeResponse(BaseModel):
    """Worker mode response."""
    mode: str
    mode_description: str
    broker_url: Optional[str]
    broker_connected: bool
    flower_url: Optional[str]
    flower_available: bool
    worker_count: Optional[int]
    worker_names: Optional[List[str]]


# === Restart Schemas ===

class RestartRequest(BaseModel):
    """Restart request body."""
    reason: Optional[str] = None
    delay_seconds: int = Field(default=5, ge=0, le=60)


class RestartResponse(BaseModel):
    """Restart response."""
    status: str
    reason: Optional[str]
    delay_seconds: int
    timestamp: datetime


# === Task Retry Schemas ===

class TaskRetryRequest(BaseModel):
    """Task retry request body."""
    priority: Optional[int] = None


class TaskRetryResponse(BaseModel):
    """Task retry response."""
    task_id: str
    status: str
    retry_count: int
    message: str


class BulkRetryResponse(BaseModel):
    """Bulk retry response."""
    retried_count: int
    filters: Dict[str, Any]
    message: str


# === Enhanced Health Schema ===

class QueueDetails(BaseModel):
    """Queue breakdown."""
    pending: int
    processing: int
    failed: int


class LpmStatus(BaseModel):
    """LPM storage status."""
    db_size_mb: float
    pending_files: int
    raw_files: int


class HealthResponseEnhanced(BaseModel):
    """Enhanced health check response."""
    status: str
    platform: Optional[str]
    queue_depth: int
    queue_details: QueueDetails
    lpm_status: LpmStatus
    timestamp: datetime
