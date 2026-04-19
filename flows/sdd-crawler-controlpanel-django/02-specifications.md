# Specifications: Crawler AppSmith UI

> Version: 1.0
> Status: APPROVED
> Last Updated: 2026-03-01

---

## 1. Overview

This specification defines the AppSmith UI integration for the Universal Crawler. The UI provides a management interface for monitoring tasks, viewing health metrics, managing configuration, and debugging failures.

**Key Design Principles:**
- **Mode-Aware**: Adapts to Async or Celery worker mode
- **API-First**: All data from crawler's FastAPI endpoints
- **Single-Instance**: Manages ONE crawler instance
- **Complementary to Flower**: Flower for Celery monitoring, AppSmith for management

---

## 2. Affected Systems

### 2.1 Crawler API (Backend)

| Component | Change |
|-----------|--------|
| `crawler/api/routes/health.py` | Extend `/health` with detailed metrics |
| `crawler/api/routes/tasks.py` | Add retry endpoint, enhance filtering |
| `crawler/api/routes/config.py` | Add restart endpoint |
| `crawler/api/schemas.py` | Add new response schemas |
| **NEW**: `crawler/api/routes/metrics.py` | CPU, memory, throughput metrics |
| **NEW**: `crawler/api/routes/logs.py` | Log querying with filters |
| **NEW**: `crawler/api/routes/system.py` | Mode detection, restart control |

### 2.2 Local Persistence Manager (LPM)

| Component | Change |
|-----------|--------|
| `crawler/lpm.py` | Add log storage methods |
| `crawler/db/schema.py` | Add `logs` table |
| `crawler/repositories/task_repo.py` | Add bulk retry method |

### 2.3 AppSmith (Frontend)

| Widget/Purpose | Data Source |
|----------------|-------------|
| **Dashboard Page** | `/health`, `/tasks`, `/metrics` |
| **Tasks Page** | `/tasks`, `/tasks/{id}`, `/tasks/{id}/retry` |
| **Health Page** | `/metrics`, `/mode` |
| **Config Page** | `/config`, `/config` (PUT), `/restart` |
| **Logs Page** | `/logs` |

### 2.4 Docker Compose

| Component | Change |
|-----------|--------|
| `docker-compose.yml` | Add AppSmith sidecar service |
| `docker-compose.celery.yml` | Add Flower link in AppSmith config |

---

## 3. API Specifications

### 3.1 New Endpoints

#### GET `/metrics` — Detailed System Metrics

**Purpose:** Provide CPU, memory, and throughput metrics for Health page.

**Response Schema:**
```json
{
  "cpu_percent": 45.2,
  "memory_percent": 62.1,
  "memory_mb": 512,
  "uptime_seconds": 3600,
  "uptime_human": "1h 0m",
  "tasks_per_minute": 12.5,
  "tasks_per_hour": 750,
  "success_rate_1h": 0.95,
  "success_rate_24h": 0.93,
  "mode": "async",
  "timestamp": "2026-03-01T12:00:00Z"
}
```

**Implementation Notes:**
- CPU/memory from `psutil` library
- Uptime from process start time
- Tasks/minute from LPM task completion timestamps
- Success rate from task status history

---

#### GET `/logs` — Log Entries with Filters

**Purpose:** Provide searchable, filterable log entries for Logs page.

**Query Parameters:**
- `level` (optional): Filter by log level (INFO, WARN, ERROR, DEBUG)
- `search` (optional): Full-text search in message
- `page` (optional): Page number (default: 1)
- `page_size` (optional): Items per page (default: 50, max: 200)
- `since` (optional): ISO timestamp for time-based filtering

**Response Schema:**
```json
{
  "entries": [
    {
      "id": 12345,
      "timestamp": "2026-03-01T12:00:00Z",
      "level": "ERROR",
      "message": "Task failed: connection timeout",
      "logger": "crawler.worker",
      "context": {
        "task_id": "abc-123",
        "url": "https://example.com/parcel/456"
      }
    }
  ],
  "total": 1250,
  "page": 1,
  "page_size": 50,
  "total_pages": 25
}
```

**Implementation Notes:**
- Logs stored in SQLite `logs` table for fast querying
- Raw log file at `/data/logs/crawler.log` for full context
- Auto-cleanup: logs older than 7 days

---

#### GET `/mode` — Worker Mode and Broker Status

**Purpose:** Detect worker mode (async/celery) and provide Flower link.

**Response Schema:**
```json
{
  "mode": "celery",
  "mode_description": "Celery distributed workers",
  "broker_url": "redis://localhost:6379/0",
  "broker_connected": true,
  "flower_url": "http://localhost:5555",
  "flower_available": true,
  "worker_count": 4,
  "worker_names": ["worker1@host", "worker2@host"]
}
```

**Implementation Notes:**
- Mode from `MODE` environment variable
- Flower URL from `FLOWER_URL` environment variable
- Worker count from Celery inspect API (if Celery mode)

---

#### POST `/restart` — Restart Crawler

**Purpose:** Trigger graceful crawler restart after config changes.

**Request Body:** (optional)
```json
{
  "reason": "Config change: rate_limit updated",
  "delay_seconds": 5
}
```

**Response Schema:**
```json
{
  "status": "restarting",
  "reason": "Config change: rate_limit updated",
  "delay_seconds": 5,
  "timestamp": "2026-03-01T12:00:00Z"
}
```

**Implementation Notes:**
- Graceful shutdown: complete current task, then exit
- Docker restart policy will restart container
- Log warning before restart
- Requires container to have restart policy (`unless-stopped`)

---

#### POST `/tasks/{id}/retry` — Retry Failed Task

**Purpose:** Re-queue a failed task for processing.

**Path Parameters:**
- `id`: Task ID

**Request Body:** (optional)
```json
{
  "priority": 10
}
```

**Response Schema:**
```json
{
  "task_id": "abc-123",
  "status": "pending",
  "retry_count": 1,
  "message": "Task re-queued successfully"
}
```

**Implementation Notes:**
- Reset task status to `pending`
- Increment `retry_count`
- Clear `error` field
- Optionally update priority

---

#### POST `/tasks/retry-bulk` — Bulk Retry Failed Tasks

**Purpose:** Retry all failed tasks or tasks matching filters.

**Query Parameters:**
- `status`: Must be `failed`
- `platform`: Optional filter
- `limit`: Max tasks to retry (default: 100)

**Response Schema:**
```json
{
  "retried_count": 15,
  "filters": {
    "status": "failed",
    "platform": null,
    "limit": 100
  },
  "message": "15 tasks re-queued successfully"
}
```

---

### 3.2 Enhanced Existing Endpoints

#### GET `/health` — Enhanced with Extended Metrics

**Current Response:**
```json
{
  "status": "healthy",
  "platform": "beacon",
  "queue_depth": 42,
  "timestamp": "2026-03-01T12:00:00Z"
}
```

**Enhanced Response:**
```json
{
  "status": "healthy",
  "platform": "beacon",
  "queue_depth": 42,
  "queue_details": {
    "pending": 30,
    "processing": 10,
    "failed": 2
  },
  "lpm_status": {
    "db_size_mb": 128,
    "pending_files": 5,
    "raw_files": 150
  },
  "timestamp": "2026-03-01T12:00:00Z"
}
```

---

#### GET `/tasks` — Enhanced Filtering

**New Query Parameters:**
- `status`: Filter by status (existing)
- `platform`: Filter by platform (existing)
- `limit`: Max results (existing)
- **NEW** `offset`: Pagination offset
- **NEW** `sort_by`: Sort field (`created_at`, `completed_at`, `priority`)
- **NEW** `sort_order`: `asc` or `desc`
- **NEW** `retry_count`: Filter by retry count (e.g., `>0`)

---

### 3.3 New Schema Definitions

**Add to `crawler/api/schemas.py`:**

```python
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
    logger: str
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
```

---

## 4. Database Schema Changes

### 4.1 New Table: `logs`

```sql
CREATE TABLE IF NOT EXISTS logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    level TEXT NOT NULL,
    message TEXT NOT NULL,
    logger TEXT,
    context_json TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for fast filtering
CREATE INDEX idx_logs_level ON logs(level);
CREATE INDEX idx_logs_timestamp ON logs(timestamp);
CREATE INDEX idx_logs_logger ON logs(logger);
```

### 4.2 LPM Methods

**Add to `crawler/lpm.py`:**

```python
async def add_log_entry(
    self,
    level: str,
    message: str,
    logger: str = None,
    context: dict = None,
):
    """Add a log entry to the database."""
    # Implementation: INSERT into logs table


async def get_logs(
    self,
    level: str = None,
    search: str = None,
    page: int = 1,
    page_size: int = 50,
    since: datetime = None,
) -> dict:
    """Get paginated log entries with filters."""
    # Implementation: SELECT with filters, COUNT for pagination


async def cleanup_old_logs(self, days: int = 7):
    """Delete logs older than N days."""
    # Implementation: DELETE where timestamp < now - days
```

---

## 5. AppSmith Widget Structure

### 5.1 Dashboard Page

| Widget | Type | Data Source | Properties |
|--------|------|-------------|------------|
| `txt_pending` | Text | `{{tasks.pending}}` | Format: number |
| `txt_completed` | Text | `{{tasks.completed}}` | Format: number |
| `txt_failed` | Text | `{{tasks.failed}}` | Format: number |
| `gauge_cpu` | Progress | `{{metrics.cpu_percent}}` | Max: 100 |
| `gauge_memory` | Progress | `{{metrics.memory_percent}}` | Max: 100 |
| `txt_uptime` | Text | `{{metrics.uptime_human}}` | - |
| `table_recent` | Table | `{{tasks_recent.data}}` | Columns: id, url, status, completed_at |
| `chart_throughput` | Line | `{{metrics_history.data}}` | X: timestamp, Y: tasks_per_minute |

**API Queries:**
- `tasks`: `GET /tasks?limit=100`
- `metrics`: `GET /metrics`
- `tasks_recent`: `GET /tasks?status=completed&limit=10`

---

### 5.2 Tasks Page

| Widget | Type | Data Source | Properties |
|--------|------|-------------|------------|
| `table_tasks` | Table | `{{tasks_list.data}}` | Paginated, sortable |
| `dropdown_status` | Select | Static: [All, pending, processing, completed, failed] | Filter |
| `input_search` | Input | - | Search by URL/ID |
| `btn_retry` | Button | - | Visible when `selectedRow.status === 'failed'` |
| `btn_retry_all` | Button | - | Retry all failed |
| `modal_details` | Modal | - | Shows `{{table_tasks.selectedRow}}` |

**API Queries:**
- `tasks_list`: `GET /tasks?status={{dropdown_status.value}}&limit={{table_tasks.pageSize}}&offset={{(table_tasks.page - 1) * table_tasks.pageSize}}`
- `task_retry`: `POST /tasks/{{table_tasks.selectedRow.id}}/retry`
- `tasks_retry_bulk`: `POST /tasks/retry-bulk?status=failed`

---

### 5.3 Health Page

| Widget | Type | Data Source | Properties |
|--------|------|-------------|------------|
| `gauge_cpu` | Progress | `{{metrics.cpu_percent}}` | Color thresholds |
| `gauge_memory` | Progress | `{{metrics.memory_percent}}` | Color thresholds |
| `chart_cpu_history` | Line | `{{metrics_history.data}}` | Time series |
| `chart_memory_history` | Line | `{{metrics_history.data}}` | Time series |
| `txt_mode` | Text | `{{mode.mode}}` | - |
| `link_flower` | Link | `{{mode.flower_url}}` | Visible if `mode.flower_available` |
| `txt_broker` | Text | `{{mode.broker_connected}}` | Show connection status |

**API Queries:**
- `metrics`: `GET /metrics`
- `mode`: `GET /mode`
- `metrics_history`: Stored query (local history)

---

### 5.4 Config Page

| Widget | Type | Data Source | Properties |
|--------|------|-------------|------------|
| `json_editor` | JSON Editor | `{{config.data.config}}` | Validation |
| `txt_config_path` | Text | `{{config.data.path}}` | Read-only |
| `btn_save` | Button | - | `PUT /config` |
| `btn_restart` | Button | - | `POST /restart`, visible after save |
| `alert_restart` | Alert | - | Warning: requires restart |

**API Queries:**
- `config`: `GET /config`
- `config_save`: `PUT /config`
- `restart`: `POST /restart`

---

### 5.5 Logs Page

| Widget | Type | Data Source | Properties |
|--------|------|-------------|------------|
| `table_logs` | Table | `{{logs.data.entries}}` | Paginated |
| `dropdown_level` | Select | Static: [ALL, INFO, WARN, ERROR] | Filter |
| `input_search` | Input | - | Full-text search |
| `btn_refresh` | Button | - | Refresh logs |
| `txt_log_count` | Text | `{{logs.data.total}}` | Total count |

**API Queries:**
- `logs`: `GET /logs?level={{dropdown_level.value}}&search={{input_search.text}}&page={{table_logs.page}}&page_size={{table_logs.pageSize}}`

---

## 6. Data Models and Interfaces

### 6.1 Task Model (Existing)

```python
class Task(BaseModel):
    id: str
    url: str
    platform: str
    status: TaskStatusEnum
    priority: int
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    result_path: Optional[str]
    error: Optional[str]
    retry_count: int
```

### 6.2 Log Entry Model (New)

```python
class LogEntry(BaseModel):
    id: int
    timestamp: datetime
    level: str  # DEBUG, INFO, WARN, ERROR, CRITICAL
    message: str
    logger: Optional[str]  # e.g., "crawler.worker"
    context: Optional[Dict[str, Any]]  # task_id, url, etc.
```

### 6.3 Metrics Model (New)

```python
class SystemMetrics(BaseModel):
    cpu_percent: float
    memory_percent: float
    memory_mb: float
    uptime_seconds: int
    uptime_human: str
    tasks_per_minute: float
    tasks_per_hour: float
    success_rate_1h: float
    success_rate_24h: float
    mode: str  # async, celery
    timestamp: datetime
```

---

## 7. Edge Cases and Error Handling

### 7.1 API Unavailable

**Scenario:** AppSmith cannot reach crawler API.

**Handling:**
- Show error banner: "Cannot connect to crawler API"
- Retry automatically every 30 seconds
- Last known data displayed with stale indicator

---

### 7.2 Task Retry Failure

**Scenario:** Retry endpoint returns error.

**Handling:**
- Show toast: "Failed to retry task: {error}"
- Log error to console
- Keep task in failed state

---

### 7.3 Config Validation Error

**Scenario:** Invalid JSON in config editor.

**Handling:**
- Disable Save button
- Show validation error inline
- Highlight invalid JSON region

---

### 7.4 Restart Timeout

**Scenario:** Crawler doesn't restart within expected time.

**Handling:**
- Show warning: "Restart in progress... (taking longer than expected)"
- Poll `/health` every 5 seconds
- Auto-refresh page when crawler back online

---

### 7.5 Celery Mode without Flower

**Scenario:** `mode.flower_available` is false.

**Handling:**
- Hide Flower link
- Show message: "Flower monitoring not configured"
- Display basic metrics from `/metrics` endpoint

---

### 7.6 Large Log Volume

**Scenario:** Logs table has >100,000 entries.

**Handling:**
- Enforce max `page_size` of 200
- Show message: "Showing latest {page_size} entries. Use search to find specific logs"
- Suggest log cleanup if total > threshold

---

### 7.7 Concurrent Config Edits

**Scenario:** Two users edit config simultaneously.

**Handling:**
- Optimistic locking: include `version` or `updated_at` in config
- On save conflict: show "Config was modified by another user. Reload and merge changes?"
- Provide diff view

---

## 8. Dependencies and Integration Points

### 8.1 External Dependencies

| Dependency | Version | Purpose |
|------------|---------|---------|
| `psutil` | ^5.9.0 | System metrics (CPU, memory) |
| AppSmith | Latest (Docker) | UI framework |

### 8.2 Integration Points

| System | Integration | Purpose |
|--------|-------------|---------|
| **Flower** | Link from Health page | Celery task monitoring |
| **Docker** | Restart endpoint | Container lifecycle |
| **Redis** | Via `/mode` endpoint | Broker status (Celery mode) |

---

## 9. Security Considerations

### 9.1 Authentication

- **Current**: Single-user assumed (no auth)
- **Future**: Add Basic Auth or JWT if multi-user needed

### 9.2 Authorization

- **Current**: All operations allowed
- **Future**: Role-based access (read-only vs admin)

### 9.3 Sensitive Data

- Config may contain secrets (webhook URLs, API keys)
- **Mitigation**: Mask sensitive fields in UI, use environment variables

---

## 10. Performance Considerations

### 10.1 API Rate Limits

| Endpoint | Max Rate | Reason |
|----------|----------|--------|
| `/metrics` | 1 req/sec | CPU overhead |
| `/logs` | 10 req/sec | Database queries |
| `/tasks` | 10 req/sec | Database queries |
| `/restart` | 1 req/min | Prevent abuse |

### 10.2 AppSmith Query Optimization

- Cache `/metrics` for 5 seconds
- Paginate logs (50 per page max)
- Use incremental refresh for task list

---

## Approval

- [ ] Specifications reviewed by user
- [ ] All affected systems identified
- [ ] Edge cases documented
- [ ] **User explicitly approves: "specs approved"**

---

## Next Phase

After specifications approval, move to **PLAN** phase to define:
- Task breakdown
- File changes (create/modify/delete)
- Testing strategy
- Estimated complexity
