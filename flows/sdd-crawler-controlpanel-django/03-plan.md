# Plan: Crawler AppSmith UI

> Version: 1.0
> Status: DRAFT
> Last Updated: 2026-03-01

---

## 1. Overview

This plan breaks down the implementation of the AppSmith UI for the Universal Crawler into atomic, testable tasks.

**Implementation Strategy:**
1. Backend API first (schemas, routes, database)
2. Docker Compose configuration
3. AppSmith UI pages
4. Integration testing

---

## 2. Task Breakdown

### Phase 1: Backend API

#### Task 1.1: Add API Schemas
**File:** `crawler/api/schemas.py`
**Type:** MODIFY
**Complexity:** Low
**Dependencies:** None

**Changes:**
- Add `MetricsResponse` schema
- Add `LogEntry` and `LogListResponse` schemas
- Add `ModeResponse` schema
- Add `RestartRequest` and `RestartResponse` schemas
- Add `TaskRetryRequest`, `TaskRetryResponse`, `BulkRetryResponse` schemas
- Add `QueueDetails`, `LpmStatus`, `HealthResponseEnhanced` schemas

**Test:**
- Import schemas without errors
- Validate sample data against each schema

---

#### Task 1.2: Create Metrics Route
**File:** `crawler/api/routes/metrics.py`
**Type:** CREATE
**Complexity:** Medium
**Dependencies:** Task 1.1, `psutil` library

**Changes:**
- Create `GET /metrics` endpoint
- Collect CPU, memory from `psutil`
- Calculate uptime from process start
- Calculate tasks/minute from LPM history
- Calculate success rates from task status

**Test:**
- `GET /metrics` returns valid JSON
- All fields present and correct types
- CPU/memory values in valid range (0-100)

---

#### Task 1.3: Create Logs Route
**File:** `crawler/api/routes/logs.py`
**Type:** CREATE
**Complexity:** Medium
**Dependencies:** Task 1.1, Task 2.1 (logs table)

**Changes:**
- Create `GET /logs` endpoint with filters
- Support `level`, `search`, `page`, `page_size`, `since` parameters
- Return paginated response with total count
- Add logging middleware to capture logs to SQLite

**Test:**
- `GET /logs` returns entries
- Filter by level works
- Search by text works
- Pagination works correctly

---

#### Task 1.4: Create System Route
**File:** `crawler/api/routes/system.py`
**Type:** CREATE
**Complexity:** Low
**Dependencies:** Task 1.1

**Changes:**
- Create `GET /mode` endpoint
- Detect worker mode from env var
- Check Flower availability
- Get Celery worker info (if Celery mode)
- Create `POST /restart` endpoint
- Graceful shutdown with delay

**Test:**
- `GET /mode` returns correct mode
- Flower URL configured correctly
- `POST /restart` triggers shutdown

---

#### Task 1.5: Enhance Health Route
**File:** `crawler/api/routes/health.py`
**Type:** MODIFY
**Complexity:** Low
**Dependencies:** Task 1.1

**Changes:**
- Add queue details (pending, processing, failed counts)
- Add LPM status (db_size_mb, pending_files, raw_files)
- Return enhanced response (backward compatible)

**Test:**
- `/health` returns enhanced fields
- Queue counts are accurate
- LPM status fields present

---

#### Task 1.6: Enhance Tasks Route
**File:** `crawler/api/routes/tasks.py`
**Type:** MODIFY
**Complexity:** Medium
**Dependencies:** Task 1.1

**Changes:**
- Add `POST /tasks/{id}/retry` endpoint
- Add `POST /tasks/retry-bulk` endpoint
- Add pagination params (`offset`, `sort_by`, `sort_order`)
- Add `retry_count` filter

**Test:**
- Retry single task works
- Bulk retry works
- Pagination works
- Sorting works

---

### Phase 2: Database and LPM

#### Task 2.1: Add Logs Table Schema
**File:** `crawler/db/schema.py`
**Type:** MODIFY
**Complexity:** Low
**Dependencies:** None

**Changes:**
- Add `CREATE TABLE logs` statement
- Add indexes for level, timestamp, logger
- Add migration logic (if table exists, skip)

**Test:**
- Table created on first run
- Indexes exist
- Migration is idempotent

---

#### Task 2.2: Add LPM Log Methods
**File:** `crawler/lpm.py`
**Type:** MODIFY
**Complexity:** Medium
**Dependencies:** Task 2.1

**Changes:**
- Add `add_log_entry()` method
- Add `get_logs()` method with filters
- Add `cleanup_old_logs()` method
- Integrate logging middleware with LPM

**Test:**
- Log entries are saved
- Filtering works correctly
- Old logs are cleaned up

---

### Phase 3: Docker Compose

#### Task 3.1: Add AppSmith Service
**File:** `docker-compose.yml`
**Type:** MODIFY
**Complexity:** Low
**Dependencies:** None

**Changes:**
- Add `appsmith` service
- Configure volume for persistence
- Set environment variables
- Expose port 3000
- Add dependency on `crawler` service

**Test:**
- `docker-compose up` starts AppSmith
- AppSmith accessible at `http://localhost:3000`
- AppSmith can reach crawler API

---

### Phase 4: AppSmith UI

#### Task 4.1: Create Dashboard Page
**Type:** CREATE (AppSmith)
**Complexity:** Medium
**Dependencies:** Task 1.2, 1.5, 1.6

**Widgets:**
- Task count cards (pending, completed, failed)
- Health summary (CPU, memory, uptime)
- Recent activity table

**API Queries:**
- `GET /tasks` for counts
- `GET /metrics` for health
- `GET /tasks?status=completed&limit=10` for recent

**Test:**
- Dashboard loads without errors
- Counts match API data
- Auto-refresh works (30s interval)

---

#### Task 4.2: Create Tasks Page
**Type:** CREATE (AppSmith)
**Complexity:** High
**Dependencies:** Task 1.6

**Widgets:**
- Paginated task table
- Status filter dropdown
- Search input
- Retry button (single)
- Retry all button (bulk)
- Details modal

**API Queries:**
- `GET /tasks` with filters
- `POST /tasks/{id}/retry`
- `POST /tasks/retry-bulk`

**Test:**
- Table displays tasks correctly
- Filters work
- Retry single task works
- Bulk retry works
- Details modal shows correct data

---

#### Task 4.3: Create Health Page
**Type:** CREATE (AppSmith)
**Complexity:** Medium
**Dependencies:** Task 1.2, 1.4

**Widgets:**
- CPU gauge
- Memory gauge
- Throughput charts
- Mode indicator
- Flower link (conditional)

**API Queries:**
- `GET /metrics`
- `GET /mode`

**Test:**
- Gauges show correct values
- Charts render correctly
- Flower link visible in Celery mode
- Flower link hidden in Async mode

---

#### Task 4.4: Create Config Page
**Type:** CREATE (AppSmith)
**Complexity:** Medium
**Dependencies:** Existing `/config` endpoints

**Widgets:**
- JSON editor
- Save button
- Restart button
- Validation alerts

**API Queries:**
- `GET /config`
- `PUT /config`
- `POST /restart`

**Test:**
- Config loads correctly
- JSON validation works
- Save updates config
- Restart button visible after save
- Restart triggers container restart

---

#### Task 4.5: Create Logs Page
**Type:** CREATE (AppSmith)
**Complexity:** Medium
**Dependencies:** Task 1.3

**Widgets:**
- Paginated log table
- Level filter dropdown
- Search input
- Refresh button

**API Queries:**
- `GET /logs` with filters

**Test:**
- Logs display correctly
- Level filter works
- Search works
- Pagination works

---

### Phase 5: Integration Testing

#### Task 5.1: End-to-End Testing
**Type:** TEST
**Complexity:** Medium
**Dependencies:** All previous tasks

**Test Scenarios:**
1. Start crawler + AppSmith stack
2. Navigate to each page
3. Create a task via API
4. Verify task appears in Tasks page
5. Retry a failed task
6. Update config and restart
7. Verify logs appear in Logs page

**Test:**
- All scenarios pass
- No console errors in AppSmith
- API calls succeed

---

## 3. File Changes Summary

### Create (6 files)
| File | Purpose |
|------|---------|
| `crawler/api/routes/metrics.py` | Metrics endpoint |
| `crawler/api/routes/logs.py` | Logs endpoint |
| `crawler/api/routes/system.py` | Mode + restart endpoints |
| `flows/sdd-crawler-appsmith/03-plan.md` | This plan |
| `flows/sdd-crawler-appsmith/04-implementation-log.md` | Implementation log |
| `appsmith/` (or volume) | AppSmith application export |

### Modify (6 files)
| File | Purpose |
|------|---------|
| `crawler/api/schemas.py` | Add new schemas |
| `crawler/api/routes/health.py` | Enhance health endpoint |
| `crawler/api/routes/tasks.py` | Add retry endpoints |
| `crawler/api/app.py` | Register new routes |
| `crawler/db/schema.py` | Add logs table |
| `crawler/lpm.py` | Add log methods |
| `docker-compose.yml` | Add AppSmith service |

---

## 4. Testing Strategy

### Unit Tests (Backend)
- Test each API endpoint independently
- Test schema validation
- Test LPM log methods

### Integration Tests
- Test API with real SQLite database
- Test AppSmith queries against API
- Test Docker Compose stack

### Manual Tests
- Navigate each AppSmith page
- Verify UI components render correctly
- Test retry workflows

---

## 5. Rollback Considerations

- **API changes:** Backward compatible (new endpoints, enhanced responses)
- **Database changes:** Additive only (new table, no schema modifications)
- **AppSmith:** Can be removed without affecting crawler
- **Docker Compose:** AppSmith service is optional

---

## 6. Estimated Complexity

| Phase | Tasks | Complexity |
|-------|-------|------------|
| Backend API | 6 | Medium |
| Database/LPM | 2 | Low-Medium |
| Docker Compose | 1 | Low |
| AppSmith UI | 5 | Medium-High |
| Testing | 1 | Medium |
| **Total** | **15** | **Medium** |

**Estimated Time:** 4-6 hours (excluding AppSmith UI design iteration)

---

## Approval

- [ ] Plan reviewed by user
- [ ] Tasks are atomic and testable
- [ ] Dependencies mapped
- [ ] **User explicitly approves: "plan approved"**

---

## Next Phase

After plan approval, move to **IMPLEMENTATION** phase:
- Execute tasks one by one
- Log progress in `04-implementation-log.md`
- Run tests after each task
- Document any deviations from plan
