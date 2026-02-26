# Requirements: Celery Distributed Task Queue Integration

**Version:** 1.0
**Status:** REQUIREMENTS PHASE
**Last Updated:** 2026-02-26

---

## 1. Problem Statement

The current `sdd-crawler` specification describes a **single-instance, SQLite-based task queue** architecture. However, the legacy-celery codebase (`/legacy/legacy-celery/`) contains **distributed task orchestration patterns** that are NOT captured in the main SDD:

### Missing Capabilities from Legacy-Celery:

1. **Distributed Task Execution**: Multiple worker nodes processing tasks in parallel via Redis broker
2. **Task Chain Orchestration**: Celery chains/groups for complex multi-step workflows (scrape → save → parse → import)
3. **Periodic Task Scheduling**: Celery Beat for scheduled crawling (e.g., "every 30 minutes", "every Monday 7:30 AM")
4. **Result Backend**: Redis-based result storage with expiration policies
5. **Task Rate Limiting**: Per-task rate annotations (e.g., "5 tasks per minute")
6. **Task Monitoring**: Flower integration for real-time task monitoring and debugging
7. **Platform-Specific Task Modules**: Modular platform implementations (e.g., `platforms/qpublic/`)

The current `sdd-crawler` spec assumes:
- Single Docker container operation
- SQLite for local task persistence
- No distributed worker coordination
- No periodic scheduling built-in

This creates a **capability gap** for production deployments requiring:
- Horizontal scaling (multiple workers)
- High-throughput parallel scraping
- Scheduled recurring crawls
- Centralized task monitoring

---

## 2. Goal

Extend `sdd-crawler` to support **Celery-based distributed task orchestration** as an **optional deployment mode**:

- **Standalone Mode**: SQLite-based (current SDD spec) - for single-instance, low-volume crawling
- **Celery Mode**: Redis-based distributed queue - for multi-worker, high-volume, scheduled crawling

Both modes share the same:
- Core scraping/parsing engine
- Platform configurations
- Result formats
- Webhook notifications

But differ in:
- Task queue backend (SQLite vs Redis)
- Worker coordination (single vs distributed)
- Scheduling (manual/CLI vs Beat periodic)
- Monitoring (logs vs Flower dashboard)

---

## 3. User Stories

### US-1: Horizontal Scaling
**As** a platform operator
**I want** to run multiple crawler worker containers
**So that** I can process hundreds of URLs in parallel

**Acceptance Criteria:**
- [ ] Multiple workers can connect to the same Redis broker
- [ ] Tasks are distributed across workers automatically
- [ ] No task duplication (each task processed once)
- [ ] Workers can scale up/down dynamically
- [ ] Results are collected in a central backend

### US-2: Task Chain Orchestration
**As** a developer
**I want** to define multi-step task workflows (chains)
**So that** complex operations execute atomically

**Acceptance Criteria:**
- [ ] Support Celery chains: `chain(scrape, save_html, parse, import_db)()`
- [ ] Support Celery groups: `group(task(url) for url in urls)()`
- [ ] Output of one task becomes input of next
- [ ] Chain fails fast on error (configurable)
- [ ] Chain progress is trackable

### US-3: Periodic Scheduling
**As** a data engineer
**I want** to schedule recurring crawls (e.g., daily, weekly)
**So that** data stays fresh without manual intervention

**Acceptance Criteria:**
- [ ] Celery Beat configuration for periodic tasks
- [ ] Support cron-like schedules (e.g., "every 30 minutes", "Monday 7:30 AM")
- [ ] Periodic tasks are platform-specific (different schedules per platform)
- [ ] Schedule configuration is externalized (not hardcoded)
- [ ] Can enable/disable periodic tasks without redeploy

### US-4: Task Monitoring (Flower)
**As** an operator
**I want** a web dashboard to monitor task execution
**So that** I can debug failures and track throughput

**Acceptance Criteria:**
- [ ] Flower integration for task monitoring
- [ ] Real-time task progress visualization
- [ ] Task history and retry logs
- [ ] Worker status and queue depth
- [ ] Task statistics (success rate, avg duration)

### US-5: Rate Limiting & Throttling
**As** a platform operator
**I want** to limit task execution rate per platform
**So that** I don't trigger anti-bot defenses

**Acceptance Criteria:**
- [ ] Per-task rate limits (e.g., "5 tasks/minute")
- [ ] Per-platform rate limits via configuration
- [ ] Rate limits are enforced by Celery broker
- [ ] Rate limit violations are logged

### US-6: Result Backend with Expiration
**As** an operator
**I want** task results stored with automatic cleanup
**So that** Redis doesn't fill up with old data

**Acceptance Criteria:**
- [ ] Results stored in Redis (or alternative backend)
- [ ] Configurable expiration (e.g., 30 days)
- [ ] Results accessible via task ID
- [ ] Result serialization supports complex types (dict, list)

### US-7: Platform-Modular Task Definitions
**As** a developer
**I want** platform-specific task modules
**So that** each platform has its own task chain logic

**Acceptance Criteria:**
- [ ] Platform tasks in `platforms/{platform}/{platform}_tasks.py`
- [ ] Platform-specific task chains (e.g., `qpublic_main_chain()`)
- [ ] Shared core tasks (scrape, save, parse) are reusable
- [ ] Auto-discovery of platform task modules

### US-8: Legacy Compatibility Mode
**As** an operator migrating from legacy-celery
**I want** to preserve existing task chain patterns
**So that** I can migrate incrementally

**Acceptance Criteria:**
- [ ] Support legacy task signatures (e.g., `qpublic_scrape_counties_urls_task`)
- [ ] Support legacy data flow (counties → parcels → single URLs)
- [ ] Compatible with existing platform configs
- [ ] Migration path documented

---

## 4. Constraints

- **C-1**: Must coexist with standalone mode (SQLite) - Celery is **optional**, not mandatory
- **C-2**: Must use Redis as primary broker (legacy compatibility)
- **C-3**: Must support Celery 5.4.0+ (version from legacy-celery/requirements.txt)
- **C-4**: Must support Flower 2.0.1+ for monitoring
- **C-5**: Must preserve platform-specific task logic from legacy-celery
- **C-6**: Must support SeleniumBase integration (headless browser automation)
- **C-7**: Must support sbvirtualdisplay for Xvfb display emulation
- **C-8**: Task chains must handle exceptions gracefully (log + continue, not crash)

---

## 5. Non-Goals

- **NG-1**: Replacing SQLite mode - Celery is an **alternative**, not a replacement
- **NG-2**: Supporting multiple brokers simultaneously (Redis only for Celery mode)
- **NG-3**: Complex task routing (single queue for all tasks)
- **NG-4**: Task priorities in Celery mode (FIFO only, priorities are SQLite-mode feature)
- **NG-5**: Re-implementing legacy task logic - preserve existing patterns from `/legacy/legacy-celery/`

---

## 6. Open Questions

1. **Q1 - Broker Configuration**: Should Redis connection be via environment variable, config file, or Docker network alias?
2. **Q2 - Task Serialization**: JSON (default) or msgpack/pickle for complex Python objects?
3. **Q3 - Error Handling**: Should failed tasks auto-retry? How many retries? What's the backoff strategy?
4. **Q4 - Result Backend**: Redis only, or support SQLite/file backend for simpler deployments?
5. **Q5 - Periodic Task Config**: JSON file, environment variables, or database-driven schedules?
6. **Q6 - Worker Configuration**: How to configure worker concurrency, prefetch limits, pool type?
7. **Q7 - Deployment**: Docker Compose setup for Celery + Redis + Flower, or separate orchestration?

---

## 7. Legacy Code Analysis Summary

### Components Identified in `/legacy/legacy-celery/`:

| File | Purpose | Reuse Strategy |
|------|---------|----------------|
| `celery_app.py` | Celery app initialization | Extract pattern, modernize config |
| `tasks.py` | Task chains, periodic setup | Preserve structure, refactor for modularity |
| `functions.py` | Shared utilities (scrape, save, parse) | Integrate into core engine |
| `platforms/qpublic/qpublic_functions.py` | Platform-specific scraping/parsing | Migrate to platform modules |
| `requirements.txt` | Dependencies (Celery, Redis, Flower) | Merge with main requirements |
| `dev_run_*.sh` | Development scripts | Update for new architecture |

### Task Chain Patterns Identified:

```python
# Main chain: QPublic full crawl
qpublic_main_chain()
  └─> qpublic_scrape_counties_urls_task(url)
  └─> qpublic_get_all_parcels_urls_task(counties_urls)
  └─> save_json(all_parcels_urls)
  └─> group(qpublic_single_url_chain(url) for url in all_parcels_urls)

# Single URL chain
qpublic_single_url_chain(url)
  └─> scrape_url_task(url)
  └─> save_html_task(html)
  └─> qpublic_parse_html_task(html)
  └─> import_to_db_task(data)
```

### Configuration Patterns:

```python
app.conf.update(
    timezone='Europe/Moscow',
    enable_utc=True,
    result_backend='redis://localhost:6379/0',
    result_expires=3600 * 24 * 30,  # 30 days
    task_annotations={'*': {'rate_limit': '5/m'}}
)
```

---

## 8. Integration with Existing SDD Flows

### Flows That Need Celery Support:

| SDD Flow | Celery Integration Needed |
|----------|---------------------------|
| `sdd-crawler` (main) | Core task queue backend option |
| `sdd-crawler-bulk` | Bulk ingestion as Celery tasks |
| `sdd-crawler-photos` | Image download as Celery group |
| `sdd-crawler-ondemand` | Gateway tasks via Celery |
| `sdd-crawler-standalone` | Alternative to SQLite loop |
| `sdd-crawler-priority` | NOT compatible (Celery is FIFO only) |

### Conflicts to Resolve:

1. **Priority Queue**: SQLite mode supports priorities; Celery mode is FIFO only
   - **Resolution**: Document as limitation, or implement priority via multiple queues

2. **Local Ripple Effect**: Standalone auto-adds discovered links to local queue
   - **Resolution**: In Celery mode, discovered links submitted as new tasks to broker

3. **State Persistence**: SQLite mode has local checkpointing
   - **Resolution**: Celery mode uses result backend for state, no local checkpoint needed

---

## 9. Acceptance Criteria (Summary)

### Must Have

1. **Given** a Redis broker is available
   **When** workers start with `--celery` flag
   **Then** they connect to Redis and consume tasks

2. **Given** a task chain is submitted
   **When** tasks execute sequentially
   **Then** output of each task is passed to the next

3. **Given** Celery Beat is configured
   **When** a scheduled time arrives
   **Then** the periodic task is triggered

4. **Given** Flower is running
   **When** I access the Flower dashboard
   **Then** I can see task status, workers, and statistics

### Should Have

- Graceful shutdown (complete current task, then exit)
- Task timeout configuration (per-task or global)
- Task retry on failure (configurable retries)

### Won't Have (This Iteration)

- Task priorities in Celery mode
- Multiple broker support
- Complex routing rules

---

## Next Phase

After requirements are approved, move to **SPECIFICATIONS** phase to define:
- Celery app architecture and configuration
- Task definitions and signatures
- Chain/group orchestration patterns
- Periodic task scheduling design
- Flower deployment configuration
- Docker Compose setup for Celery stack

---

## Approval

- [ ] Reviewed by: [name]
- [ ] Approved on: [date]
- [ ] Notes: [any conditions or clarifications]
