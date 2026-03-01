# Implementation Plan: Crawler AppSmith UI

> Version: 1.0
> Status: DRAFT
> Last Updated: 2026-03-01
> Specifications: [02-specifications.md](02-specifications.md)

---

## Summary

Implement AppSmith-based management UI for Universal Crawler with:
1. Backend API endpoints (metrics, logs, mode, restart, retry)
2. Database schema for logs
3. AppSmith application (5 pages)
4. Docker compose integration

**Key Decisions:**
- AppSmith as sidecar container (:3000)
- Logs in SQLite with file backup
- psutil for system metrics
- Mode-aware UI (Async vs Celery)

---

## Task Breakdown

### Phase 1: Backend API - Core Endpoints (6 tasks)

#### Task 1.1: Add psutil dependency
- **Description**: Add psutil to requirements for system metrics
- **Files**:
  - `pyproject.toml` — Add `psutil = "^5.9.0"`
  - `requirements.txt` — Add `psutil>=5.9.0` (if used)
- **Dependencies**: None
- **Verification**: `pip install -e .` succeeds
- **Complexity**: Low

#### Task 1.2: Add metrics endpoint
- **Description**: Implement GET /metrics for CPU, memory, throughput
- **Files**:
  - **CREATE** `crawler/api/routes/metrics.py` — MetricsResponse endpoint
  - `crawler/api/schemas.py` — Add MetricsResponse schema
  - `crawler/api/main.py` — Register router
- **Dependencies**: Task 1.1
- **Verification**: `curl /metrics` returns JSON with cpu_percent, memory_percent
- **Complexity**: Medium

#### Task 1.3: Add mode endpoint
- **Description**: Implement GET /mode for worker mode and Flower status
- **Files**:
  - **CREATE** `crawler/api/routes/system.py` — ModeResponse endpoint
  - `crawler/api/schemas.py` — Add ModeResponse schema
  - `crawler/api/main.py` — Register router
- **Dependencies**: None
- **Verification**: `curl /mode` returns mode, flower_url, broker_connected
- **Complexity**: Low

#### Task 1.4: Add restart endpoint
- **Description**: Implement POST /restart for graceful restart
- **Files**:
  - `crawler/api/routes/system.py` — Add restart endpoint
  - `crawler/api/schemas.py` — Add RestartRequest/Response schemas
- **Dependencies**: Task 1.3
- **Verification**: `curl -X POST /restart` triggers graceful shutdown
- **Complexity**: Medium

#### Task 1.5: Add task retry endpoint
- **Description**: Implement POST /tasks/{id}/retry
- **Files**:
  - `crawler/api/routes/tasks.py` — Add retry endpoint
  - `crawler/api/schemas.py` — Add TaskRetryRequest/Response schemas
  - `crawler/repositories/task_repo.py` — Add retry_task method
- **Dependencies**: None
- **Verification**: Failed task can be retried, status changes to pending
- **Complexity**: Low

#### Task 1.6: Add bulk retry endpoint
- **Description**: Implement POST /tasks/retry-bulk
- **Files**:
  - `crawler/api/routes/tasks.py` — Add bulk retry endpoint
  - `crawler/api/schemas.py` — Add BulkRetryResponse schema
  - `crawler/repositories/task_repo.py` — Add retry_failed_tasks method
- **Dependencies**: Task 1.5
- **Verification**: `curl -X POST /tasks/retry-bulk?status=failed` retries all failed
- **Complexity**: Low

---

### Phase 2: Backend API - Logs (4 tasks)

#### Task 2.1: Add logs table schema
- **Description**: Add logs table to LPM database
- **Files**:
  - `crawler/db/schema.py` — Add logs table DDL
  - `crawler/db/migrations/` — Add migration if needed
- **Dependencies**: None
- **Verification**: Table created on crawler start
- **Complexity**: Low

#### Task 2.2: Implement log storage in LPM
- **Description**: Add methods to store and query logs
- **Files**:
  - `crawler/lpm.py` — Add add_log_entry, get_logs, cleanup_old_logs
- **Dependencies**: Task 2.1
- **Verification**: Logs can be written and queried
- **Complexity**: Medium

#### Task 2.3: Add logging handler for DB
- **Description**: Custom logging handler that writes to SQLite
- **Files**:
  - **CREATE** `crawler/logging_handler.py` — SQLiteHandler class
  - `crawler/core/logging.py` — Register handler
- **Dependencies**: Task 2.2
- **Verification**: Log messages appear in database
- **Complexity**: Medium

#### Task 2.4: Add logs endpoint
- **Description**: Implement GET /logs with filters
- **Files**:
  - **CREATE** `crawler/api/routes/logs.py` — LogListResponse endpoint
  - `crawler/api/schemas.py` — Add LogEntry, LogListResponse schemas
  - `crawler/api/main.py` — Register router
- **Dependencies**: Task 2.2
- **Verification**: `curl /logs?level=ERROR&page=1` returns filtered logs
- **Complexity**: Low

---

### Phase 3: Backend API - Enhancements (2 tasks)

#### Task 3.1: Enhance /health endpoint
- **Description**: Add queue_details and lpm_status to health response
- **Files**:
  - `crawler/api/routes/health.py` — Extend response
  - `crawler/api/schemas.py` — Add QueueDetails, LpmStatus, HealthResponseEnhanced
- **Dependencies**: None
- **Verification**: `/health` returns queue breakdown and LPM stats
- **Complexity**: Low

#### Task 3.2: Enhance /tasks endpoint
- **Description**: Add offset, sort_by, sort_order, retry_count filters
- **Files**:
  - `crawler/api/routes/tasks.py` — Add query params
  - `crawler/repositories/task_repo.py` — Update query builder
- **Dependencies**: None
- **Verification**: Tasks can be sorted and paginated properly
- **Complexity**: Low

---

### Phase 4: Docker Integration (2 tasks)

#### Task 4.1: Add AppSmith to docker-compose
- **Description**: Add AppSmith sidecar service
- **Files**:
  - `docker-compose.yml` — Add appsmith service
  - `docker-compose.celery.yml` — Add appsmith with Flower link
- **Dependencies**: Phase 1-3
- **Verification**: `docker-compose up` starts crawler + appsmith
- **Complexity**: Low

#### Task 4.2: Configure AppSmith networking
- **Description**: Ensure AppSmith can reach crawler API
- **Files**:
  - `docker-compose.yml` — Network configuration
  - `.env.example` — Add APPSMITH_PORT, CRAWLER_API_URL
- **Dependencies**: Task 4.1
- **Verification**: AppSmith queries succeed from container
- **Complexity**: Low

---

### Phase 5: AppSmith Application (5 tasks)

#### Task 5.1: Create AppSmith application
- **Description**: Initialize AppSmith app with navigation
- **Files**:
  - **CREATE** `appsmith/` — Directory for exports
  - **CREATE** `appsmith/application.json` — App definition
- **Dependencies**: Task 4.1
- **Verification**: App imports into AppSmith
- **Complexity**: Low

#### Task 5.2: Build Dashboard page
- **Description**: Task counts, health summary, recent activity
- **Files**:
  - `appsmith/application.json` — Dashboard page widgets
- **Dependencies**: Task 5.1
- **Queries**: `/tasks`, `/metrics`, `/health`
- **Verification**: Dashboard displays all metrics
- **Complexity**: Medium

#### Task 5.3: Build Tasks page
- **Description**: Task list, filters, retry, details modal
- **Files**:
  - `appsmith/application.json` — Tasks page widgets
- **Dependencies**: Task 5.1
- **Queries**: `/tasks`, `/tasks/{id}/retry`, `/tasks/retry-bulk`
- **Verification**: Tasks filterable, retry works
- **Complexity**: Medium

#### Task 5.4: Build Health page
- **Description**: CPU/memory gauges, mode display, Flower link
- **Files**:
  - `appsmith/application.json` — Health page widgets
- **Dependencies**: Task 5.1
- **Queries**: `/metrics`, `/mode`
- **Verification**: Gauges update, Flower link visible in Celery mode
- **Complexity**: Low

#### Task 5.5: Build Config page
- **Description**: JSON editor, save, restart button
- **Files**:
  - `appsmith/application.json` — Config page widgets
- **Dependencies**: Task 5.1
- **Queries**: `/config`, `/config` (PUT), `/restart`
- **Verification**: Config editable, restart works
- **Complexity**: Medium

#### Task 5.6: Build Logs page
- **Description**: Log table with filters, search, pagination
- **Files**:
  - `appsmith/application.json` — Logs page widgets
- **Dependencies**: Task 5.1
- **Queries**: `/logs`
- **Verification**: Logs filterable by level, searchable
- **Complexity**: Low

---

### Phase 6: Documentation (2 tasks)

#### Task 6.1: API documentation
- **Description**: Document new endpoints
- **Files**:
  - `crawler/docs/API.md` — Update with new endpoints
- **Dependencies**: Phase 1-3
- **Verification**: All endpoints documented
- **Complexity**: Low

#### Task 6.2: AppSmith setup guide
- **Description**: Guide for importing AppSmith app
- **Files**:
  - **CREATE** `appsmith/README.md` — Setup instructions
  - **CREATE** `appsmith/IMPORT.md` — Import guide
- **Dependencies**: Phase 5
- **Verification**: New user can follow guide
- **Complexity**: Low

---

## Dependency Graph

```
Phase 1: Core API
  1.1 ─→ 1.2 (psutil)
  1.3 ─→ 1.4 (system.py)
  1.5 ─→ 1.6 (retry)

Phase 2: Logs
  2.1 ─→ 2.2 ─→ 2.3 ─→ 2.4

Phase 3: Enhancements
  3.1 (independent)
  3.2 (independent)

Phase 4: Docker
  [Phase 1-3] ─→ 4.1 ─→ 4.2

Phase 5: AppSmith
  4.1 ─→ 5.1 ─→ 5.2, 5.3, 5.4, 5.5, 5.6 (parallel)

Phase 6: Docs
  [Phase 1-3] ─→ 6.1
  [Phase 5] ─→ 6.2
```

---

## File Change Summary

| File | Action | Phase |
|------|--------|-------|
| `pyproject.toml` | Modify | 1 |
| `crawler/api/routes/metrics.py` | Create | 1 |
| `crawler/api/routes/system.py` | Create | 1 |
| `crawler/api/routes/logs.py` | Create | 2 |
| `crawler/api/routes/tasks.py` | Modify | 1, 3 |
| `crawler/api/routes/health.py` | Modify | 3 |
| `crawler/api/schemas.py` | Modify | 1, 2, 3 |
| `crawler/api/main.py` | Modify | 1, 2 |
| `crawler/db/schema.py` | Modify | 2 |
| `crawler/lpm.py` | Modify | 2 |
| `crawler/logging_handler.py` | Create | 2 |
| `crawler/core/logging.py` | Modify | 2 |
| `crawler/repositories/task_repo.py` | Modify | 1, 3 |
| `docker-compose.yml` | Modify | 4 |
| `docker-compose.celery.yml` | Modify | 4 |
| `.env.example` | Modify | 4 |
| `appsmith/application.json` | Create | 5 |
| `appsmith/README.md` | Create | 6 |
| `crawler/docs/API.md` | Modify | 6 |

**Total:** 19 files (7 create, 12 modify)

---

## Testing Strategy

### Unit Tests
- `test_metrics_endpoint.py` — Metrics response format
- `test_logs_endpoint.py` — Log filtering and pagination
- `test_mode_endpoint.py` — Mode detection
- `test_task_retry.py` — Single and bulk retry
- `test_restart_endpoint.py` — Graceful shutdown

### Integration Tests
- `test_appsmith_queries.py` — API responses match AppSmith expectations
- `test_log_pipeline.py` — Logs written and queryable

### Manual Testing
- [ ] Dashboard displays correct counts
- [ ] Tasks page: filter, retry, view details
- [ ] Health page: gauges update, Flower link works (Celery)
- [ ] Config page: edit, save, restart
- [ ] Logs page: filter by level, search works

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| psutil platform compatibility | Low | Medium | Test on Linux/macOS |
| AppSmith import issues | Medium | Low | Provide manual setup guide |
| Log volume overwhelming SQLite | Low | Medium | Auto-cleanup, pagination limits |
| Restart endpoint abuse | Low | High | Rate limit (1/min) |

---

## Rollback Strategy

If implementation fails:
1. Remove new API routes
2. Remove logs table migration
3. Revert docker-compose changes
4. Delete appsmith/ directory

---

## Checkpoints

After each phase, verify:
- [ ] All endpoints return correct response format
- [ ] No regressions in existing functionality
- [ ] AppSmith queries succeed

---

## Approval

- [ ] Plan reviewed by user
- [ ] All tasks clear and actionable
- [ ] Dependencies make sense
- [ ] **User explicitly approves: "plan approved"**

---

## Next Phase

After plan approval, move to **IMPLEMENTATION** phase:
- Execute tasks in order
- Log progress in `04-implementation-log.md`
- Test after each task
