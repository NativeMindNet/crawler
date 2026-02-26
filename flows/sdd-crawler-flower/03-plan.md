# Plan: Flower Real-Time Monitoring Dashboard

**Version:** 1.0
**Status:** PLAN PHASE
**Last Updated:** 2026-02-26

**Specifications:** [02-specifications.md](02-specifications.md)

---

## 1. Implementation Overview

This plan breaks down the Flower monitoring integration into **atomic, testable tasks**. The implementation follows a **layered approach**:

1. **Core Infrastructure** - Redis, Celery event configuration
2. **Flower Service** - Basic Flower deployment
3. **Authentication** - Basic Auth + OAuth
4. **Monitoring Stack** - Prometheus + Grafana (optional)
5. **Production Hardening** - Reverse proxy, HTTPS, scaling

---

## 2. Task Breakdown

### Phase 1: Core Infrastructure (Priority: HIGH)

#### Task 1.1: Update Celery App Configuration
**File:** `celery_app.py`
**Changes:**
```python
# Add Flower event configuration
app.conf.update(
    # ... existing config ...
    
    # Flower monitoring support
    worker_send_task_events=True,
    task_send_sent_events=True,
    event_queue_expires=60.0,
    event_queue_ttl=60.0,
)
```
**Testing:**
- [ ] Celery worker starts without errors
- [ ] Worker sends events (verify via Celery inspect)
- [ ] Events visible in Redis pubsub

**Dependencies:** None
**Estimated Effort:** 30 minutes

---

#### Task 1.2: Update Worker Launch Command
**File:** `dev_run_celery.sh` or worker entrypoint
**Changes:**
```bash
# Add --send-events flag
celery -A celery_app worker \
  --loglevel=info \
  --concurrency=4 \
  --prefetch-multiplier=1 \
  --send-events  # Required for Flower
```
**Testing:**
- [ ] Worker starts with event emission enabled
- [ ] Events visible in Flower (once running)

**Dependencies:** Task 1.1
**Estimated Effort:** 15 minutes

---

#### Task 1.3: Create Docker Compose Base File
**File:** `docker-compose.yml`
**Changes:** Add services:
```yaml
version: '3.8'

services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes

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
      replicas: 3

  flower:
    image: mher/flower:2.0.1
    command: >
      flower
      --app=celery_app
      --broker=redis://redis:6379/0
      --port=5555
      --basic_auth=flower:flower_password
    ports:
      - "5555:5555"
    environment:
      - CELERY_BROKER_URL=redis://redis:6379/0
      - CELERY_APP=celery_app
      - FLOWER_BASIC_AUTH=flower:flower_password
    depends_on:
      - redis
      - worker

volumes:
  redis_data:
```
**Testing:**
- [ ] `docker-compose up` starts all services
- [ ] Redis accessible on port 6379
- [ ] Workers register with broker
- [ ] Flower accessible at http://localhost:5555
- [ ] Flower login works (flower:flower_password)
- [ ] Dashboard shows workers and tasks

**Dependencies:** Task 1.1, Task 1.2
**Estimated Effort:** 1 hour

---

### Phase 2: Flower Configuration (Priority: HIGH)

#### Task 2.1: Create Flower Configuration File
**File:** `flower/flowerconfig.py`
**Content:**
```python
# Flower configuration
broker = "redis://redis:6379/0"
auth = "basic"
auth_option = "flower:flower_password"
prometheus = True
metrics_port = 5556
max_workers = 5000
max_tasks = 10000
state_save_interval = 60000

# Optional: OAuth configuration
# oauth2_key = "GITHUB_CLIENT_ID"
# oauth2_secret = "GITHUB_CLIENT_SECRET"
# oauth2_redirect_uri = "https://flower.example.com/login"
```
**Testing:**
- [ ] Flower loads configuration on startup
- [ ] Settings applied correctly (check Flower logs)

**Dependencies:** Task 1.3
**Estimated Effort:** 30 minutes

---

#### Task 2.2: Update Docker Compose to Use Config
**File:** `docker-compose.yml`
**Changes:**
```yaml
flower:
  volumes:
    - ./flower:/app/flowerconfig
  command: >
    flower
    --conf=/app/flowerconfig/flowerconfig.py
    --port=5555
    --prometheus
    --metrics_port=5556
```
**Testing:**
- [ ] Flower starts with config file
- [ ] Prometheus metrics endpoint accessible at :5556/metrics

**Dependencies:** Task 2.1
**Estimated Effort:** 30 minutes

---

#### Task 2.3: Create Flower Environment File (.env)
**File:** `.env`
**Content:**
```bash
# Flower Authentication
FLOWER_BASIC_AUTH=flower:flower_password

# OAuth (optional, uncomment to enable)
# FLOWER_OAUTH2_KEY=your_github_client_id
# FLOWER_OAUTH2_SECRET=your_github_client_secret
# FLOWER_OAUTH2_REDIRECT_URI=https://flower.example.com/login

# Prometheus
FLOWER_PROMETHEUS=true
FLOWER_METRICS_PORT=5556
```
**Testing:**
- [ ] Environment variables loaded by docker-compose
- [ ] Auth credentials not hardcoded in docker-compose.yml

**Dependencies:** Task 2.1
**Estimated Effort:** 15 minutes

---

### Phase 3: Prometheus Integration (Priority: MEDIUM)

#### Task 3.1: Create Prometheus Configuration
**File:** `prometheus/prometheus.yml`
**Content:**
```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'flower'
    static_configs:
      - targets: ['flower:5556']
    scrape_interval: 15s
    metrics_path: '/metrics'
  
  - job_name: 'redis'
    static_configs:
      - targets: ['redis:6379']
    scrape_interval: 30s
```
**Testing:**
- [ ] Prometheus starts without errors
- [ ] Flower metrics being scraped (check Prometheus UI)
- [ ] Query `flower_events_total` returns data

**Dependencies:** Task 2.2
**Estimated Effort:** 30 minutes

---

#### Task 3.2: Add Prometheus to Docker Compose
**File:** `docker-compose.monitoring.yml` (override file)
**Content:**
```yaml
version: '3.8'

services:
  prometheus:
    image: prom/prometheus:v2.45.0
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--storage.tsdb.retention.time=15d'
    depends_on:
      - flower

volumes:
  prometheus_data:
```
**Testing:**
- [ ] `docker-compose -f docker-compose.yml -f docker-compose.monitoring.yml up`
- [ ] Prometheus accessible at http://localhost:9090
- [ ] Flower metrics visible in Prometheus

**Dependencies:** Task 3.1
**Estimated Effort:** 30 minutes

---

### Phase 4: Grafana Integration (Priority: MEDIUM)

#### Task 4.1: Create Grafana Datasource Configuration
**File:** `grafana/datasources/prometheus.yml`
**Content:**
```yaml
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
    editable: true
```
**Testing:**
- [ ] Grafana auto-configures Prometheus datasource
- [ ] Datasource visible in Grafana UI

**Dependencies:** Task 3.2
**Estimated Effort:** 20 minutes

---

#### Task 4.2: Create Grafana Dashboard
**File:** `grafana/dashboards/flower-overview.json`
**Content:** Pre-built dashboard with panels:
- Task execution rate (tasks/min)
- Success/failure rate over time
- Average task runtime
- Worker count and status
- Queue depth over time
- Task runtime distribution (histogram)

**Testing:**
- [ ] Dashboard auto-imports on Grafana startup
- [ ] All panels display data correctly
- [ ] Time range selectors work (1h, 24h, 7d)

**Dependencies:** Task 4.1
**Estimated Effort:** 1 hour

---

#### Task 4.3: Add Grafana to Docker Compose
**File:** `docker-compose.monitoring.yml`
**Changes:**
```yaml
grafana:
  image: grafana/grafana:10.0.0
  ports:
    - "3000:3000"
  environment:
    - GF_SECURITY_ADMIN_USER=admin
    - GF_SECURITY_ADMIN_PASSWORD=grafana_password
    - GF_INSTALL_PLUGINS=
  volumes:
    - grafana_data:/var/lib/grafana
    - ./grafana/datasources:/etc/grafana/provisioning/datasources
    - ./grafana/dashboards:/etc/grafana/provisioning/dashboards
  depends_on:
    - prometheus
```
**Testing:**
- [ ] Grafana accessible at http://localhost:3000
- [ ] Login works (admin/grafana_password)
- [ ] Dashboard visible and populated

**Dependencies:** Task 4.1, Task 4.2
**Estimated Effort:** 30 minutes

---

### Phase 5: Reverse Proxy (Priority: MEDIUM)

#### Task 5.1: Create nginx Configuration
**File:** `nginx/flower.conf`
**Content:**
```nginx
server {
    listen 80;
    server_name flower.localhost;

    location / {
        proxy_pass http://flower:5555;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";

        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Metrics (internal only)
    location /metrics {
        allow 10.0.0.0/8;
        deny all;
        proxy_pass http://flower:5556;
    }
}
```
**Testing:**
- [ ] nginx starts without config errors
- [ ] Flower accessible via nginx (http://flower.localhost)
- /metrics endpoint restricted

**Dependencies:** Task 1.3
**Estimated Effort:** 45 minutes

---

#### Task 5.2: Add nginx to Docker Compose
**File:** `docker-compose.prod.yml`
**Content:**
```yaml
version: '3.8'

services:
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/flower.conf:/etc/nginx/conf.d/flower.conf
      - ./nginx/ssl:/etc/ssl/certs
    depends_on:
      - flower
```
**Testing:**
- [ ] nginx proxies requests to Flower
- [ ] Real-time updates work (WebSocket)

**Dependencies:** Task 5.1
**Estimated Effort:** 30 minutes

---

### Phase 6: Testing & Validation (Priority: HIGH)

#### Task 6.1: Test Task Monitoring
**Steps:**
1. Start full stack: `docker-compose -f docker-compose.yml -f docker-compose.monitoring.yml up -d`
2. Submit test tasks to Celery
3. Verify in Flower dashboard:
   - [ ] Tasks appear in real-time
   - [ ] Task status updates (PENDING → STARTED → SUCCESS/FAILURE)
   - [ ] Task details show correct args/result
   - [ ] Worker assignment visible

**Dependencies:** Task 1.3, Task 2.2
**Estimated Effort:** 1 hour

---

#### Task 6.2: Test Worker Monitoring
**Steps:**
1. Scale workers: `docker-compose up -d --scale worker=5`
2. Verify in Flower dashboard:
   - [ ] All 5 workers visible
   - [ ] Worker status shows online
   - [ ] Worker stats (tasks completed, uptime)
   - [ ] Scale down to 2 workers, verify offline detection

**Dependencies:** Task 1.3
**Estimated Effort:** 30 minutes

---

#### Task 6.3: Test Task Administration
**Steps:**
1. Submit a long-running task
2. In Flower UI:
   - [ ] Click task to view details
   - [ ] Try "Revoke" action (cancel task)
   - [ ] Submit a task that will fail
   - [ ] Try "Retry" action on failed task
   - [ ] Verify actions logged

**Dependencies:** Task 1.3
**Estimated Effort:** 45 minutes

---

#### Task 6.4: Test Prometheus Metrics
**Steps:**
1. Access Prometheus: http://localhost:9090
2. Run queries:
   - [ ] `flower_events_total` - shows task events
   - [ ] `flower_worker_tasks_total` - shows worker stats
   - [ ] `flower_task_runtime_seconds` - shows runtime distribution
3. Verify metrics update in real-time

**Dependencies:** Task 3.2
**Estimated Effort:** 30 minutes

---

#### Task 6.5: Test Grafana Dashboard
**Steps:**
1. Access Grafana: http://localhost:3000
2. Open "Flower Overview" dashboard
3. Verify:
   - [ ] All panels show data
   - [ ] Time range changes work
   - [ ] Auto-refresh works (every 30s)
   - [ ] Dashboard variables work (filter by worker, task name)

**Dependencies:** Task 4.3
**Estimated Effort:** 30 minutes

---

### Phase 7: Documentation (Priority: MEDIUM)

#### Task 7.1: Update README
**File:** `README.md` or `docs/flower.md`
**Content:**
- Flower overview and purpose
- Quick start (docker-compose commands)
- Access URLs (Flower, Prometheus, Grafana)
- Default credentials
- Troubleshooting guide

**Testing:**
- [ ] Follow README instructions from scratch
- [ ] Verify all steps work for new user

**Dependencies:** Task 6.1-6.5
**Estimated Effort:** 1 hour

---

#### Task 7.2: Create Operations Runbook
**File:** `docs/flower-operations.md`
**Content:**
- Daily operations checklist
- Monitoring what to watch
- Common issues and solutions
- Scaling guidelines
- Backup/recovery procedures

**Testing:**
- [ ] Review with operations team
- [ ] Validate procedures work

**Dependencies:** Task 6.1-6.5
**Estimated Effort:** 1 hour

---

## 3. Task Dependencies

```
Task 1.1: Celery App Config ─┬─> Task 1.2: Worker Launch
                              │
                              └─> Task 1.3: Docker Compose ─┬─> Task 2.1: Flower Config
                                                             │
                                                             ├─> Task 5.1: nginx Config
                                                             │
                                                             └─> Task 2.2: Flower Config Volume
                                                                  │
                                                                  ├─> Task 3.1: Prometheus Config
                                                                  │    │
                                                                  │    └─> Task 3.2: Prometheus Compose
                                                                  │         │
                                                                  │         └─> Task 4.1: Grafana Datasource
                                                                  │              │
                                                                  │              └─> Task 4.2: Grafana Dashboard
                                                                  │                   │
                                                                  │                   └─> Task 4.3: Grafana Compose
                                                                  │
                                                                  └─> Task 6.x: Testing
```

---

## 4. Implementation Order

### Sprint 1: Core Monitoring (Day 1)
1. Task 1.1: Celery App Configuration
2. Task 1.2: Worker Launch Command
3. Task 1.3: Docker Compose Base
4. Task 2.1: Flower Configuration
5. Task 6.1: Test Task Monitoring
6. Task 6.2: Test Worker Monitoring

**Deliverable:** Flower dashboard showing tasks and workers

---

### Sprint 2: Enhanced Monitoring (Day 2)
1. Task 2.2: Docker Compose Config Volume
2. Task 2.3: Environment File
3. Task 3.1: Prometheus Configuration
4. Task 3.2: Prometheus Docker Compose
5. Task 6.4: Test Prometheus Metrics

**Deliverable:** Prometheus metrics scraping working

---

### Sprint 3: Grafana & Production (Day 3)
1. Task 4.1: Grafana Datasource
2. Task 4.2: Grafana Dashboard
3. Task 4.3: Grafana Docker Compose
4. Task 6.5: Test Grafana Dashboard
5. Task 5.1: nginx Configuration
6. Task 5.2: nginx Docker Compose

**Deliverable:** Full monitoring stack with Grafana

---

### Sprint 4: Testing & Documentation (Day 4)
1. Task 6.3: Test Task Administration
2. Task 7.1: Update README
3. Task 7.2: Operations Runbook
4. Final validation and bug fixes

**Deliverable:** Production-ready Flower monitoring

---

## 5. Risk Assessment

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Celery events overhead | Medium | Low | Enable only when Flower deployed |
| Redis memory usage | Medium | Medium | Configure event TTL, monitor memory |
| Flower performance at scale | Low | Low | Set max_workers/max_tasks limits |
| OAuth complexity | Low | Medium | Start with Basic Auth, add OAuth later |
| WebSocket proxy issues | Medium | Low | Test nginx config thoroughly |

---

## 6. Acceptance Criteria

### Must Pass Before "Complete":

1. **Given** docker-compose stack is running
   **When** I access http://localhost:5555
   **Then** I see Flower dashboard with workers and tasks

2. **Given** a task is submitted
   **When** I view the task list
   **Then** I see real-time status updates

3. **Given** Prometheus is running
   **When** I query `flower_events_total`
   **Then** I get task event metrics

4. **Given** Grafana is running
   **When** I open the dashboard
   **Then** all panels show data

---

## Approval

- [ ] Reviewed by: [name]
- [ ] Approved on: [date]
- [ ] Notes: [any conditions or clarifications]
