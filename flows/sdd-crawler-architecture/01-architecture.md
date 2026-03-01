# Architecture: Universal Single-Platform Crawler

**Version:** 3.0
**Status:** ARCHITECTURE DOCUMENT
**Last Updated:** 2026-03-01
**Scope:** Universal crawler architecture - one instance per platform, orchestrated externally.

---

## 1. Executive Summary

The **Universal Crawler** is a stateless, single-platform data collection system. Each instance handles **ONE platform** (e.g., Beacon, QPublic). Multiple instances can be deployed externally to cover multiple platforms. The design is **not specific to tax-lien data** - it can be configured for any web scraping domain.

### Architectural Pivot (from v1.0)

| Old Design (taxlien-parser) | New Design (Universal Crawler) |
|----------------------------|-------------------------------|
| Multi-platform in one codebase | Single-platform per instance |
| Tax-lien specific | Domain-agnostic |
| Platform code embedded | Platform configs as JSON |
| Celery-only workers | **Celery-only (simplified)** |
| Complex strategy mix | External orchestration |

### Key Architectural Principles

| Principle | Description |
|-----------|-------------|
| **Single-Platform Focus** | Each instance handles ONE platform, simplifying logic |
| **External Orchestration** | Multi-platform coordination happens OUTSIDE the crawler |
| **Config-Driven** | Platform behavior defined in JSON configs, not code |
| **Docker-First** | Containerized with volume mounts for results |
| **Dual Interface** | Both API (FastAPI) and CLI (Typer) access |
| **Celery + Flower** | Distributed task queue with real-time monitoring |
| **Local Persistence** | LPM (SQLite + files) for resilience and resume capability |

---

## 2. High-Level Architecture

```
+===================================================================================+
|                           EXTERNAL ORCHESTRATION LAYER                            |
+===================================================================================+
|                                                                                   |
|   +-------------------+     +-------------------+     +-------------------+       |
|   |   Gateway API     |     |   Scheduler       |     |   Task Manager    |       |
|   | (api.taxlien...)  |     | (cron/airflow)    |     | (external system) |       |
|   +--------+----------+     +--------+----------+     +--------+----------+       |
|            |                         |                         |                  |
|            +-------------------------+-------------------------+                  |
|                                      |                                            |
|                          Spawn/Configure Instances                                |
|                                      |                                            |
+===================================================================================+
                                       |
                                       v
+===================================================================================+
|                              CRAWLER INSTANCES                                     |
|                      (Each handles ONE platform)                                   |
+===================================================================================+
|                                                                                   |
|  +------------------------+  +------------------------+  +------------------------+
|  |   CRAWLER INSTANCE 1   |  |   CRAWLER INSTANCE 2   |  |   CRAWLER INSTANCE N   |
|  |   Platform: beacon     |  |   Platform: qpublic    |  |   Platform: custom     |
|  +------------------------+  +------------------------+  +------------------------+
|  |                        |  |                        |  |                        |
|  | +--------------------+ |  | +--------------------+ |  | +--------------------+ |
|  | |  Platform Config   | |  | |  Platform Config   | |  | |  Platform Config   | |
|  | | - selectors.json   | |  | | - selectors.json   | |  | | - selectors.json   | |
|  | | - mapping.json     | |  | | - mapping.json     | |  | | - mapping.json     | |
|  | | - discovery.json   | |  | | - discovery.json   | |  | | - discovery.json   | |
|  | +--------------------+ |  | +--------------------+ |  | +--------------------+ |
|  |                        |  |                        |  |                        |
|  | +--------------------+ |  | +--------------------+ |  | +--------------------+ |
|  | |   SCRAPER MODULE   | |  | |   SCRAPER MODULE   | |  | |   SCRAPER MODULE   | |
|  | | - SeleniumBase     | |  | | - SeleniumBase     | |  | | - SeleniumBase     | |
|  | | - Anti-bot handler | |  | | - Anti-bot handler | |  | | - Anti-bot handler | |
|  | | - Retry logic      | |  | | - Retry logic      | |  | | - Retry logic      | |
|  | +--------------------+ |  | +--------------------+ |  | +--------------------+ |
|  |                        |  |                        |  |                        |
|  | +--------------------+ |  | +--------------------+ |  | +--------------------+ |
|  | |   PARSER MODULE    | |  | |   PARSER MODULE    | |  | |   PARSER MODULE    | |
|  | | - Selector engine  | |  | | - Selector engine  | |  | | - Selector engine  | |
|  | | - Transformer      | |  | | - Transformer      | |  | | - Transformer      | |
|  | | - Image extractor  | |  | | - Image extractor  | |  | | - Image extractor  | |
|  | +--------------------+ |  | +--------------------+ |  | +--------------------+ |
|  |                        |  |                        |  |                        |
|  | +--------------------+ |  | +--------------------+ |  | +--------------------+ |
|  | |  LOCAL PERSISTENCE | |  | |  LOCAL PERSISTENCE | |  | |  LOCAL PERSISTENCE | |
|  | | - SQLite (tasks)   | |  | | - SQLite (tasks)   | |  | | - SQLite (tasks)   | |
|  | | - Files (HTML,IMG) | |  | | - Files (HTML,IMG) | |  | | - Files (HTML,IMG) | |
|  | +--------------------+ |  | +--------------------+ |  | +--------------------+ |
|  |                        |  |                        |  |                        |
|  | +--------------------+ |  | +--------------------+ |  | +--------------------+ |
|  | |  API (FastAPI)     | |  | |  API (FastAPI)     | |  | |  API (FastAPI)     | |
|  | |  CLI (Typer)       | |  | |  CLI (Typer)       | |  | |  CLI (Typer)       | |
|  | +--------------------+ |  | +--------------------+ |  | +--------------------+ |
|  |                        |  |                        |  |                        |
|  +------------------------+  +------------------------+  +------------------------+
|            |                          |                          |                |
|            |  Webhook Notifications   |                          |                |
|            +-------------+------------+--------------------------+                |
|                          |                                                        |
+===================================================================================+
                           |
                           v
+===================================================================================+
|                              RESULTS STORAGE                                       |
+===================================================================================+
|                                                                                   |
|   +-------------------+     +-------------------+     +-------------------+       |
|   |  Volume Mount     |     |  S3/MinIO         |     |   Gateway API     |       |
|   |  /data/results    |     |  (archive)        |     |   (sync)          |       |
|   +-------------------+     +-------------------+     +-------------------+       |
|                                                                                   |
+===================================================================================+
```

---

## 3. Component Catalog

### 3.1 Crawler Instance Components

| Component | Purpose | Technology |
|-----------|---------|------------|
| **Config Loader** | Load platform JSON configs | Python dataclasses |
| **Scraper** | Fetch HTML from websites | SeleniumBase (undetected) |
| **Parser** | Extract data from HTML | BeautifulSoup + CSS selectors |
| **LPM** | Task queue + result storage | SQLite + filesystem |
| **Worker** | Process task queue | Async Python loop |
| **API** | HTTP interface | FastAPI |
| **CLI** | Command-line interface | Typer |
| **Webhook Client** | Notify external systems | HMAC-signed HTTP |

### 3.2 Platform Configuration Files

```
config/platforms/{platform_name}/
├── manifest.json       # Platform metadata, rate limits
├── selectors.json      # CSS/XPath selectors for data extraction
├── mapping.json        # Field mapping to output schema
├── discovery.json      # URL patterns for link discovery
├── business_rules.json # Data normalization rules
├── schedule.json       # Crawl frequency settings
└── counties.json       # (Optional) County-specific overrides
```

### 3.3 Execution Modes

| Mode | Description | Use Case |
|------|-------------|----------|
| **API Mode** | HTTP endpoints for task management | Production, external integration |
| **CLI Mode** | Command-line task execution | Development, debugging, `celery call` |
| **Worker Mode** | Continuous queue processing | Background crawling |
| **Drain Mode** | Process queue until empty | Batch jobs |

### 3.4 Worker Architecture (Celery + Flower)

The crawler uses **Celery** for distributed task execution with **Flower** for real-time monitoring.

```
┌─────────────────────────────────────────────────────────────────────┐
│                         CRAWLER INSTANCE                             │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐             │
│  │   Worker 1  │    │   Worker 2  │    │   Worker N  │             │
│  │  (scrape)   │    │  (scrape)   │    │  (scrape)   │             │
│  └──────┬──────┘    └──────┬──────┘    └──────┬──────┘             │
│         │                  │                  │                     │
│         └──────────────────┼──────────────────┘                     │
│                            │                                        │
│                            ▼                                        │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                       Redis Broker                           │   │
│  │  Queues: urgent | high | default | low                       │   │
│  │  Rate Limiting: per-task annotations                         │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                            │                                        │
│         ┌──────────────────┼──────────────────┐                     │
│         ▼                  ▼                  ▼                     │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────────────┐     │
│  │   Celery    │    │   Flower    │    │      LPM            │     │
│  │    Beat     │    │   (:5555)   │    │   (SQLite+Files)    │     │
│  │ (Scheduler) │    │ Monitoring  │    │   Local Persist     │     │
│  └─────────────┘    └─────────────┘    └─────────────────────┘     │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

#### Component Responsibilities

| Component | Purpose |
|-----------|---------|
| **Celery Workers** | Execute scrape/parse tasks in parallel |
| **Redis Broker** | Task queue with priority support (4 queues) |
| **Celery Beat** | Periodic tasks (Gateway sync, cleanup, scheduled crawls) |
| **Flower** | Real-time monitoring, retry, revoke, metrics |
| **LPM** | Local persistence (SQLite + files) for resilience |

#### Priority Queues

| Queue | Priority | Use Case |
|-------|----------|----------|
| `urgent` | 1 (highest) | Auction-imminent tasks |
| `high` | 2 | Delinquent properties |
| `default` | 3 | Normal crawling |
| `low` | 4 | Background maintenance |

#### Flower Dashboard Features

- Real-time task monitoring (live progress)
- Worker status and health indicators
- Task retry/revoke with one click
- Prometheus metrics export (`/metrics`)
- Task history and statistics
- Rate limiting visibility

#### Starting the Stack

```bash
docker-compose up -d
# Starts: crawler-api, redis, celery-worker, celery-beat, flower
```

---

## 4. Data Flow

### 4.1 Single Task Flow

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│                              SINGLE TASK DATA FLOW                                │
└──────────────────────────────────────────────────────────────────────────────────┘

    ┌─────────────┐         ┌─────────────┐         ┌─────────────┐
    │   External  │         │   Crawler   │         │   Website   │
    │   System    │         │  Instance   │         │  (Platform) │
    └──────┬──────┘         └──────┬──────┘         └──────┬──────┘
           │                       │                       │
           │  1. POST /tasks       │                       │
           │   {url, priority}     │                       │
           │──────────────────────>│                       │
           │                       │                       │
           │  2. Task queued       │                       │
           │<──────────────────────│                       │
           │                       │                       │
           │                       │  3. HTTP GET (with    │
           │                       │     anti-bot bypass)  │
           │                       │──────────────────────>│
           │                       │                       │
           │                       │  4. HTML Response     │
           │                       │<──────────────────────│
           │                       │                       │
           │                       │  5. Parse HTML        │
           │                       │  (selectors.json)     │
           │                       │                       │
           │                       │  6. Transform data    │
           │                       │  (mapping.json)       │
           │                       │                       │
           │                       │  7. Save to LPM       │
           │                       │  - result.json        │
           │                       │  - raw.html           │
           │                       │  - images/*.jpg       │
           │                       │                       │
           │  8. Webhook: task.completed                   │
           │<──────────────────────│                       │
           │  {task_id, result}    │                       │
           │                       │                       │
    ┌──────┴──────┐         ┌──────┴──────┐         ┌──────┴──────┐
    │   External  │         │   Crawler   │         │   Website   │
    │   System    │         │  Instance   │         │  (Platform) │
    └─────────────┘         └─────────────┘         └─────────────┘
```

### 4.2 Bulk Ingestion Flow

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│                              BULK INGESTION FLOW                                  │
└──────────────────────────────────────────────────────────────────────────────────┘

    Source Files                    Pipeline                      Output
    ============                    ========                      ======

    +-------------+                                         +-------------+
    | parcels.csv |                                         |   LPM DB    |
    +------+------+                                         +------+------+
           │                                                       │
           │  ┌────────────────────────────────────────────────────┼─┐
           │  │                 BULK PIPELINE                      │ │
           │  │                                                    │ │
           ▼  │  ┌──────────┐  ┌──────────┐  ┌──────────┐         │ │
    [CSV Reader]─>│Transform │─>│ Validate │─>│  Upsert  │─────────┼─┘
           │  │  │(mapping) │  │  (rules) │  │  (dedup) │         │
           │  │  └──────────┘  └──────────┘  └──────────┘         │
           │  │                                                    │
    +-------------+                                                │
    | shapes.shp  |                                         +------▼------+
    +------+------+                                         | Discovered  |
           │  │                                             |   Tasks     |
           ▼  │                                             +------+------+
    [GIS Reader]─>│                                                │
           │  │                                                    ▼
           │  │                                             Queue for
    +-------------+                                         Scraping
    | data.json   |
    +------+------+
           │  │
           ▼  │
    [JSON Reader]─>│
              │
              └────────────────────────────────────────────────────────┘
```

---

## 5. Module Structure

```
crawler/
├── __init__.py
├── __main__.py              # Entry point
├── config_loader.py         # Platform config loading
├── config_validator.py      # Config schema validation
├── lpm.py                   # Local Persistence Manager
├── storage.py               # File storage utilities
├── state.py                 # State serialization (checkpoint)
├── worker.py                # Task processing worker
├── discovery.py             # Link discovery engine
├── priority.py              # Priority calculation
├── gateway_sync.py          # Gateway synchronization
│
├── models/                  # Data models
│   ├── task.py
│   ├── bulk_job.py
│   ├── scraped_content.py
│   ├── parsed_result.py
│   ├── mapping_profile.py
│   └── external_links.py
│
├── repositories/            # Database access
│   ├── task_repo.py
│   ├── bulk_job_repo.py
│   └── link_repo.py
│
├── db/                      # Database layer
│   ├── connection.py
│   └── schema.py
│
├── scraper/                 # Web scraping
│   ├── browser.py           # SeleniumBase wrapper
│   ├── anti_bot.py          # Challenge handlers
│   ├── retry.py             # Retry with backoff
│   ├── screenshots.py       # Error screenshots
│   └── scraper.py           # Main scraper class
│
├── parser/                  # HTML parsing
│   ├── selector_engine.py   # CSS/XPath engine
│   ├── transformer.py       # Data transformation
│   ├── validator.py         # Schema validation
│   ├── parser.py            # Main parser class
│   ├── image_extractor.py   # Property images
│   └── external_links.py    # Map link generation
│
├── bulk/                    # Bulk ingestion
│   ├── readers/
│   │   ├── csv_reader.py
│   │   ├── excel_reader.py
│   │   ├── gis_reader.py
│   │   └── json_reader.py
│   ├── pipeline.py
│   ├── transformer.py
│   ├── state.py
│   └── upsert.py
│
├── imagery/                 # Image processing
│   ├── link_generator.py    # External map links
│   ├── downloader.py        # Image download
│   ├── service.py           # Imagery coordination
│   └── analyzer.py          # YOLOv8 placeholder
│
├── api/                     # FastAPI layer
│   ├── app.py
│   ├── schemas.py
│   ├── middleware.py
│   └── routes/
│       ├── health.py
│       ├── tasks.py
│       ├── scrape.py
│       ├── bulk.py
│       ├── config.py
│       └── webhooks.py
│
├── cli/                     # Typer CLI
│   └── commands/
│       ├── scrape.py
│       ├── task.py
│       ├── bulk.py
│       ├── worker.py
│       └── config.py
│
├── webhooks/                # Webhook notifications
│   ├── models.py
│   ├── signer.py            # HMAC signing
│   └── client.py
│
└── tests/
    ├── conftest.py
    ├── test_lpm.py
    ├── test_parser.py
    ├── test_worker.py
    ├── test_discovery.py
    └── test_imagery_service.py
```

---

## 6. Deployment Options

### 6.1 Docker Compose (Single Platform)

```yaml
version: '3.8'
services:
  crawler:
    image: taxlien-crawler:latest
    environment:
      - PLATFORM=beacon
      - CONFIG_DIR=/config
      - DATA_DIR=/data
      - WEBHOOK_URL=https://api.example.com/webhook
    volumes:
      - ./config/platforms/beacon:/config:ro
      - ./data/beacon:/data
    ports:
      - "8000:8000"
```

### 6.2 Multi-Platform (Multiple Instances)

```yaml
version: '3.8'
services:
  crawler-beacon:
    image: taxlien-crawler:latest
    environment:
      - PLATFORM=beacon
    volumes:
      - ./config/platforms/beacon:/config:ro
      - ./data/beacon:/data
    ports:
      - "8001:8000"

  crawler-qpublic:
    image: taxlien-crawler:latest
    environment:
      - PLATFORM=qpublic
    volumes:
      - ./config/platforms/qpublic:/config:ro
      - ./data/qpublic:/data
    ports:
      - "8002:8000"

  crawler-floridatax:
    image: taxlien-crawler:latest
    environment:
      - PLATFORM=floridatax
    volumes:
      - ./config/platforms/floridatax:/config:ro
      - ./data/floridatax:/data
    ports:
      - "8003:8000"
```

### 6.3 Kubernetes Deployment

**Key Principle:** Crawler is **platform-agnostic**. It doesn't know it's "beacon" or "qpublic". Platform identity is defined externally via:
- K8s labels (for service discovery)
- Volume subPath (for storage isolation)
- Config mount (for platform-specific selectors)

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: crawler-beacon
  labels:
    app: crawler
    platform: beacon
spec:
  replicas: 1                    # One instance per platform
  selector:
    matchLabels:
      app: crawler
      platform: beacon
  template:
    metadata:
      labels:
        app: crawler
        platform: beacon
    spec:
      containers:
      - name: crawler
        image: crawler:latest
        ports:
        - containerPort: 8000
        volumeMounts:
        - name: data
          mountPath: /data
          subPath: beacon        # Platform isolation via subPath
        - name: config
          mountPath: /config
          readOnly: true
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "2000m"
      volumes:
      - name: data
        persistentVolumeClaim:
          claimName: crawler-data-pvc
      - name: config
        configMap:
          name: crawler-beacon-config
---
apiVersion: v1
kind: Service
metadata:
  name: crawler-beacon
  labels:
    app: crawler
    platform: beacon
spec:
  selector:
    app: crawler
    platform: beacon
  ports:
  - port: 8000
    targetPort: 8000
```

**Service Discovery:** External systems discover crawlers via K8s API:
```python
# label_selector="app=crawler"
# Returns all crawler services with their platform labels
```

---

## 7. Storage Architecture (Platform-Agnostic)

### 7.1 Core Principle

**Crawler does NOT know about platforms.** It simply writes to `/data`. Platform isolation is achieved externally via volume mounts.

### 7.2 Internal Structure (What Crawler Sees)

```
/data/                    # Crawler's view - just /data
├── lpm.db               # Local Persistence Manager (SQLite)
├── pending/             # Results ready for consumption
│   └── {task_id}.json
├── raw/                 # HTML archive (optional)
│   └── {task_id}.html.gz
└── images/
    └── {task_id}/
```

### 7.3 External Mapping (Volume Mounts)

**Docker Compose:**
```yaml
services:
  crawler-beacon:
    volumes:
      - ./data/beacon:/data      # Externally mapped to beacon/

  crawler-qpublic:
    volumes:
      - ./data/qpublic:/data     # Externally mapped to qpublic/
```

**Kubernetes (subPath):**
```yaml
volumeMounts:
  - name: crawler-data
    mountPath: /data
    subPath: beacon              # Platform determined by subPath
```

### 7.4 Result Structure on Shared Storage

```
/mnt/crawler-data/               # Shared PersistentVolume
├── beacon/
│   ├── lpm.db
│   ├── pending/
│   │   └── {task_id}.json
│   ├── raw/
│   └── images/
├── qpublic/
│   └── ...
└── tyler/
    └── ...
```

### 7.5 Consumer Contract

External systems (taxlien-parser) consume results by:
1. Reading `{platform}/pending/*.json`
2. Processing and moving/deleting files
3. Optionally archiving `{platform}/raw/*.html.gz`

This design enables:
- **OSS standalone use:** User mounts local folder, gets results in `pending/`
- **Production integration:** Parser reads from shared volume
- **Platform isolation:** Each crawler writes to isolated subPath

---

## 8. API Reference

### 8.1 Task Management

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/tasks` | POST | Create new scrape task |
| `/tasks` | GET | List all tasks |
| `/tasks/{id}` | GET | Get task status |
| `/tasks/{id}/result` | GET | Get task result |

### 8.2 Scraping

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/scrape` | POST | Immediate scrape (sync) |
| `/scrape/batch` | POST | Batch scrape tasks |

### 8.3 Bulk Operations

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/bulk/import` | POST | Start bulk import job |
| `/bulk/jobs` | GET | List bulk jobs |
| `/bulk/jobs/{id}` | GET | Get job status |

### 8.4 Health & Config

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/config` | GET | Current config |
| `/config/selectors` | GET | Selector definitions |

---

## 9. Comparison: Old vs New

| Aspect | Old (taxlien-parser) | New (Universal Crawler) |
|--------|---------------------|------------------------|
| **Scope** | 27+ platforms in one codebase | 1 platform per instance |
| **Domain** | Tax-lien specific | Any web data |
| **Worker** | Celery only | **Celery + Flower** |
| **Orchestration** | Internal strategy mixer | External (Gateway/Scheduler) |
| **Platform code** | Python classes | JSON configs |
| **Scaling** | Celery worker count | Container instances × Celery workers |
| **Complexity** | High (multi-platform logic) | Low (single focus) |
| **Testability** | Difficult (coupled platforms) | Easy (isolated instances) |
| **Monitoring** | Custom code | **Flower dashboard** |
| **Dependencies** | Redis | Redis + Flower |

---

## 10. Next Steps

1. **Complete Testing** - Run full test suite
2. **Docker Build** - Build and push image
3. **Sample Deployment** - Deploy for beacon platform
4. **K8s Integration** - Deploy with labels for service discovery
5. **Documentation** - API docs, deployment guide

---

**Document Status:** DRAFTED v3.0
**Last Updated:** 2026-03-01
**Author:** Claude (v3.0: Celery-only architecture, removed async mode, added Flower integration)
