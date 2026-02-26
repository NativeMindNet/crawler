# Requirements: Flower Real-Time Monitoring Dashboard

**Version:** 1.0
**Status:** REQUIREMENTS PHASE
**Last Updated:** 2026-02-26

---

## 1. Problem Statement

The current `sdd-crawler` specification (both SQLite and Celery modes) lacks **real-time operational visibility**. When running crawlers in production, operators cannot answer critical questions:

- How many tasks are currently being processed?
- Which workers are active and what are they doing?
- What is the success/failure rate of tasks?
- Are there any tasks stuck or taking too long?
- What is the current queue depth?
- How many tasks completed in the last hour/day?

The legacy-celery codebase includes **Flower** (`flower==2.0.1` in requirements.txt) but provides **no implementation details** for:
- How Flower integrates with the crawler
- What monitoring views are needed
- How operators access the dashboard
- What alerts or notifications should trigger

The main `sdd-crawler` spec mentions monitoring only briefly:
- `/health` endpoint for queue depth (SQLite mode)
- No real-time task progress visualization
- No worker status dashboard
- No task history or retry logs

This creates an **operational blind spot** for production deployments.

---

## 2. Goal

Integrate **Flower** as a **real-time monitoring and administration dashboard** for Celery-based crawler deployments:

- **Real-Time Visibility**: Live task progress, worker status, queue depth
- **Task Administration**: View task details, retry failed tasks, revoke stuck tasks
- **Performance Analytics**: Success rates, average task duration, throughput metrics
- **Prometheus Integration**: Export metrics for external monitoring (Grafana)
- **Secure Access**: Authentication (HTTP Basic Auth or OAuth) for dashboard access
- **Docker-Native**: Flower runs as a separate container alongside Celery workers

Flower is **optional** and only required for **Celery mode** deployments:
- **SQLite Mode**: No Flower needed (local logging only)
- **Celery Mode**: Flower recommended for production monitoring

---

## 3. User Stories

### US-1: Real-Time Task Monitoring
**As** an operations engineer
**I want** to see all running and pending tasks in real-time
**So that** I can monitor crawler progress and identify bottlenecks

**Acceptance Criteria:**
- [ ] Dashboard shows all active tasks with progress indicators
- [ ] Task list includes: task name, args, start time, runtime, worker
- [ ] Pending tasks show position in queue
- [ ] Completed tasks show status (success/failed) and duration
- [ ] Task list auto-refreshes without page reload
- [ ] Filter tasks by status (active, pending, completed, failed)

### US-2: Worker Status Dashboard
**As** an operations engineer
**I want** to see all Celery workers and their status
**So that** I can verify workers are healthy and scaling properly

**Acceptance Criteria:**
- [ ] Dashboard lists all registered workers
- [ ] Worker status shows: online/offline, current task, pool size
- [ ] Worker details include: hostname, concurrency, prefetch limit
- [ ] Worker statistics: tasks completed, tasks failed, uptime
- [ ] Visual indicator for worker health (green/yellow/red)
- [ ] Auto-detect when workers join or leave the cluster

### US-3: Task Details & Debugging
**As** a developer
**I want** to inspect individual task details
**So that** I can debug failures and understand task behavior

**Acceptance Criteria:**
- [ ] Click task to view full details (args, kwargs, result)
- [ ] View task execution timeline (queued, started, completed)
- [ ] View task logs and error messages
- [ ] View task retry history (if retried)
- [ ] Download task result (if large payload)
- [ ] View task chain/group relationships

### US-4: Task Administration
**As** an operator
**I want** to manage tasks from the dashboard
**So that** I can recover from failures without redeploying

**Acceptance Criteria:**
- [ ] Retry failed tasks with one click
- [ ] Revoke (cancel) stuck or running tasks
- [ ] Terminate tasks that are hung
- [ ] Rate limit tasks per type or worker
- [ ] Confirm actions before execution (prevent accidents)
- [ ] Admin actions are logged for audit trail

### US-5: Performance Analytics
**As** a platform operator
**I want** to see task performance statistics
**So that** I can optimize crawler configuration and identify slow platforms

**Acceptance Criteria:**
- [ ] Dashboard shows task statistics (1h, 24h, 7d ranges)
- [ ] Metrics include: total tasks, success rate, avg runtime, median runtime
- [ ] Runtime distribution histogram (identify outliers)
- [ ] Throughput graph (tasks completed per minute/hour)
- [ ] Breakdown by task type (scrape, parse, save, import)
- [ ] Breakdown by platform (qpublic, beacon, etc.)

### US-6: Prometheus Metrics Export
**As** an SRE
**I want** Flower to export Prometheus metrics
**So that** I can integrate with Grafana dashboards and alerting

**Acceptance Criteria:**
- [ ] Flower exposes `/metrics` endpoint for Prometheus scraping
- [ ] Metrics include: task count, task runtime, worker count, queue depth
- [ ] Metrics support labels (task_name, worker, status)
- [ ] Pre-built Grafana dashboard available
- [ ] Alerting rules documented (e.g., "queue depth > 1000 for 5min")

### US-7: Secure Dashboard Access
**As** a security officer
**I want** the Flower dashboard to require authentication
**So that** unauthorized users cannot view or modify tasks

**Acceptance Criteria:**
- [ ] Support HTTP Basic Auth (username/password)
- [ ] Support OAuth providers (Google, GitHub, GitLab, Okta)
- [ ] Configurable access control (read-only vs admin users)
- [ ] HTTPS support (SSL/TLS termination)
- [ ] Session timeout after inactivity
- [ ] Failed login attempts are logged

### US-8: Docker Compose Integration
**As** a DevOps engineer
**I want** Flower to be deployable via Docker Compose
**So that** monitoring is part of the standard crawler stack

**Acceptance Criteria:**
- [ ] Flower service defined in docker-compose.yml
- [ ] Flower connects to same Redis broker as workers
- [ ] Flower port configurable (default: 5555)
- [ ] Flower configuration via environment variables
- [ ] Flower container is lightweight (minimal dependencies)
- [ ] Flower logs to stdout for Docker log drivers

### US-9: Legacy Compatibility
**As** an operator migrating from legacy-celery
**I want** Flower to work with existing task definitions
**So that** I get monitoring without code changes

**Acceptance Criteria:**
- [ ] Flower auto-discovers tasks from `tasks.py` and platform modules
- [ ] Task names match legacy naming (e.g., `qpublic_scrape_counties_urls_task`)
- [ ] Task arguments and results display correctly
- [ ] Task chains/groups show parent-child relationships
- [ ] Compatible with Celery 5.4.0+ (legacy version)

---

## 4. Constraints

- **C-1**: Must use Flower 2.0.1+ (version from legacy-celery/requirements.txt)
- **C-2**: Must connect to same Redis broker as Celery workers
- **C-3**: Must support Celery events (required for real-time monitoring)
- **C-4**: Must work with existing task definitions (no code changes required)
- **C-5**: Must support Docker deployment (containerized architecture)
- **C-6**: Must support authentication (Basic Auth minimum, OAuth preferred)
- **C-7**: Prometheus integration is optional but recommended
- **C-8**: Flower is **Celery-mode only** (not needed for SQLite standalone mode)

---

## 5. Non-Goals

- **NG-1**: Replacing Flower with custom dashboard (use Flower as-is)
- **NG-2**: Supporting multiple Celery clusters from one Flower instance (one Flower per cluster)
- **NG-3**: Custom metrics beyond Celery defaults (use Prometheus for custom metrics)
- **NG-4**: Mobile-responsive dashboard (Flower desktop-first is acceptable)
- **NG-5**: Task result content search (Flower shows results, doesn't index them)
- **NG-6**: Long-term task history (Flower is real-time, use external logging for history)

---

## 6. Open Questions

1. **Q1 - Authentication**: Which auth method to prioritize? Basic Auth, OAuth, or both?
2. **Q2 - OAuth Provider**: If OAuth, which provider? (Google, GitHub, GitLab, Okta)
3. **Q3 - Port Exposure**: Should Flower be exposed publicly or internal-only (via reverse proxy)?
4. **Q4 - Prometheus**: Is Prometheus/Grafana integration required for MVP, or optional add-on?
5. **Q5 - Custom Views**: Do we need custom Flower tabs/views for crawler-specific metrics?
6. **Q6 - Alerting**: Should Flower send alerts (email/webhook) or just display metrics?
7. **Q7 - Persistence**: How long should Flower retain task history in memory? (default: unlimited until restart)

---

## 7. Legacy Code Analysis Summary

### Flower in Legacy-Celery:

| File | Evidence | Purpose |
|------|----------|---------|
| `requirements.txt` | `flower==2.0.1` | Flower dependency included |
| `dev_run_flower.sh` | Script exists (not yet analyzed) | Development Flower launcher |
| `celery_app.py` | Celery app with Redis broker | Flower connects to this broker |

### Expected Flower Configuration (from legacy patterns):

```python
# Celery app must enable events for Flower monitoring
app = Celery('app', broker='redis://localhost:6379/0')
app.conf.update(
    worker_send_task_events=True,  # Required for Flower
    task_send_sent_events=True,    # Required for Flower
)
```

### Flower Launch Command (expected):

```bash
flower --app=celery_app:app --broker=redis://localhost:6379/0 --port=5555
```

### Flower Configuration Options (from docs):

```python
# flowerconfig.py (optional)
broker = "redis://localhost:6379/0"
auth = "basic"  # or "oauth"
oauth2_key = "..."  # If using OAuth
oauth2_secret = "..."
oauth2_redirect_uri = "..."
prometheus = True
metrics_port = 5556
```

---

## 8. Integration with Existing SDD Flows

### Flows That Need Flower Support:

| SDD Flow | Flower Integration Needed |
|----------|---------------------------|
| `sdd-crawler` (main) | No (SQLite mode only) |
| `sdd-crawler-celery` | **Yes** - Primary monitoring interface |
| `sdd-crawler-bulk` | Bulk job monitoring via Flower |
| `sdd-crawler-photos` | Image download task monitoring |
| `sdd-crawler-ondemand` | Gateway task monitoring |
| `sdd-crawler-standalone` | No (SQLite mode only) |
| `sdd-crawler-priority` | No (SQLite mode only) |

### Conflicts to Resolve:

1. **Event Emission Overhead**: Celery events (required for Flower) add ~5-10% overhead
   - **Resolution**: Make events optional; enable only when Flower is deployed

2. **Task History Persistence**: Flower keeps history in memory (lost on restart)
   - **Resolution**: Document limitation; use external logging for audit trail

3. **SQLite vs Celery Mode**: Flower only works with Celery
   - **Resolution**: Clearly document Flower as "Celery mode only" feature

---

## 9. Acceptance Criteria (Summary)

### Must Have

1. **Given** Flower is running with Celery workers
   **When** I access `http://localhost:5555`
   **Then** I see the Flower dashboard with workers and tasks

2. **Given** a task is executing
   **When** I view the task list
   **Then** I see real-time progress and worker assignment

3. **Given** authentication is configured
   **When** I access Flower
   **Then** I must log in before viewing the dashboard

4. **Given** a task failed
   **When** I click the task
   **Then** I can see the error message and retry the task

### Should Have

- Prometheus metrics endpoint (`/metrics`)
- Task statistics (success rate, avg duration)
- Worker health indicators
- Auto-refresh without page reload

### Won't Have (This Iteration)

- Custom crawler-specific tabs
- Long-term task history (beyond session)
- Mobile-responsive design
- Built-in alerting (email/webhook)

---

## 10. Flower Feature Reference (from Documentation)

### Core Features:

| Feature | Description | Priority |
|---------|-------------|----------|
| **Real-Time Monitoring** | Live task and worker status | Must Have |
| **Task Details** | Args, result, runtime, logs | Must Have |
| **Task Administration** | Retry, revoke, terminate | Must Have |
| **Worker Stats** | Pool size, concurrency, uptime | Must Have |
| **Filtering** | Filter by status, name, worker | Should Have |
| **Statistics** | Success rate, runtime distribution | Should Have |
| **Prometheus Export** | Metrics for Grafana | Should Have |
| **Authentication** | Basic Auth, OAuth | Must Have |
| **Reverse Proxy** | nginx, Traefik support | Should Have |
| **REST API** | Programmatic access | Nice to Have |

### Prometheus Metrics (from docs):

- `flower_events_total` - Total number of Celery events
- `flower_event_processing_time_seconds` - Event processing time
- `flower_worker_tasks_total` - Tasks completed per worker
- `flower_worker_status` - Worker online/offline status
- `flower_task_runtime_seconds` - Task execution time
- `flower_task_status` - Task status (success/failed/running)

---

## Next Phase

After requirements are approved, move to **SPECIFICATIONS** phase to define:
- Flower deployment architecture (Docker Compose)
- Celery event configuration
- Authentication setup (Basic Auth vs OAuth)
- Prometheus metrics configuration
- Reverse proxy setup (nginx/Traefik)
- Security hardening (HTTPS, session management)

---

## Approval

- [ ] Reviewed by: [name]
- [ ] Approved on: [date]
- [ ] Notes: [any conditions or clarifications]
