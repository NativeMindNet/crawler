# Requirements: Crawler AppSmith UI

> Version: 1.0
> Status: DRAFT
> Last Updated: 2026-03-01

---

## Problem Statement

Each crawler instance needs a local management interface for:
- Monitoring task queue and processing status
- Viewing health metrics (CPU, memory, success rate)
- Managing configuration
- Debugging failed tasks

The crawler is **platform-agnostic** and **self-contained**. It doesn't know about other crawlers or what platform it serves. This UI manages ONE crawler instance.

---

## User Stories

### Primary

**US-1: Monitor Task Queue**
**As a** crawler operator
**I want** to see the current task queue status
**So that** I understand what the crawler is doing

**US-2: View Health Metrics**
**As a** crawler operator
**I want** to see CPU, memory, and success rate
**So that** I can detect performance issues

**US-3: Retry Failed Tasks**
**As a** crawler operator
**I want** to retry failed tasks
**So that** transient errors don't require manual intervention

**US-4: View Task Details**
**As a** crawler operator
**I want** to see full details of any task (input, output, errors)
**So that** I can debug failures

### Secondary

**US-5: Manage Configuration**
**As a** crawler operator
**I want** to view and update crawler configuration
**So that** I can tune behavior without redeploying

**US-6: View Logs**
**As a** crawler operator
**I want** to search and filter logs
**So that** I can diagnose issues

---

## Acceptance Criteria

### Must Have

1. **Given** a running crawler instance
   **When** I open the dashboard
   **Then** I see: tasks pending, completed, failed counts

2. **Given** tasks in the queue
   **When** I view the queue page
   **Then** I see a paginated list with: task_id, URL, status, retries

3. **Given** a failed task
   **When** I click "Retry"
   **Then** the task is re-queued and status changes to "pending"

4. **Given** a task
   **When** I click "View Details"
   **Then** I see full JSON: input, output, error, timestamps

5. **Given** a running crawler
   **When** I view the health page
   **Then** I see: CPU %, Memory %, uptime, tasks/minute throughput

### Should Have

6. Configuration editor (JSON) with validation
7. Log viewer with level filter (INFO, WARN, ERROR)
8. Auto-refresh toggle for dashboard

### Won't Have (This Iteration)

- Multi-crawler view (that's taxlien-parser's job)
- Platform selection (crawler is platform-agnostic)
- K8s integration (crawler doesn't know about K8s)
- User authentication (single-user assumed)

---

## Constraints

- **Technical**: Must use crawler's existing FastAPI endpoints
- **Deployment**: AppSmith runs as sidecar or embedded in crawler container
- **Independence**: No external dependencies (no Redis, no external DB for AppSmith)
- **Storage**: AppSmith uses SQLite (local)

---

## API Endpoints Required

Based on existing crawler API (from `sdd-crawler-architecrure`):

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/health` | GET | Health check + metrics |
| `/tasks` | GET | List tasks (paginated) |
| `/tasks` | POST | Create task |
| `/tasks/{id}` | GET | Task details |
| `/tasks/{id}/retry` | POST | Retry failed task |
| `/config` | GET | Current config |
| `/config` | PUT | Update config |

**New endpoints needed:**

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/metrics` | GET | Detailed metrics (CPU, memory, throughput) |
| `/logs` | GET | Log entries (with filters) |

---

## UI Pages

| Page | Purpose |
|------|---------|
| **Dashboard** | Overview: task counts, health summary, recent activity |
| **Tasks** | Task queue: list, filter, retry, view details |
| **Health** | Metrics: CPU, memory, throughput charts |
| **Config** | Configuration editor |
| **Logs** | Log viewer with search |

---

## Open Questions

- [ ] Should AppSmith be embedded in crawler Docker image or separate sidecar?
- [ ] What log storage backend? (file-based, SQLite, or in-memory?)
- [ ] Should config changes require crawler restart?

---

## References

- `crawler/flows/sdd-crawler-architecrure/01-architecture.md` — Crawler architecture
- `crawler/flows/sdd-crawler-architecrure/` — API endpoints

---

## Approval

- [ ] Reviewed by: [name]
- [ ] Approved on: [date]
- [ ] Notes: [any conditions or clarifications]
