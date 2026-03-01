# Requirements: Standalone Mode (Celery-based)

**Version:** 1.0
**Status:** DRAFT
**Last Updated:** 2026-03-01

---

## 1. Problem Statement

Current workers require the central Gateway API for task acquisition. This creates a single point of failure and prevents:
- Emergency data collection when Gateway is down
- Local testing without production infrastructure
- Isolated benchmarking of parser changes

## 2. Goal

Enable crawler to execute tasks from local sources (CLI/CSV/JSON) using **Celery + local Redis**, storing results locally via LPM, with **no Gateway dependency**.

---

## 3. Key Scenarios

### Scenario A: Emergency Collection

**Context:** Gateway is down for maintenance, but an auction starts in 1 hour.

**Workflow:**
```bash
# 1. Start standalone stack (Redis + Workers + Flower)
docker-compose -f docker-compose.standalone.yml up -d

# 2. Import urgent parcels from CSV
python -m crawler bulk import auction_parcels.csv --queue=urgent

# 3. Monitor in Flower
open http://localhost:5555

# 4. Results appear in /data/pending/
ls ./data/pending/*.json
```

**Outcome:** Data collected locally, ready for manual sync when Gateway recovers.

---

### Scenario B: Performance Benchmarking

**Context:** Testing a new parser version without polluting production database.

**Workflow:**
```bash
# 1. Start isolated stack
docker-compose -f docker-compose.standalone.yml up -d

# 2. Import test sample
python -m crawler bulk import test_sample.csv

# 3. Wait for completion (watch Flower)
# 4. Analyze results
python -m crawler analyze ./data/pending/

# 5. Cleanup
docker-compose -f docker-compose.standalone.yml down -v
```

**Outcome:** Isolated test environment, results reviewed locally, no production impact.

---

### Scenario C: Development & Debugging

**Context:** Developer needs to debug scraper for specific URL.

**Workflow:**
```bash
# Single URL scrape via CLI
celery -A crawler call scrape_task --args='["http://county.gov/parcel/123"]'

# Or via Python
python -c "from crawler.tasks import scrape_task; scrape_task.delay('http://...')"

# Check result in Flower or LPM
```

---

## 4. Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    STANDALONE MODE                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────────────┐ │
│  │   Celery    │    │   Celery    │    │      Flower         │ │
│  │    Beat     │───>│   Workers   │    │   (:5555)           │ │
│  │ (optional)  │    │  (scrape)   │    │   Monitoring        │ │
│  └─────────────┘    └──────┬──────┘    └─────────────────────┘ │
│                            │                                    │
│                            ▼                                    │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                    Redis (local)                         │   │
│  │              Queues: urgent | default                    │   │
│  └─────────────────────────────────────────────────────────┘   │
│                            │                                    │
│                            ▼                                    │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              LocalPersistenceManager (LPM)               │   │
│  │   ┌──────────┐  ┌──────────┐  ┌────────────────────┐    │   │
│  │   │ lpm.db   │  │ pending/ │  │ raw/               │    │   │
│  │   │ (SQLite) │  │ (JSON)   │  │ (HTML/Images)      │    │   │
│  │   └──────────┘  └──────────┘  └────────────────────┘    │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                    NO GATEWAY                            │   │
│  │          (sync disabled, local-only operation)           │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 5. Functional Requirements

### FR-1: Standalone Docker Compose

**Requirement:** Provide `docker-compose.standalone.yml` with minimal dependencies.

**Services:**
| Service | Purpose | Port |
|---------|---------|------|
| redis | Task broker | 6379 |
| worker | Celery workers | — |
| flower | Monitoring UI | 5555 |

**Example:**
```yaml
# docker-compose.standalone.yml
version: '3.8'
services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  worker:
    image: crawler:latest
    command: celery -A crawler worker -Q urgent,default -c 4
    environment:
      - STANDALONE=true
      - REDIS_URL=redis://redis:6379/0
      - GATEWAY_SYNC=disabled
    volumes:
      - ./data:/data
    depends_on:
      - redis

  flower:
    image: mher/flower:2.0
    command: celery flower --broker=redis://redis:6379/0
    ports:
      - "5555:5555"
    depends_on:
      - redis
```

---

### FR-2: Bulk Import from Local Files

**Requirement:** CLI command to import tasks from CSV/JSON into Celery queue.

**Interface:**
```bash
python -m crawler bulk import <file> [options]

Options:
  --queue       Queue name (urgent|default)  [default: default]
  --batch-size  Tasks per batch              [default: 100]
  --dry-run     Show what would be imported
```

**Supported Formats:**

| Format | Structure |
|--------|-----------|
| CSV | `url` column required, optional: `priority`, `parcel_id` |
| JSON | Array of `{"url": "...", "priority": 1}` |
| JSONL | One JSON object per line |
| TXT | One URL per line |

**Example CSV:**
```csv
url,priority,parcel_id
http://county.gov/parcel/123,1,123
http://county.gov/parcel/456,2,456
```

**Import:**
```bash
python -m crawler bulk import parcels.csv --queue=urgent
# Output: Imported 150 tasks to queue 'urgent'
```

---

### FR-3: Local-Only Results (No Gateway Sync)

**Requirement:** When `STANDALONE=true`, disable all Gateway communication.

**Behavior:**
- No calls to `/internal/work` (task collector disabled)
- No calls to `/internal/results` (sync service disabled)
- No heartbeat to Gateway
- Results saved only to LPM (`/data/pending/`)

**Environment Variable:**
```bash
STANDALONE=true          # Disable Gateway sync
GATEWAY_SYNC=disabled    # Alternative flag
```

---

### FR-4: Resume Capability

**Requirement:** Support resuming interrupted scraping sessions.

**Mechanism:**
1. Redis persists task queue (RDB snapshots)
2. LPM tracks task state in SQLite
3. On restart, pending tasks remain in Redis queue

**Resume Workflow:**
```bash
# Session interrupted (Ctrl+C or crash)
docker-compose -f docker-compose.standalone.yml down

# Resume later
docker-compose -f docker-compose.standalone.yml up -d
# Workers automatically continue from Redis queue
```

**LPM State Table:**
```sql
CREATE TABLE standalone_tasks (
    task_id TEXT PRIMARY KEY,
    url TEXT,
    status TEXT,  -- pending, processing, completed, failed
    celery_task_id TEXT,
    imported_at TIMESTAMP,
    completed_at TIMESTAMP
);
```

---

### FR-5: CLI Task Submission

**Requirement:** Submit individual tasks via CLI for debugging.

**Methods:**

```bash
# Method 1: Celery CLI
celery -A crawler call scrape_task --args='["http://example.com/parcel/123"]'

# Method 2: Crawler CLI
python -m crawler scrape http://example.com/parcel/123

# Method 3: Python
python -c "
from crawler.tasks import scrape_task
result = scrape_task.delay('http://example.com/parcel/123')
print(f'Task ID: {result.id}')
"
```

---

### FR-6: Result Export

**Requirement:** Export collected results for manual processing.

**Commands:**
```bash
# List results
python -m crawler results list
# Output: 150 results in /data/pending/

# Export to single JSON
python -m crawler results export --output results.json

# Export to CSV
python -m crawler results export --format csv --output results.csv

# Archive and cleanup
python -m crawler results archive --compress
```

---

## 6. User Stories

### US-1: Emergency Scraping
**As a** crawler operator
**I want** to scrape urgent parcels from a CSV when Gateway is down
**So that** I don't miss auction deadlines

**Acceptance Criteria:**
- [ ] `docker-compose.standalone.yml` starts without Gateway
- [ ] `bulk import` creates Celery tasks from CSV
- [ ] Results appear in `/data/pending/`
- [ ] Flower shows task progress

---

### US-2: Isolated Testing
**As a** developer
**I want** to test parser changes on sample data
**So that** I can verify fixes without affecting production

**Acceptance Criteria:**
- [ ] Standalone stack is fully isolated
- [ ] No data sent to Gateway
- [ ] Results can be analyzed locally
- [ ] Stack can be destroyed cleanly (`down -v`)

---

### US-3: Resume After Crash
**As a** operator
**I want** to resume scraping after worker crash
**So that** I don't lose progress

**Acceptance Criteria:**
- [ ] Redis persists queue state
- [ ] LPM tracks completed tasks
- [ ] Restart continues from where it stopped
- [ ] No duplicate scraping

---

### US-4: Single URL Debug
**As a** developer
**I want** to scrape a single URL for debugging
**So that** I can test specific pages

**Acceptance Criteria:**
- [ ] CLI command for single URL
- [ ] Result visible in Flower
- [ ] HTML/JSON saved to LPM

---

## 7. Comparison: Async vs Celery Standalone

| Aspect | Async (old) | Celery (new) |
|--------|-------------|--------------|
| Workers | 1 process | N workers (parallel) |
| Queue | SQLite | Redis |
| Monitoring | Logs only | **Flower UI** |
| Retry | Manual | **Automatic** |
| Rate Limit | Code | **Annotations** |
| Resume | SQLite state | Redis + LPM |
| Debugging | Hard | **Flower + CLI** |

---

## 8. Implementation Tasks

| Task | Description | Complexity |
|------|-------------|------------|
| 1 | Create `docker-compose.standalone.yml` | Low |
| 2 | Add `STANDALONE` env var handling | Low |
| 3 | Implement `bulk import` CLI command | Medium |
| 4 | Add LPM `standalone_tasks` table | Low |
| 5 | Implement `results export` CLI command | Low |
| 6 | Add single URL CLI (`crawler scrape <url>`) | Low |
| 7 | Documentation and examples | Low |

**Total: 7 tasks**

---

## 9. File Changes

| File | Action | Purpose |
|------|--------|---------|
| `docker-compose.standalone.yml` | Create | Standalone stack |
| `crawler/cli/commands/bulk.py` | Modify | Add `import` command |
| `crawler/cli/commands/results.py` | Create | Export commands |
| `crawler/cli/commands/scrape.py` | Modify | Single URL support |
| `crawler/db/schema.py` | Modify | Add standalone_tasks table |
| `crawler/config.py` | Modify | STANDALONE flag |
| `docs/STANDALONE.md` | Create | Usage documentation |

**Total: 7 files**

---

## 10. Constraints

- **C-1:** Must work completely offline (no internet required for Gateway)
- **C-2:** Must use same LPM as production mode
- **C-3:** Results must be compatible with manual Gateway sync
- **C-4:** Redis data must persist across restarts (RDB)

---

## 11. Non-Goals

- **NG-1:** Automatic Gateway sync when it becomes available
- **NG-2:** Multi-node Redis cluster (single instance sufficient)
- **NG-3:** Kubernetes deployment for standalone (Docker Compose only)

---

## Approval

- [ ] Reviewed by: [name]
- [ ] Approved on: [date]
- [ ] Notes: [any conditions or clarifications]
