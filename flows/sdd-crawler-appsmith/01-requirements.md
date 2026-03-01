# Requirements: Crawler Management (Flower + API)

> Version: 2.0
> Status: DRAFT
> Last Updated: 2026-03-01

---

## Decision: Flower Replaces AppSmith

After analysis, **AppSmith is overkill** for single-instance crawler management:
- AppSmith requires 2GB RAM, separate container
- Flower already provides: task monitoring, retry, revoke, worker stats
- Remaining needs are minimal: config, logs, restart

**New Approach:** Flower + minimal FastAPI endpoints

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                       CRAWLER INSTANCE                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────────────┐ │
│  │   Celery    │    │   Celery    │    │      Flower         │ │
│  │    Beat     │───>│   Workers   │    │   (:5555)           │ │
│  │ (Scheduler) │    │ (Scrapers)  │    │   Task Monitoring   │ │
│  └─────────────┘    └──────┬──────┘    │   Retry/Revoke      │ │
│                            │           │   Worker Status     │ │
│                            │           │   Prometheus /metrics│ │
│                            │           └─────────────────────┘ │
│         ┌──────────────────┴──────────────────┐                 │
│         ▼                                     ▼                 │
│  ┌─────────────┐                       ┌─────────────┐         │
│  │    Redis    │                       │ Crawler API │         │
│  │   Broker    │                       │   (:8000)   │         │
│  └─────────────┘                       └─────────────┘         │
│                                               │                 │
│         Flower Covers:                        │                 │
│         - Task list + details                 │                 │
│         - Retry/revoke tasks                  │                 │
│         - Worker status/health                │                 │
│         - Prometheus metrics                  │                 │
│                                               │                 │
│         API Provides:                         │                 │
│         - GET /config                         │                 │
│         - PUT /config                         │                 │
│         - GET /logs                           │                 │
│         - POST /restart                       │                 │
│         - GET /health (enhanced)              │                 │
│                                               │                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## What Flower Provides (No New Code Needed)

| Feature | Flower Capability |
|---------|-------------------|
| **Task Monitoring** | Real-time task list, status, progress |
| **Task Details** | Args, result, runtime, errors |
| **Retry/Revoke** | One-click retry, cancel tasks |
| **Worker Status** | Online/offline, current task, pool size |
| **Worker Stats** | Tasks completed, uptime, concurrency |
| **Prometheus** | `/metrics` endpoint for Grafana |
| **Task History** | Recent completed/failed tasks |
| **Filtering** | Filter by status, task name, worker |

Access: `http://crawler:5555`

---

## What API Needs to Provide (Minimal)

### 1. Configuration Management

**GET /config**
```json
{
  "platform": "beacon",
  "rate_limit": "5/m",
  "retry_count": 3,
  "timeout_seconds": 30,
  "proxy": null
}
```

**PUT /config**
```json
{
  "rate_limit": "10/m"
}
```
Returns: `{"status": "updated", "restart_required": false}`

---

### 2. Log Viewing

**GET /logs?level=ERROR&limit=100&since=2026-03-01T00:00:00Z**
```json
{
  "entries": [
    {
      "timestamp": "2026-03-01T12:34:56Z",
      "level": "ERROR",
      "message": "Connection timeout",
      "task_id": "abc123",
      "context": {"url": "..."}
    }
  ],
  "total": 150,
  "page": 1
}
```

Implementation: Query SQLite `logs` table or parse log file.

---

### 3. Restart Capability

**POST /restart**
```json
{
  "graceful": true
}
```
Returns: `{"status": "restarting", "message": "Will restart after current tasks complete"}`

Implementation: Send SIGTERM to Celery workers, Beat will reschedule.

---

### 4. Enhanced Health

**GET /health** (already exists, enhance)
```json
{
  "status": "healthy",
  "mode": "celery",
  "uptime_seconds": 3600,
  "redis_connected": true,
  "flower_url": "http://localhost:5555",
  "queue": {
    "pending": 42,
    "active": 3,
    "completed_1h": 150,
    "failed_1h": 2
  },
  "lpm": {
    "pending_files": 5,
    "raw_storage_mb": 1024
  }
}
```

---

## User Stories (Simplified)

**US-1: Monitor Tasks**
> **Covered by Flower** - Open Flower dashboard to see all tasks

**US-2: Retry Failed Tasks**
> **Covered by Flower** - Click retry in Flower UI

**US-3: View Logs**
> Use `GET /logs` endpoint (simple HTML page or curl)

**US-4: Update Config**
> Use `PUT /config` endpoint (curl or simple HTML form)

**US-5: Restart Crawler**
> Use `POST /restart` endpoint

---

## Implementation Tasks

### Phase 1: API Endpoints (4 tasks)

| Task | Description | Complexity |
|------|-------------|------------|
| 1.1 | Add `GET /logs` endpoint with SQLite backend | Medium |
| 1.2 | Add `POST /restart` endpoint (graceful shutdown) | Low |
| 1.3 | Enhance `GET /health` with queue stats | Low |
| 1.4 | Add Flower URL to health response | Low |

### Phase 2: Log Infrastructure (2 tasks)

| Task | Description | Complexity |
|------|-------------|------------|
| 2.1 | Add SQLite `logs` table to LPM | Low |
| 2.2 | Add SQLiteHandler to Python logging | Medium |

### Phase 3: Docker Integration (2 tasks)

| Task | Description | Complexity |
|------|-------------|------------|
| 3.1 | Add Flower to docker-compose.yml | Low |
| 3.2 | Configure Flower with Basic Auth | Low |

**Total: 8 tasks** (vs 21 tasks in AppSmith approach)

---

## File Changes

| File | Action | Purpose |
|------|--------|---------|
| `crawler/api/routes/logs.py` | Create | Log endpoint |
| `crawler/api/routes/system.py` | Create | Restart endpoint |
| `crawler/api/routes/health.py` | Modify | Enhance with queue stats |
| `crawler/db/schema.py` | Modify | Add logs table |
| `crawler/logging_handler.py` | Create | SQLite log handler |
| `docker-compose.yml` | Modify | Add Flower service |

**Total: 6 files** (vs 19 files in AppSmith approach)

---

## Comparison: AppSmith vs Flower

| Aspect | AppSmith (Old Plan) | Flower (New Plan) |
|--------|---------------------|-------------------|
| **RAM** | 2GB+ | ~100MB |
| **Containers** | crawler + appsmith | crawler + flower (included) |
| **Setup** | Import JSON app | Zero setup |
| **Task Monitoring** | Build custom | Built-in |
| **Retry/Revoke** | Build custom | Built-in |
| **Implementation** | 21 tasks, 19 files | 8 tasks, 6 files |
| **Maintenance** | Custom UI code | Flower updates |

**Winner:** Flower - 60% less work, better features

---

## Access Points

| Service | Port | Purpose |
|---------|------|---------|
| Crawler API | 8000 | Task submission, config, logs, health |
| Flower | 5555 | Task monitoring, retry, worker stats |
| Redis | 6379 | Task broker (internal) |

---

## Not In Scope

- Custom dashboard UI (use Flower)
- Real-time WebSocket updates (Flower has this)
- Multi-crawler view (that's taxlien-parser's job)
- Authentication beyond Basic Auth (Flower supports OAuth if needed)

---

## Approval

- [ ] Reviewed by: [name]
- [ ] Approved on: [date]
- [ ] Notes: [any conditions or clarifications]
