# Requirements: On-demand Mode (Celery-based)

**Version:** 1.0
**Status:** DRAFT
**Last Updated:** 2026-03-01

---

## 1. Goal

Implement a mode where the crawler fetches tasks from the **Gateway API** via Celery Beat, processes them with Celery Workers, and syncs results back via background tasks — all with **local persistence** for resilience.

---

## 2. Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         ON-DEMAND MODE                                   │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                      Celery Beat (Scheduler)                     │   │
│  │  ┌─────────────────┐              ┌─────────────────┐           │   │
│  │  │ collect_tasks   │              │ sync_results    │           │   │
│  │  │ (every 30s)     │              │ (every 60s)     │           │   │
│  │  └────────┬────────┘              └────────┬────────┘           │   │
│  └───────────┼────────────────────────────────┼─────────────────────┘   │
│              │                                │                         │
│              ▼                                ▼                         │
│  ┌───────────────────┐              ┌───────────────────┐              │
│  │    Gateway API    │              │    Gateway API    │              │
│  │  GET /internal/   │              │  POST /internal/  │              │
│  │      work         │              │      results      │              │
│  └─────────┬─────────┘              └─────────┬─────────┘              │
│            │                                  │                         │
│            ▼                                  │                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                         Redis Broker                             │   │
│  │                  Queues: urgent | high | default                 │   │
│  └──────────────────────────────┬──────────────────────────────────┘   │
│                                 │                                       │
│                                 ▼                                       │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                      Celery Workers                              │   │
│  │              scrape_task → parse_task → save_task                │   │
│  └──────────────────────────────┬──────────────────────────────────┘   │
│                                 │                                       │
│                                 ▼                                       │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                LocalPersistenceManager (LPM)                     │   │
│  │   lpm.db (task state) | pending/ (results) | raw/ (HTML)        │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 3. User Stories

### US-1: Reliable Task Processing
**As a** system operator
**I want** the worker to fetch tasks from Gateway and persist them locally before processing
**So that** if the worker crashes, task state is not lost

**Celery Implementation:**
- `collect_tasks` Beat task fetches from Gateway
- Tasks immediately submitted to Redis queue
- LPM tracks task state for recovery

---

### US-2: Asynchronous Result Delivery
**As a** system operator
**I want** results stored locally first, then synced to Gateway in background
**So that** scraping performance is decoupled from Gateway latency

**Celery Implementation:**
- Workers save results to LPM (`/data/pending/`)
- `sync_results` Beat task uploads completed results
- Retry on Gateway failure with exponential backoff

---

### US-3: Real-time Scalability
**As a** system operator
**I want** to spin up multiple workers reporting to same Gateway
**So that** I can scale parsing capacity dynamically

**Celery Implementation:**
- Multiple Celery workers consume from same Redis broker
- Each worker has own LPM for local persistence
- Gateway sees aggregated results from all workers

---

## 4. Functional Requirements

### FR-1: Gateway Task Collector (Celery Beat)

```python
@app.task(bind=True)
def collect_tasks(self):
    """Fetch tasks from Gateway and submit to Celery queue."""
    response = gateway_client.get_work(limit=50)

    for task in response.tasks:
        # Determine queue based on priority
        queue = priority_to_queue(task.priority)

        # Submit to Celery
        scrape_task.apply_async(
            args=[task.url],
            kwargs={'task_id': task.id, 'metadata': task.metadata},
            queue=queue
        )

        # Track in LPM
        lpm.track_task(task.id, status='queued')

# Beat schedule
app.conf.beat_schedule = {
    'collect-from-gateway': {
        'task': 'crawler.tasks.collect_tasks',
        'schedule': 30.0,  # Every 30 seconds
        'options': {'queue': 'beat'}
    },
}
```

---

### FR-2: Local Execution (Celery Workers)

```python
@app.task(bind=True, max_retries=3)
def scrape_task(self, url, task_id=None, metadata=None):
    """Scrape URL and save to LPM."""
    try:
        # Mark as processing
        lpm.update_task(task_id, status='processing')

        # Scrape
        html = scraper.fetch(url)

        # Parse
        result = parser.parse(html)

        # Save to LPM
        lpm.save_result(task_id, result)
        lpm.save_raw(task_id, html)
        lpm.update_task(task_id, status='completed', sync_status='pending')

        return {'task_id': task_id, 'status': 'completed'}

    except Exception as e:
        lpm.update_task(task_id, status='failed', error=str(e))
        raise self.retry(exc=e, countdown=60)
```

---

### FR-3: Background Sync Service (Celery Beat)

```python
@app.task(bind=True)
def sync_results(self):
    """Upload completed results to Gateway."""
    pending = lpm.get_unsynced_results(limit=100)

    for result in pending:
        try:
            # Upload raw files first
            if result.raw_path:
                gateway_client.upload_raw(result.task_id, result.raw_path)

            # Submit result
            gateway_client.submit_result(result.task_id, result.data)

            # Mark synced
            lpm.update_task(result.task_id, sync_status='synced')

        except GatewayError as e:
            lpm.update_task(result.task_id, sync_status='failed', sync_error=str(e))
            # Will retry on next beat

# Beat schedule
app.conf.beat_schedule = {
    'sync-to-gateway': {
        'task': 'crawler.tasks.sync_results',
        'schedule': 60.0,  # Every minute
        'options': {'queue': 'beat'}
    },
}
```

---

### FR-4: Heartbeat & Health

```python
@app.task
def send_heartbeat():
    """Report worker health to Gateway."""
    stats = {
        'worker_id': worker_id,
        'queue_depth': lpm.get_queue_depth(),
        'pending_sync': lpm.count_unsynced(),
        'completed_1h': lpm.count_completed(hours=1),
        'failed_1h': lpm.count_failed(hours=1),
    }
    gateway_client.heartbeat(stats)

app.conf.beat_schedule = {
    'heartbeat': {
        'task': 'crawler.tasks.send_heartbeat',
        'schedule': 60.0,
    },
}
```

---

## 5. LPM State Tables

```sql
-- Task tracking
CREATE TABLE ondemand_tasks (
    task_id TEXT PRIMARY KEY,
    gateway_task_id TEXT,
    url TEXT,
    priority INTEGER,
    status TEXT,          -- queued, processing, completed, failed
    sync_status TEXT,     -- pending, syncing, synced, failed
    celery_task_id TEXT,
    queued_at TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    synced_at TIMESTAMP,
    error TEXT,
    sync_error TEXT
);

-- Results pending sync
CREATE TABLE pending_results (
    task_id TEXT PRIMARY KEY,
    result_json TEXT,
    raw_path TEXT,
    created_at TIMESTAMP,
    sync_attempts INTEGER DEFAULT 0,
    last_sync_attempt TIMESTAMP
);
```

---

## 6. Configuration

```python
# Environment variables
GATEWAY_URL = "https://api.taxlien.online"
GATEWAY_API_KEY = "..."
COLLECT_INTERVAL = 30      # seconds
SYNC_INTERVAL = 60         # seconds
HEARTBEAT_INTERVAL = 60    # seconds
COLLECT_BATCH_SIZE = 50
SYNC_BATCH_SIZE = 100
SYNC_MAX_RETRIES = 5
```

---

## 7. Docker Compose

```yaml
# docker-compose.ondemand.yml
version: '3.8'
services:
  redis:
    image: redis:7-alpine

  worker:
    image: crawler:latest
    command: celery -A crawler worker -Q urgent,high,default,beat -c 4
    environment:
      - GATEWAY_URL=${GATEWAY_URL}
      - GATEWAY_API_KEY=${GATEWAY_API_KEY}
    volumes:
      - ./data:/data

  beat:
    image: crawler:latest
    command: celery -A crawler beat --loglevel=info
    environment:
      - GATEWAY_URL=${GATEWAY_URL}
      - GATEWAY_API_KEY=${GATEWAY_API_KEY}
    depends_on:
      - redis

  flower:
    image: mher/flower:2.0
    command: celery flower --broker=redis://redis:6379
    ports:
      - "5555:5555"
```

---

## 8. Sequence Diagram

```
Gateway          Beat           Redis         Workers         LPM
   │               │              │              │              │
   │◄──get_work()──│              │              │              │
   │──tasks[]─────►│              │              │              │
   │               │──task.delay()─►│             │              │
   │               │              │──task────────►│              │
   │               │              │              │──save_result()─►│
   │               │              │              │              │
   │               │◄─────────────────sync_results()───────────│
   │◄─submit_result()─────────────────────────────│              │
   │               │              │              │◄─mark_synced()─│
```

---

## 9. Comparison: Async vs Celery

| Aspect | Async (old) | Celery (new) |
|--------|-------------|--------------|
| Collector | Background thread | **Beat task** |
| Worker | Async loop | **Celery workers** |
| Sync | Background thread | **Beat task** |
| Parallelism | 1 process | **N workers** |
| Monitoring | Logs | **Flower** |
| Retry | Manual code | **Built-in** |
| Scaling | Restart process | **Add workers** |

---

## 10. Implementation Tasks

| Task | Description | Complexity |
|------|-------------|------------|
| 1 | Implement `collect_tasks` Beat task | Medium |
| 2 | Implement `sync_results` Beat task | Medium |
| 3 | Implement `send_heartbeat` Beat task | Low |
| 4 | Add LPM tables for ondemand tracking | Low |
| 5 | Add Gateway client methods | Low |
| 6 | Create `docker-compose.ondemand.yml` | Low |
| 7 | Add Beat schedule configuration | Low |

**Total: 7 tasks**

---

## 11. Constraints

- **C-1:** Must use same LPM as standalone mode
- **C-2:** Must handle Gateway outages gracefully (queue locally)
- **C-3:** Must not lose tasks on worker crash (Redis persistence)
- **C-4:** Must report accurate queue depth to Gateway

---

## Approval

- [ ] Reviewed by: [name]
- [ ] Approved on: [date]
