# Specifications: Universal Single-Platform Crawler

**Version:** 1.0
**Status:** SPECIFICATIONS PHASE
**Last Updated:** 2026-02-26

**Requirements:** [01-requirements.md](01-requirements.md)

---

## 1. Architecture Overview

The crawler is a **single-platform, Docker-native service** that combines scraping, parsing, bulk ingestion, and imagery extraction into a unified engine.

```
┌─────────────────────────────────────────────────────────────────┐
│                    External Ecosystem                           │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │   CLI       │  │  HTTP API    │  │  Webhook Listener    │  │
│  │  Commands   │  │  Endpoints   │  │  (optional callback) │  │
│  └──────┬──────┘  └──────┬───────┘  └──────────────────────┘  │
└─────────┼────────────────┼─────────────────────────────────────┘
          │                │
          ▼                ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Crawler Instance (Docker)                     │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              API/CLI Interface Layer                      │  │
│  │  - FastAPI REST API                                       │  │
│  │  - Typer CLI                                              │  │
│  │  - Webhook Client                                         │  │
│  └──────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              Core Engine                                  │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐  │  │
│  │  │   Scraper   │  │   Parser    │  │  Bulk Ingestion │  │  │
│  │  │  (Selenium) │  │  (Beautiful │  │  (CSV/GIS/JSON) │  │  │
│  │  │             │  │   Soup)     │  │                 │  │  │
│  │  └─────────────┘  └─────────────┘  └─────────────────┘  │  │
│  │  ┌─────────────┐  ┌─────────────┐                        │  │
│  │  │  Imagery    │  │  Discovery  │                        │  │
│  │  │  Service    │  │  (Ripple)   │                        │  │
│  │  └─────────────┘  └─────────────┘                        │  │
│  └──────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              Local Persistence Manager (LPM)              │  │
│  │  - SQLite: Task queue, state tracking, priorities         │  │
│  │  - File System: HTML, PDF, images, JSON results           │  │
│  │  - State Files: msgpack/pickle/JSON for bulk ingestion    │  │
│  └──────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              Platform Configuration                       │  │
│  │  - selectors.json: CSS/XPath selectors                    │  │
│  │  - mapping.json: Data field mapping                       │  │
│  │  - discovery.json: Navigation rules                       │  │
│  │  - business_rules.json: Validation, transforms            │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Docker Volume Mounts                         │
│  /data/results/    - Parsed JSON, metadata                      │
│  /data/raw/        - HTML, PDF, images                          │
│  /data/state/      - SQLite DB, ingestion state                 │
│  /config/          - Platform configuration (read-only)         │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. Component Specifications

### 2.1 Interface Layer

#### 2.1.1 FastAPI REST API

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check, queue depth |
| `/tasks` | POST | Submit single URL task |
| `/tasks/bulk` | POST | Submit multiple URLs |
| `/tasks/{task_id}` | GET | Get task status |
| `/tasks/{task_id}/result` | GET | Get task result |
| `/scrape` | POST | Scrape + parse in one call |
| `/bulk/ingest` | POST | Start bulk ingestion (CSV/GIS/JSON) |
| `/bulk/{job_id}` | GET | Get bulk job status |
| `/webhooks/test` | POST | Test webhook endpoint |

#### 2.1.2 CLI Commands (Typer)

```bash
# Single operations
crawler scrape <url>                    # Scrape + parse single URL
crawler scrape --url <url> --output <path>

# Task queue operations
crawler task add <url>                  # Add to queue
crawler task status <task_id>           # Check status
crawler task list                       # List all tasks

# Bulk operations
crawler bulk ingest <file> --profile <name>  # Import CSV/GIS/JSON
crawler bulk status <job_id>                 # Check job status

# Worker operations
crawler worker run                      # Start processing queue
crawler worker resume                   # Resume from checkpoint
crawler worker drain                    # Process all pending tasks

# Config operations
crawler config validate <platform>      # Validate platform config
crawler config list                     # List available platforms
```

#### 2.1.3 Webhook Client

```python
class WebhookClient:
    def send_task_completed(task_id: str, result: dict, raw_paths: dict)
    def send_bulk_completed(job_id: str, stats: dict)
    def send_error(task_id: str, error: str)
```

**Payload Schema:**
```json
{
  "event": "task.completed",
  "task_id": "uuid",
  "platform": "qpublic",
  "timestamp": "2026-02-26T10:00:00Z",
  "result": {
    "parcel_id": "...",
    "owner": "...",
    "data": {...}
  },
  "raw_paths": {
    "html": "/data/raw/qpublic/abc123.html",
    "images": ["/data/raw/qpublic/abc123_img1.jpg"]
  },
  "signature": "hmac-sha256:..."
}
```

---

### 2.2 Core Engine

#### 2.2.1 Scraper

```python
class Scraper:
    def __init__(self, config: PlatformConfig, display: Display)
    
    async def fetch(self, url: str) -> ScrapedContent:
        """Fetch URL, handle anti-bot, return HTML + metadata"""
    
    async def fetch_with_discovery(self, url: str) -> ScrapedContent:
        """Fetch + extract discovered URLs from page"""
```

**Features:**
- SeleniumBase integration (UC mode for anti-bot)
- sbvirtualdisplay for headless operation
- Retry logic with exponential backoff
- Screenshot capture on error
- Raw HTML saved to `/data/raw/{platform}/{id}.html`

#### 2.2.2 Parser

```python
class Parser:
    def __init__(self, config: PlatformConfig)
    
    def parse(self, html: str) -> ParsedResult:
        """Parse HTML using selectors.json, apply mapping.json"""
    
    def extract_images(self, soup: BeautifulSoup) -> list[str]:
        """Extract property image URLs (from sdd-crawler-photos)"""
```

**Features:**
- Config-driven selectors (CSS/XPath)
- Data transformation via mapping.json
- Image extraction (unified from sdd-crawler-photos)
- External link generation (Google Maps, Street View, Satellite)
- Output: Structured JSON to `/data/results/{platform}/{id}.json`

#### 2.2.3 BulkIngestionPipeline

```python
class BulkIngestionPipeline:
    def __init__(self, config: PlatformConfig, lpm: LocalPersistenceManager)
    
    async def ingest(self, file_path: str, profile: MappingProfile) -> str:
        """Start ingestion job, return job_id"""
    
    async def resume(self, job_id: str) -> str:
        """Resume interrupted job"""
    
    def get_status(self, job_id: str) -> IngestionStatus:
        """Get job progress and stats"""
```

**Features:**
- Source readers: CSV, Excel, GIS (Shapefile/GeoJSON), JSON/JSONL
- Streaming for large files (>1GB)
- Mapping profiles for column transformation
- State tracking: msgpack (index), pickle (complex), JSON (manifest)
- Idempotent upsert (parcel_id + county + state)

#### 2.2.4 ImageryService

```python
class ImageryService:
    def enrich_with_external_links(self, coords: tuple) -> ExternalLinks:
        """Generate Google Maps, Street View, Satellite, Bing links"""
    
    async def download_images(self, urls: list[str], output_dir: str) -> list[str]:
        """Download images, return local paths"""
    
    def extract_from_html(self, soup: BeautifulSoup, platform: str) -> list[str]:
        """Extract image URLs from HTML (filter icons/logos)"""
```

**Features:**
- External link generation (from sdd-crawler-photos)
- Image download with deduplication
- YOLOv8 placeholder for condition analysis

#### 2.2.5 DiscoveryEngine (Ripple Effect)

```python
class DiscoveryEngine:
    def __init__(self, config: PlatformConfig, lpm: LocalPersistenceManager)
    
    def process_discovered_links(self, source_task_id: str, links: list[DiscoveredLink]):
        """Add discovered URLs to queue with priority adjustment"""
```

**Features:**
- Extract links from parsed data (`discovered_links` field)
- Auto-add to local queue (from sdd-crawler-standalone)
- Priority adjustment based on relationship type
- Prevent duplicates

---

### 2.3 Local Persistence Manager (LPM)

```python
class LocalPersistenceManager:
    def __init__(self, db_path: str, data_dir: str)
    
    # Task Queue
    def add_task(self, task: Task) -> str
    def get_next_pending_task(self) -> Task | None
    def complete_task(self, task_id: str, result: dict)
    def fail_task(self, task_id: str, error: str)
    
    # Bulk Ingestion State
    def create_ingestion_job(self, job: IngestionJob) -> str
    def update_ingestion_progress(self, job_id: str, processed: int, total: int)
    def save_ingestion_state(self, job_id: str, state: bytes, format: str)
    
    # Results
    def save_result(self, task_id: str, data: dict, raw_paths: dict)
    def get_result(self, task_id: str) -> dict | None
    
    # Priority Queue
    def recalculate_priorities(self, delta: dict[str, int])
```

**SQLite Schema:**
```sql
CREATE TABLE tasks (
    id TEXT PRIMARY KEY,
    url TEXT NOT NULL,
    platform TEXT NOT NULL,
    status TEXT NOT NULL,  -- pending, processing, completed, failed
    priority INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    result_path TEXT,
    error TEXT,
    retry_count INTEGER DEFAULT 0,
    discovered_links_count INTEGER DEFAULT 0
);

CREATE TABLE bulk_jobs (
    id TEXT PRIMARY KEY,
    source_file TEXT NOT NULL,
    profile_id TEXT NOT NULL,
    status TEXT NOT NULL,  -- pending, processing, completed, failed
    total_rows INTEGER,
    processed_rows INTEGER DEFAULT 0,
    error_rows INTEGER DEFAULT 0,
    state_manifest_path TEXT,
    state_index_path TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);

CREATE TABLE discovered_links (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_task_id TEXT NOT NULL,
    url TEXT NOT NULL,
    relationship_type TEXT,  -- owner, county, parcel, etc.
    priority_delta INTEGER DEFAULT 0,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed BOOLEAN DEFAULT FALSE
);

CREATE INDEX idx_tasks_status_priority ON tasks(status, priority DESC);
CREATE INDEX idx_discovered_links_source ON discovered_links(source_task_id);
```

---

### 2.4 Platform Configuration

**Directory Structure:**
```
/config/{platform}/
├── selectors.json      # CSS/XPath selectors for parsing
├── mapping.json        # Field mapping and transforms
├── discovery.json      # Navigation and link discovery rules
├── business_rules.json # Validation, constraints
├── schedule.json       # (optional) Cron schedule for periodic crawling
└── manifest.json       # Platform metadata
```

**selectors.json Schema:**
```json
{
  "platform": "qpublic",
  "version": "1.0",
  "selectors": {
    "parcel_id": {"selector": "#_lblParcelID", "type": "css"},
    "owner": {"selector": "#ctlBodyPane_ctl01_ctl00_lblName", "type": "css"},
    "site_address": {"selector": "#InfoPane2_lnkWebsite", "type": "css", "attr": "href"},
    "legal_description": {"selector": "#_lblLegalDescription", "type": "css"},
    "tax_amount": {"selector": ".value-column", "type": "css", "index": 2}
  },
  "discovery": {
    "county_links": {"selector": ".county-option", "type": "css", "attr": "href"},
    "parcel_links": {"selector": "[id*='_lnkParcelID']", "type": "css", "attr": "href"},
    "owner_links": {"selector": ".owner-name", "type": "css", "attr": "href"}
  }
}
```

**mapping.json Schema:**
```json
{
  "platform": "qpublic",
  "fields": {
    "parcel_id": {"source": "parcel_id", "transform": "clean_parcel_id"},
    "owner_name": {"source": "owner", "transform": "normalize_name"},
    "tax_amount": {"source": "tax_amount", "transform": "to_decimal"},
    "county": {"const": "Columbia"},
    "state": {"const": "FL"}
  },
  "required": ["parcel_id", "county", "state"]
}
```

---

### 2.5 Data Models

```python
@dataclass
class Task:
    id: str
    url: str
    platform: str
    status: str  # pending, processing, completed, failed
    priority: int = 0
    created_at: datetime = None
    retry_count: int = 0

@dataclass
class ScrapedContent:
    html: str
    url: str
    screenshot: bytes | None = None
    discovered_urls: list[str] = None
    metadata: dict = None

@dataclass
class ParsedResult:
    task_id: str
    platform: str
    parcel_id: str
    data: dict  # Mapped fields
    image_urls: list[str]
    external_links: dict  # Google Maps, etc.
    discovered_links: list[DiscoveredLink]

@dataclass
class DiscoveredLink:
    url: str
    relationship_type: str  # owner, county, parcel, etc.
    priority_delta: int = 0
    source_task_id: str

@dataclass
class IngestionJob:
    id: str
    source_file: str
    profile_id: str
    status: str
    total_rows: int = 0
    processed_rows: int = 0
    error_rows: int = 0
    state: dict = None

@dataclass
class MappingProfile:
    profile_name: str
    source_format: str
    mappings: dict  # source_col -> target_field
    transformations: dict
    required_fields: list[str]
```

---

## 3. Integration Points

### 3.1 External Ecosystem

| Integration | Direction | Description |
|-------------|-----------|-------------|
| **HTTP API** | Inbound | Task submission, status queries |
| **Webhooks** | Outbound | Task completion notifications |
| **Docker Volumes** | Both | Results, raw files, state |
| **Platform Configs** | Inbound | Read-only config from host |

### 3.2 Optional: Gateway API Sync

```python
class GatewaySync:
    def __init__(self, gateway_url: str, api_key: str)
    
    async def submit_results(self, results: list[ParsedResult])
    async def get_work(self) -> list[Task]  # For on-demand mode
    async def send_heartbeat(self, queue_depth: int)
```

**Note:** Gateway sync is **optional**. Crawler operates standalone by default.

---

## 4. Edge Cases & Error Handling

### 4.1 Scraping Failures

| Error | Handling |
|-------|----------|
| Anti-bot detected | Retry with longer delay, different user agent |
| Timeout | Retry 3x with exponential backoff |
| Cloudflare challenge | Screenshot + log error, mark as failed |
| Invalid URL | Skip, log error, webhook with error |

### 4.2 Parsing Failures

| Error | Handling |
|-------|----------|
| Selector not found | Log warning, use None for field, continue |
| Required field missing | Mark as failed, save partial result |
| Invalid data format | Log error, use raw value, continue |

### 4.3 Bulk Ingestion Failures

| Error | Handling |
|-------|----------|
| File not found | Return error immediately |
| Invalid format | Return error with details |
| Row transformation error | Log to errors.jsonl, continue |
| Duplicate key | Upsert (update existing) |
| Disk full | Pause, send webhook, retry later |

### 4.4 Webhook Failures

| Error | Handling |
|-------|----------|
| Endpoint unreachable | Retry 3x with exponential backoff |
| Invalid response | Log error, continue |
| Timeout | Retry once, then skip |

---

## 5. Docker Configuration

### 5.1 Dockerfile

```dockerfile
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    xvfb \
    libnss3 \
    libatk-bridge2.0-0 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create volume mount points
RUN mkdir -p /data/results /data/raw /data/state /config

EXPOSE 8000

ENTRYPOINT ["python", "-m", "crawler"]
CMD ["worker", "run"]
```

### 5.2 Docker Compose

```yaml
version: '3.8'

services:
  crawler-qpublic:
    build: .
    container_name: crawler-qpublic
    volumes:
      - ./platforms/qpublic:/config:ro
      - ./data/qpublic/results:/data/results
      - ./data/qpublic/raw:/data/raw
      - ./data/qpublic/state:/data/state
    environment:
      - PLATFORM=qpublic
      - WEBHOOK_URL=http://gateway/api/webhooks
      - WEBHOOK_SECRET=${WEBHOOK_SECRET}
    ports:
      - "8001:8000"
    command: worker run

  crawler-beacon:
    build: .
    container_name: crawler-beacon
    volumes:
      - ./platforms/beacon:/config:ro
      - ./data/beacon/results:/data/results
      - ./data/beacon/raw:/data/raw
      - ./data/beacon/state:/data/state
    environment:
      - PLATFORM=beacon
    ports:
      - "8002:8000"
    command: worker run
```

---

## 6. Open Questions (Resolved)

| Question | Decision |
|----------|----------|
| **Q1 - API Design** | FastAPI (modern, async, auto-docs) |
| **Q2 - Webhook Security** | HMAC-SHA256 signatures |
| **Q3 - Priority Model** | API-specified + config default + discovery delta |
| **Q4 - Rate Limiting** | Per-platform config (requests/minute) |
| **Q5 - Bulk vs Real-time** | Both: CLI for one-off, API endpoint for integration |

---

## Next Phase

After specs are approved, move to **PLAN** phase to define:
- Atomic implementation tasks
- File structure and changes
- Testing strategy
- Dependencies and estimates
