# Specifications: Flower Real-Time Monitoring Dashboard

**Version:** 1.0
**Status:** SPECIFICATIONS PHASE
**Last Updated:** 2026-02-26

**Requirements:** [01-requirements.md](01-requirements.md)

---

## 1. Architecture Overview

Flower integrates with the Celery-based crawler deployment as a **separate monitoring service** that connects to the same Redis broker as the workers.

```
┌─────────────────────────────────────────────────────────────────┐
│                    Celery Cluster (Docker)                      │
│                                                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │
│  │   Worker 1  │  │   Worker 2  │  │   Worker N  │            │
│  │  (crawler)  │  │  (crawler)  │  │  (crawler)  │            │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘            │
│         │                │                │                     │
│         └────────────────┼────────────────┘                     │
│                          │                                      │
│                          ▼                                      │
│                 ┌─────────────────┐                            │
│                 │  Redis Broker   │                            │
│                 │  (task queue)   │                            │
│                 └────────┬────────┘                            │
│                          │                                      │
│         ┌────────────────┼────────────────┐                    │
│         │                │                │                     │
│         ▼                ▼                ▼                     │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │
│  │   Flower    │  │  Prometheus │  │   Grafana   │            │
│  │  (port 5555)│  │  (port 9090)│  │  (port 3000)│            │
│  │  Dashboard  │  │   Metrics   │  │   Visual    │            │
│  └─────────────┘  └─────────────┘  └─────────────┘            │
└─────────────────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Operator Access                              │
│                                                                 │
│  ┌─────────────────────┐    ┌─────────────────────┐           │
│  │  Browser: 5555      │    │  Grafana: 3000      │           │
│  │  - Task monitoring  │    │  - Custom dashboards│           │
│  │  - Worker status    │    │  - Historical data  │           │
│  │  - Task admin       │    │  - Alerting rules   │           │
│  └─────────────────────┘    └─────────────────────┘           │
└─────────────────────────────────────────────────────────────────┘
```

### Key Components:

| Component | Purpose | Port | Required |
|-----------|---------|------|----------|
| **Flower** | Real-time Celery monitoring | 5555 | Yes (Celery mode) |
| **Redis** | Task queue + event broker | 6379 | Yes |
| **Prometheus** | Metrics scraping + storage | 9090 | Optional |
| **Grafana** | Custom dashboards + alerting | 3000 | Optional |

---

## 2. Component Specifications

### 2.1 Flower Service

```python
# Flower configuration (flowerconfig.py)
broker = "redis://redis:6379/0"
auth = "basic"  # or "oauth"
auth_option = "flower:flower_password"  # Basic auth credentials
prometheus = True
metrics_port = 5556
max_workers = 5000  # Max workers to display
max_tasks = 10000  # Max tasks to keep in history
state_save_interval = 60000  # Save state every 60s
```

**Docker Command:**
```bash
flower \
  --app=celery_app:app \
  --broker=redis://redis:6379/0 \
  --port=5555 \
  --basic_auth=flower:flower_password \
  --prometheus \
  --metrics_port=5556
```

**Features:**
- Real-time task monitoring via Celery events
- Worker status dashboard
- Task administration (retry, revoke, terminate)
- Performance statistics (1h, 24h, 7d)
- Prometheus metrics export
- REST API for programmatic access

---

### 2.2 Celery Event Configuration

Celery workers **must** emit events for Flower to monitor tasks:

```python
# celery_app.py
from celery import Celery

app = Celery('app', broker='redis://localhost:6379/0')

app.conf.update(
    timezone='Europe/Moscow',
    enable_utc=True,
    result_backend='redis://localhost:6379/0',
    result_expires=3600 * 24 * 30,
    task_annotations={'*': {'rate_limit': '5/m'}},
    
    # Flower Event Configuration (REQUIRED)
    worker_send_task_events=True,      # Worker sends task events
    task_send_sent_events=True,        # Task sends sent events
    event_queue_expires=60.0,          # Event queue TTL
    event_queue_ttl=60.0,              # Event message TTL
)
```

**Worker Launch Command:**
```bash
celery -A celery_app worker \
  --loglevel=info \
  --concurrency=4 \
  --prefetch-multiplier=1 \
  --send-events  # Required for Flower
```

---

### 2.3 Authentication Configuration

#### Option A: HTTP Basic Auth (MVP)

```bash
# Environment variable
FLOWER_BASIC_AUTH=flower:flower_password

# Or command line
flower --basic_auth=flower:flower_password
```

**Format:** `username:password` (multiple users separated by comma)

#### Option B: OAuth 2.0

```python
# flowerconfig.py
auth = "oauth"
oauth2_key = "GITHUB_CLIENT_ID"
oauth2_secret = "GITHUB_CLIENT_SECRET"
oauth2_redirect_uri = "https://flower.example.com/login"
oauth2_no_verify = False  # Set True for self-signed certs

# OAuth state encryption
oauth2_state_secret = "random_secret_key_for_encryption"
```

**Supported Providers:**
- Google
- GitHub
- GitLab
- Okta

---

### 2.4 Prometheus Integration

**Flower Metrics Endpoint:**
```
GET http://flower:5556/metrics
```

**Sample Metrics:**
```prometheus
# Task metrics
flower_events_total{type="task-sent", name="tasks.scrape_url"} 1542
flower_events_total{type="task-started", name="tasks.scrape_url"} 1540
flower_events_total{type="task-succeeded", name="tasks.scrape_url"} 1520
flower_events_total{type="task-failed", name="tasks.scrape_url"} 20

# Worker metrics
flower_worker_tasks_total{worker="worker1@hostname"} 5420
flower_worker_status{worker="worker1@hostname"} 1  # 1=online, 0=offline

# Runtime metrics
flower_task_runtime_seconds_sum{name="tasks.scrape_url"} 45230.5
flower_task_runtime_seconds_count{name="tasks.scrape_url"} 1520
flower_task_runtime_seconds_bucket{name="tasks.scrape_url",le="10.0"} 850
flower_task_runtime_seconds_bucket{name="tasks.scrape_url",le="30.0"} 1420
```

**Prometheus Configuration:**
```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'flower'
    static_configs:
      - targets: ['flower:5556']
    scrape_interval: 15s
    metrics_path: '/metrics'
```

---

### 2.5 Docker Compose Configuration

```yaml
version: '3.8'

services:
  # Redis Broker
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes

  # Celery Workers
  worker:
    build: .
    command: >
      celery -A celery_app worker
      --loglevel=info
      --concurrency=4
      --send-events
    environment:
      - CELERY_BROKER_URL=redis://redis:6379/0
      - CELERY_RESULT_BACKEND=redis://redis:6379/0
    volumes:
      - ./platforms:/app/platforms
      - ./data:/data
    depends_on:
      - redis
    deploy:
      replicas: 3  # Scale workers as needed

  # Flower Monitoring
  flower:
    image: mher/flower:2.0.1
    command: >
      flower
      --app=celery_app
      --broker=redis://redis:6379/0
      --port=5555
      --basic_auth=flower:flower_password
      --prometheus
      --metrics_port=5556
    ports:
      - "5555:5555"  # Dashboard
      - "5556:5556"  # Prometheus metrics
    environment:
      - CELERY_BROKER_URL=redis://redis:6379/0
      - CELERY_APP=celery_app
      - FLOWER_BASIC_AUTH=flower:flower_password
    volumes:
      - ./flower:/app/flowerconfig  # Optional: custom config
    depends_on:
      - redis
      - worker

  # Prometheus (Optional)
  prometheus:
    image: prom/prometheus:v2.45.0
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--storage.tsdb.retention.time=15d'
    depends_on:
      - flower

  # Grafana (Optional)
  grafana:
    image: grafana/grafana:10.0.0
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_USER=admin
      - GF_SECURITY_ADMIN_PASSWORD=grafana_password
    volumes:
      - grafana_data:/var/lib/grafana
      - ./grafana/dashboards:/etc/grafana/provisioning/dashboards
      - ./grafana/datasources:/etc/grafana/provisioning/datasources
    depends_on:
      - prometheus

volumes:
  redis_data:
  prometheus_data:
  grafana_data:
```

---

### 2.6 Reverse Proxy Configuration (nginx)

For production deployments, Flower should be behind a reverse proxy:

```nginx
# /etc/nginx/conf.d/flower.conf
server {
    listen 80;
    server_name flower.example.com;

    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name flower.example.com;

    ssl_certificate /etc/ssl/certs/flower.crt;
    ssl_certificate_key /etc/ssl/private/flower.key;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    location / {
        proxy_pass http://flower:5555;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket support (for real-time updates)
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";

        # Timeout settings
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Prometheus metrics (internal only)
    location /metrics {
        allow 10.0.0.0/8;  # Internal network only
        deny all;
        proxy_pass http://flower:5556;
    }
}
```

---

## 3. Data Models

### 3.1 Task Event Schema (Celery → Flower)

```python
@dataclass
class TaskEvent:
    """Celery task event sent to Flower"""
    uuid: str              # Task ID
    name: str              # Task name (e.g., "tasks.scrape_url")
    state: str             # PENDING, STARTED, SUCCESS, FAILURE
    args: tuple            # Task arguments
    kwargs: dict           # Task keyword arguments
    result: Any            # Task result (on success)
    traceback: str         # Error traceback (on failure)
    runtime: float         # Execution time in seconds
    timestamp: datetime    # Event timestamp
    worker: str            # Worker hostname
    retry: int             # Retry count
    root_id: str           # Root task ID (for chains)
    parent_id: str         # Parent task ID (for chains)
```

### 3.2 Worker Status Schema

```python
@dataclass
class WorkerStatus:
    """Worker status information"""
    hostname: str          # Worker hostname
    pid: int               # Process ID
    concurrency: int       # Pool size
    prefetch_multiplier: int  # Prefetch limit
    status: str            # online, offline
    tasks_completed: int   # Total tasks completed
    tasks_failed: int      # Total tasks failed
    uptime: timedelta      # Time since start
    pool: str              # Pool type (prefork, threads, etc.)
    active_tasks: int      # Currently executing tasks
    scheduled_tasks: int   # Scheduled tasks count
    reserved_tasks: int    # Reserved tasks count
```

### 3.3 Task Statistics Schema

```python
@dataclass
class TaskStatistics:
    """Task performance statistics"""
    task_name: str
    time_range: str        # 1h, 24h, 7d
    total_tasks: int       # Total tasks in range
    succeeded: int         # Successful tasks
    failed: int            # Failed tasks
    success_rate: float    # Percentage (0-100)
    avg_runtime: float     # Average execution time (seconds)
    median_runtime: float  # Median execution time
    min_runtime: float     # Minimum execution time
    max_runtime: float     # Maximum execution time
    runtime_distribution: dict  # Histogram buckets
```

---

## 4. API Specifications

### 4.1 Flower REST API

Flower exposes a REST API for programmatic access:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/workers` | GET | List all workers with stats |
| `/api/tasks` | GET | List tasks (with filters) |
| `/api/task/info/<task_id>` | GET | Get task details |
| `/api/task/async-inspect/<task_id>` | GET | Inspect running task |
| `/api/task/revoke/<task_id>` | POST | Revoke/cancel task |
| `/api/task/terminate/<task_id>` | POST | Terminate running task |
| `/api/task/rate-limit/<task_name>` | POST | Set task rate limit |
| `/api/task/timeout/<task_name>` | POST | Set task timeout |
| `/api/task/retry/<task_id>` | POST | Retry failed task |
| `/api/config` | GET | Get Celery configuration |
| `/api/stats` | GET | Get task statistics |

**Example: Get Task Info**
```bash
curl -u flower:flower_password \
  http://localhost:5555/api/task/info/abc123-def456
```

**Response:**
```json
{
  "uuid": "abc123-def456",
  "name": "tasks.scrape_url",
  "state": "SUCCESS",
  "args": ["https://example.com"],
  "kwargs": {},
  "result": {"html": "...", "status": 200},
  "runtime": 2.34,
  "timestamp": 1708956000.123,
  "worker": "worker1@hostname",
  "retries": 0
}
```

---

## 5. Edge Cases & Error Handling

### 5.1 Flower Startup Failures

| Error | Handling |
|-------|----------|
| Redis connection failed | Retry with exponential backoff (5s, 10s, 20s) |
| Celery app not found | Log error, exit with code 1 |
| Port already in use | Log error, exit with code 1 |
| Invalid auth config | Log error, fall back to no auth (warning) |

### 5.2 Task Monitoring Issues

| Error | Handling |
|-------|----------|
| Task event lost | Flower shows gap in history (limitation) |
| Worker disconnects | Mark worker offline after 30s timeout |
| Task stuck in STARTED | Show as running until timeout (configurable) |
| Result backend unavailable | Show task status, hide result |

### 5.3 Performance Considerations

| Scenario | Mitigation |
|----------|------------|
| High task volume (>10k/hour) | Increase `max_tasks` limit, add memory |
| Many workers (>100) | Set `max_workers` limit, use filtering |
| Long task history | Configure `state_save_interval`, use external logging |
| Event queue overflow | Increase Redis memory, reduce event TTL |

---

## 6. Security Specifications

### 6.1 Authentication Flow

```
┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
│  User    │     │  nginx   │     │  Flower  │     │  OAuth   │
│  Browser │     │  Proxy   │     │  Server  │     │ Provider │
└────┬─────┘     └────┬─────┘     └────┬─────┘     └────┬─────┘
     │                │                │                │
     │  1. Access     │                │                │
     │     /          │                │                │
     ├───────────────>│                │                │
     │                │                │                │
     │                │  2. Forward    │                │
     │                │     request    │                │
     │                ├───────────────>│                │
     │                │                │                │
     │                │                │  3. Redirect   │
     │                │                │     to OAuth   │
     │<─────────────────────────────────────────────────│
     │                │                │                │
     │  4. Login      │                │                │
     ├─────────────────────────────────────────────────>│
     │                │                │                │
     │                │                │  5. Callback   │
     │<─────────────────────────────────────────────────│
     │                │                │                │
     │  6. Access     │                │                │
     │     with       │                │                │
     │     session    │                │                │
     ├───────────────>│                │                │
     │                │                │                │
     │                │  7. Validate   │                │
     │                │     session    │                │
     │                ├───────────────>│                │
     │                │                │                │
     │                │  8. Dashboard  │                │
     │<────────────────────────────────│                │
     │                │                │                │
```

### 6.2 HTTPS Requirements

- **Production**: HTTPS required (no HTTP)
- **Certificate**: Valid SSL/TLS certificate (Let's Encrypt or commercial)
- **TLS Version**: TLS 1.2 minimum, TLS 1.3 preferred
- **Cipher Suites**: Strong ciphers only (no RC4, DES, 3DES)

### 6.3 Session Management

- **Session Timeout**: 30 minutes of inactivity
- **Session Storage**: Server-side (Redis or memory)
- **Session ID**: Secure random token (256-bit)
- **Cookie Flags**: Secure, HttpOnly, SameSite=Strict

---

## 7. Deployment Specifications

### 7.1 Development Deployment

```bash
# Start Redis
docker run -d --name redis -p 6379:6379 redis:7-alpine

# Start Celery worker
celery -A celery_app worker --loglevel=info --send-events

# Start Flower (in separate terminal)
flower --app=celery_app --broker=redis://localhost:6379/0 --port=5555

# Access: http://localhost:5555
```

### 7.2 Production Deployment

```bash
# Docker Compose (production-ready)
docker-compose -f docker-compose.prod.yml up -d

# Health check
curl -u flower:flower_password http://localhost:5555/healthcheck

# View logs
docker-compose logs -f flower
```

### 7.3 Scaling Considerations

| Component | Scale Strategy |
|-----------|----------------|
| **Workers** | Scale horizontally based on queue depth |
| **Flower** | Single instance (stateless, can HA with load balancer) |
| **Redis** | Sentinel for HA, Cluster for sharding |
| **Prometheus** | Single instance (federate for multi-region) |
| **Grafana** | Scale horizontally (shared database) |

---

## 8. Integration with Existing SDD Flows

### 8.1 sdd-crawler-celery Integration

Flower is the **primary monitoring interface** for `sdd-crawler-celery`:

| Feature | Integration Point |
|---------|-------------------|
| Task Chains | Show chain execution flow (parent-child relationships) |
| Task Groups | Show group progress (completed/total) |
| Periodic Tasks | Show scheduled tasks (Celery Beat integration) |
| Rate Limiting | Display rate limit status per task type |
| Result Backend | Show task results from Redis |

### 8.2 Platform-Specific Monitoring

Flower displays platform-specific task names:

```
tasks.qpublic_scrape_counties_urls
tasks.qpublic_get_all_parcels_urls
tasks.qpublic_single_url_chain
tasks.scrape_url
tasks.save_html
tasks.parse_html
tasks.import_to_db
```

**Filtering by Platform:**
```
/tasks?name=qpublic  # Show only QPublic tasks
```

---

## 9. Open Questions (Resolved)

| Question | Decision |
|----------|----------|
| **Q1 - Authentication** | Basic Auth for MVP, OAuth optional |
| **Q2 - OAuth Provider** | GitHub (most common for self-hosted) |
| **Q3 - Port Exposure** | Internal only (reverse proxy required in prod) |
| **Q4 - Prometheus** | Optional but recommended (included in docker-compose) |
| **Q5 - Custom Views** | Use Flower default views (no custom tabs for MVP) |
| **Q6 - Alerting** | Flower displays metrics only; alerting via Prometheus/Grafana |
| **Q7 - Persistence** | In-memory (session-based); external logging for audit trail |

---

## Next Phase

After specs are approved, move to **PLAN** phase to define:
- Atomic implementation tasks
- Docker Compose file creation
- Configuration files (Flower, Prometheus, Grafana)
- Testing strategy (local dev, staging, production)
- Documentation updates

---

## Approval

- [ ] Reviewed by: [name]
- [ ] Approved on: [date]
- [ ] Notes: [any conditions or clarifications]
