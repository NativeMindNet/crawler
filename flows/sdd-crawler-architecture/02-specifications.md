# Specifications: Universal Single-Platform Crawler Architecture

> **Version:** 1.0  
> **Status:** DRAFT  
> **Last Updated:** 2026-03-01  
> **Requirements:** Based on approved architecture v2.1

---

## Overview

This specification defines the implementation of a **universal, single-platform crawler** that is:
- **Platform-agnostic**: Not hardcoded to tax-lien domain
- **Single-platform per instance**: Each deployment handles one platform
- **Externally orchestrated**: Multi-platform coordination happens outside the crawler
- **Dual-mode workers**: Supports both Async (lightweight) and Celery (parallel) modes
- **Config-driven**: Platform behavior defined in JSON, not code

---

## Affected Systems

| System | Impact | Notes |
|--------|--------|-------|
| `crawler/` | Create new structure | Universal crawler module |
| `crawler/lpm.py` | Create | Local Persistence Manager (SQLite + files) |
| `crawler/storage.py` | Create | File storage utilities |
| `crawler/config_loader.py` | Create | Platform config loading |
| `crawler/worker.py` | Create | Task processing worker (dual-mode) |
| `crawler/discovery.py` | Create | Link discovery engine |
| `crawler/priority.py` | Create | Priority calculation |
| `crawler/gateway_sync.py` | Create | Gateway synchronization |
| `crawler/scraper/` | Create | SeleniumBase scraper module |
| `crawler/parser/` | Create | HTML parser module |
| `crawler/bulk/` | Create | Bulk ingestion pipeline |
| `crawler/imagery/` | Create | Image processing module |
| `crawler/api/` | Create | FastAPI endpoints |
| `crawler/cli/` | Create | Typer CLI commands |
| `crawler/webhooks/` | Create | Webhook notifications |
| `config/platforms/` | Create | Platform config directory |
| `docker-compose.yml` | Modify | Crawler service definition |
| `docker-compose.celery.yml` | Create | Celery mode deployment |

---

## Architecture

### Component Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         CRAWLER INSTANCE                                 │
│                    (Single Platform, e.g., "beacon")                     │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐              │
│  │   API        │    │   CLI        │    │   Worker     │              │
│  │  (FastAPI)   │    │   (Typer)    │    │  (Async/     │              │
│  │              │    │              │    │   Celery)    │              │
│  └──────┬───────┘    └──────┬───────┘    └──────┬───────┘              │
│         │                   │                    │                       │
│         └───────────────────┼────────────────────┘                       │
│                             │                                            │
│                             ▼                                            │
│         ┌───────────────────────────────────────────────────┐           │
│         │              LOCAL PERSISTENCE MANAGER            │           │
│         │                   (lpm.py + SQLite)               │           │
│         └───────────────────────────────────────────────────┘           │
│                             │                                            │
│         ┌───────────────────┴────────────────────┐                      │
│         │                                        │                      │
│         ▼                                        ▼                      │
│  ┌──────────────────┐                   ┌──────────────────┐           │
│  │   SCRAPER        │                   │   PARSER         │           │
│  │  - SeleniumBase  │                   │  - Selectors     │           │
│  │  - Anti-bot      │                   │  - Transformer   │           │
│  │  - Retry logic   │                   │  - Validator     │           │
│  │  - Proxy (SOCKS) │                   │                  │           │
│  └──────────────────┘                   └──────────────────┘           │
│                                                                          │
│  ┌──────────────────────────────────────────────────────────┐           │
│  │              PLATFORM CONFIGS (JSON)                     │           │
│  │  - manifest.json    - selectors.json    - mapping.json  │           │
│  │  - discovery.json   - business_rules.json - schedule.json│           │
│  └──────────────────────────────────────────────────────────┘           │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### Data Flow

See `01-architecture.md` Section 4 for detailed data flow diagrams:
- Single Task Flow (Section 4.1)
- Bulk Ingestion Flow (Section 4.2)

---

## Interfaces

### External Interfaces

#### 1. Task Submission API
```python
POST /tasks
{
    "url": str,
    "priority": int = 5,
    "metadata": dict = {}
}
```

#### 2. Bulk Ingestion API
```python
POST /bulk/ingest
{
    "job_name": str,
    "source_files": List[str],
    "mapping_profile": str
}
```

#### 3. Webhook Notifications
```python
POST {webhook_url}
{
    "event": "task.completed" | "task.failed" | "bulk.completed",
    "task_id": str,
    "result": dict,
    "signature": "hmac-sha256"
}
```

### Internal Interfaces

#### Local Persistence Manager (LPM)
```python
class LocalPersistenceManager:
    def queue_task(self, task: Task) -> str
    def get_pending_tasks(self, limit: int = 100) -> List[Task]
    def complete_task(self, task_id: str, result: dict)
    def fail_task(self, task_id: str, error: str)
    def store_result(self, task_id: str, data: dict)
    def store_raw(self, task_id: str, content: bytes, content_type: str)
```

---

## Data Models

### Task Model
```python
@dataclass
class Task:
    id: str
    url: str
    priority: int
    status: TaskStatus  # PENDING, RUNNING, COMPLETED, FAILED
    metadata: dict
    created_at: datetime
    updated_at: datetime
    retry_count: int = 0
    error: Optional[str] = None
```

### Scraped Content Model
```python
@dataclass
class ScrapedContent:
    task_id: str
    url: str
    html: str
    screenshots: List[bytes]
    timestamp: datetime
    platform: str
```

### Parsed Result Model
```python
@dataclass
class ParsedResult:
    task_id: str
    data: dict  # Transformed per mapping.json
    images: List[ImageReference]
    external_links: List[ExternalLink]
    confidence: float
```

### Platform Config Model
```python
@dataclass
class PlatformConfig:
    name: str
    manifest: dict
    selectors: dict
    mapping: dict
    discovery: dict
    business_rules: dict
    schedule: dict
```

---

## Behavior Specifications

### Happy Path: Single Task

1. External system POSTs task to `/tasks`
2. Task queued in LPM with priority
3. Worker picks up task (ordered by priority)
4. Scraper fetches URL with anti-bot bypass
5. Parser extracts data using selectors.json
6. Transformer applies mapping.json
7. Result stored in `/data/pending/{task_id}.json`
8. Webhook sent to external system
9. External system consumes result

### Edge Cases

| Case | Trigger | Expected Behavior |
|------|---------|-------------------|
| Anti-bot challenge | Cloudflare/PerimeterX | Trigger challenge handler, retry |
| Network timeout | Request > 30s | Retry with exponential backoff |
| Selector mismatch | HTML structure changed | Log error, store raw HTML, mark failed |
| Duplicate task | Same URL submitted twice | Dedup by URL hash, skip or update |
| Queue overflow | > 10000 pending tasks | Reject low-priority tasks |
| Webhook failure | External system down | Retry 3x, then log and continue |

### Error Handling

| Error | Cause | Response |
|-------|-------|----------|
| `SelectorNotFound` | CSS/XPath not found in HTML | Log warning, return partial result |
| `MappingError` | mapping.json invalid | Fail task, alert admin |
| `StorageFull` | Disk space exhausted | Fail task, alert admin |
| `ConfigNotFound` | Platform config missing | Fail task, return 400 |
| `WebhookDeliveryFailed` | External system unreachable | Retry 3x, then log |
| `ProxyConnectionFailed` | SOCKS proxy unreachable | Retry with backoff, switch proxy if available |
| `RateLimitExceeded` | Domain rate limit hit | Queue backoff, retry after delay |

---

## Dependencies

### Requires

- Python 3.10+
- SeleniumBase
- FastAPI
- Typer
- SQLite (built-in)
- BeautifulSoup4
- Docker (for deployment)

### Optional Dependencies

- Redis (for Celery mode)
- Celery (for parallel workers)
- Flower (for Celery monitoring)

### Proxy Support

| Type | Configuration | Use Case |
|------|---------------|----------|
| **Plain SOCKS5** | `PROXY_URL=socks5://host:port` | Standard proxy rotation |
| **tor-socks-proxy-service** | `PROXY_URL=socks5://tor-proxy:9050` | Tor anonymity |
| **No Proxy** | (default) | Direct connection |

### Proxy Configuration

```python
# Environment variables
PROXY_URL=socks5://host:port          # Single proxy
PROXY_POOL=socks5://proxy1:port,socks5://proxy2:port  # Pool
TOR_PROXY_ENABLED=true                 # Use tor-socks-proxy-service
```

### Rate Limiting

```python
# Per-domain rate limiting configuration
RATE_LIMITS:
  default: 10 requests/minute
  beacon.example.com: 5 requests/minute
  qpublic.example.com: 20 requests/minute
```

### Blocks

- None (standalone module)

---

## Integration Points

### External Systems

| System | Integration Method |
|--------|-------------------|
| Gateway API | HTTP webhooks |
| Scheduler (cron/Airflow) | HTTP API |
| Result Consumer (taxlien-parser) | File system watch |
| S3/MinIO | Volume mount or SDK |

### Internal Systems

| System | Integration Point |
|--------|-------------------|
| `taxlien-parser` | Reads from `/data/pending/` |
| `config/` | Platform configs mounted as volumes |

---

## Testing Strategy

### Unit Tests

- [ ] `test_lpm.py` - Task queue operations
- [ ] `test_config_loader.py` - Config loading and validation
- [ ] `test_selector_engine.py` - CSS/XPath extraction
- [ ] `test_transformer.py` - Data transformation
- [ ] `test_priority.py` - Priority calculation
- [ ] `test_webhook_signer.py` - HMAC signing

### Integration Tests

- [ ] `test_worker.py` - End-to-end task processing
- [ ] `test_discovery.py` - Link discovery
- [ ] `test_bulk_pipeline.py` - Bulk ingestion
- [ ] `test_api.py` - API endpoints
- [ ] `test_gateway_sync.py` - Gateway synchronization

### Manual Verification

- [ ] Deploy via docker-compose
- [ ] Submit task via API
- [ ] Verify result in `/data/pending/`
- [ ] Verify webhook delivery
- [ ] Test Celery mode with Flower dashboard

---

## Deployment

### Docker Compose (Async Mode)
```bash
docker-compose up -d
```

### Docker Compose (Celery Mode)
```bash
docker-compose -f docker-compose.celery.yml up -d
```

### Kubernetes
```bash
kubectl apply -f k8s/deployment.yaml
```

---

## Open Design Questions

- [ ] Should bulk ingestion support streaming for large files?
- [ ] Should LPM support PostgreSQL as alternative to SQLite?
- [x] Rate limiting per domain: **Yes, implement**
- [x] Proxy support: **Plain SOCKS + tor-socks-proxy-service**

---

## Approval

- [ ] Reviewed by: [name]
- [ ] Approved on: [date]
- [ ] Notes: [any conditions or clarifications]
