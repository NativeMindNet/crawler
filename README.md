# Universal Single-Platform Crawler

**Production-ready web crawler for single-platform instances with API, CLI, and Docker support.**

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
│  │  - FastAPI REST API (port 8000)                          │  │
│  │  - Typer CLI                                             │  │
│  │  - Webhook Client (HMAC-SHA256)                          │  │
│  └──────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              Core Engine                                  │  │
│  │  Scraper │ Parser │ Bulk │ Discovery │ Worker            │  │
│  └──────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │         Local Persistence (SQLite + Filesystem)           │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Table of Contents

- [Quick Start](#quick-start)
- [Architecture](#architecture)
- [API Reference](#api-reference)
- [CLI Reference](#cli-reference)
- [Docker Deployment](#docker-deployment)
- [Webhook Integration](#webhook-integration)
- [Platform Configuration](#platform-configuration)
- [Bulk Ingestion](#bulk-ingestion)
- [Integration Examples](#integration-examples)
- [Troubleshooting](#troubleshooting)

---

## Quick Start

### Option 1: Docker (Recommended)

```bash
# Clone and setup
git clone <repository>
cd crawler
mkdir -p data/qpublic/{results,raw,state}

# Run single-platform instance
docker run -d \
  --name crawler-qpublic \
  -v $(pwd)/config/platforms/qpublic:/config:ro \
  -v $(pwd)/data/qpublic:/data \
  -e PLATFORM=qpublic \
  -e WEBHOOK_URL=http://your-gateway/api/webhooks \
  -p 8001:8000 \
  crawler:latest

# Test health
curl http://localhost:8001/health
```

### Option 2: Local Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment
export CONFIG_DIR=./config
export DATA_DIR=./data
export DB_PATH=./data/state/crawler.db

# Run API server
python -m crawler api serve --host 0.0.0.0 --port 8000

# Or run worker
python -m crawler worker run --platform qpublic
```

### Option 3: Docker Compose (Multi-Platform)

```bash
# Edit docker-compose.yml for your platforms
docker-compose up -d

# Check status
docker-compose ps
```

---

## Architecture

### Components

| Component | Description | Interface |
|-----------|-------------|-----------|
| **Scraper** | SeleniumBase browser automation, anti-bot handling | `scraper.fetch(url)` |
| **Parser** | Config-driven data extraction, validation | `parser.parse(html)` |
| **Worker** | Queue processor with checkpoint resume | `worker.run()` |
| **Discovery** | Ripple effect - auto-queue discovered links | Internal |
| **Bulk** | CSV/GIS/Excel/JSON ingestion pipeline | `pipeline.ingest(file)` |
| **API** | FastAPI REST endpoints | HTTP/JSON |
| **CLI** | Typer command-line interface | Shell commands |
| **Webhooks** | HMAC-signed notifications | HTTP POST |

### Data Flow

```
1. Task Submission
   API/CLI → Task Queue (SQLite) → Worker

2. Scraping
   Worker → Scraper → Raw HTML (/data/raw/{platform}/{id}.html)

3. Parsing
   Scraper → Parser → Structured JSON (/data/results/{platform}/{id}.json)

4. Discovery
   Parser → DiscoveryEngine → New Tasks (auto-queued)

5. Notification
   Task Complete → WebhookClient → External Gateway
```

### File Structure

```
crawler/
├── __main__.py              # Entry point
├── api/                     # FastAPI layer
│   ├── app.py
│   ├── routes/
│   └── schemas.py
├── bulk/                    # Bulk ingestion
│   ├── readers/             # CSV, Excel, GIS, JSON
│   ├── pipeline.py
│   └── transformer.py
├── cli/                     # Typer CLI
│   └── commands/
├── db/                      # Database layer
│   ├── schema.sql
│   └── connection.py
├── models/                  # Data models
├── parser/                  # Parsing engine
│   ├── selector_engine.py
│   ├── transformer.py
│   └── image_extractor.py
├── repositories/            # Data access
├── scraper/                 # Scraping engine
│   ├── browser.py           # SeleniumBase wrapper
│   ├── anti_bot.py
│   └── scraper.py
├── webhooks/                # Webhook client
│   ├── client.py
│   └── signer.py
└── worker.py                # Queue processor

config/platforms/{platform}/
├── selectors.json           # CSS/XPath selectors
├── mapping.json             # Field mappings
├── discovery.json           # Link discovery rules
└── manifest.json            # Platform metadata

data/
├── results/{platform}/      # Parsed JSON results
├── raw/{platform}/          # Raw HTML, screenshots, images
└── state/                   # SQLite DB, checkpoints
```

---

## API Reference

**Base URL:** `http://localhost:8000`

### Health Check

```bash
GET /health
```

```json
{
  "status": "healthy",
  "platform": "qpublic",
  "queue_depth": 15,
  "timestamp": "2026-02-26T10:00:00Z"
}
```

### Tasks

```bash
# Create task
POST /tasks
Content-Type: application/json

{
  "url": "https://example.com/parcel/123",
  "platform": "qpublic",
  "priority": 5
}

# Get task status
GET /tasks/{task_id}

# List tasks
GET /tasks?platform=qpublic&status=pending&limit=100

# Delete task
DELETE /tasks/{task_id}
```

**Task Response:**
```json
{
  "id": "uuid",
  "url": "https://...",
  "platform": "qpublic",
  "status": "pending|processing|completed|failed",
  "priority": 5,
  "created_at": "2026-02-26T10:00:00Z",
  "result_path": "/data/results/qpublic/abc123.json",
  "error": null
}
```

### Scrape (Synchronous)

```bash
POST /scrape
Content-Type: application/json

{
  "url": "https://example.com/parcel/123",
  "platform": "qpublic",
  "parse": true,
  "priority": 0
}
```

**Response:**
```json
{
  "task_id": "uuid",
  "status": "completed",
  "parcel_id": "123-456",
  "data": {
    "parcel_id": "123-456",
    "owner": "John Doe",
    "address": "123 Main St"
  },
  "image_urls": ["https://..."],
  "external_links": {
    "google_maps": "https://...",
    "google_street_view": "https://..."
  },
  "raw_paths": {
    "html": "/data/raw/qpublic/abc123.html"
  }
}
```

### Bulk Ingestion

```bash
# Start ingestion
POST /bulk/ingest
Content-Type: application/json

{
  "file_path": "/data/imports/parcels.csv",
  "profile": "default",
  "platform": "qpublic"
}

# Get job status
GET /bulk/{job_id}
```

**Job Status Response:**
```json
{
  "id": "job-uuid",
  "source_file": "/data/imports/parcels.csv",
  "profile_id": "default",
  "status": "processing",
  "total_rows": 10000,
  "processed_rows": 5432,
  "error_rows": 12,
  "progress_percent": 54.32,
  "created_at": "2026-02-26T10:00:00Z"
}
```

### Configuration

```bash
# List platforms
GET /config

# Get platform config
GET /config/{platform}

# Validate config
POST /config/{platform}/validate
```

### Webhooks

```bash
# Test webhook endpoint
POST /webhooks/test
Content-Type: application/json

{
  "url": "http://your-gateway/api/webhooks",
  "secret": "your-hmac-secret"
}

# Receive incoming webhook (gateway sync)
POST /webhooks/receive
```

---

## CLI Reference

```bash
# Single scrape operation
python -m crawler scrape <url> --platform qpublic --output result.json

# Task management
python -m crawler task add <url> --platform qpublic --priority 5
python -m crawler task status <task_id>
python -m crawler task list --platform qpublic --status pending

# Worker operations
python -m crawler worker run --platform qpublic
python -m crawler worker resume --platform qpublic
python -m crawler worker drain --platform qpublic  # Process all and exit

# Bulk ingestion
python -m crawler bulk ingest parcels.csv --profile default --platform qpublic
python -m crawler bulk status <job_id>

# Configuration
python -m crawler config list
python -m crawler config validate qpublic

# Health check
python -m crawler health --api-url http://localhost:8000
```

---

## Docker Deployment

### Single Platform Instance

```yaml
# docker-compose.yml
services:
  crawler-qpublic:
    image: crawler:latest
    container_name: crawler-qpublic
    volumes:
      - ./config/platforms/qpublic:/config:ro
      - ./data/qpublic/results:/data/results
      - ./data/qpublic/raw:/data/raw
      - ./data/qpublic/state:/data/state
    environment:
      - PLATFORM=qpublic
      - WEBHOOK_URL=http://gateway:8080/webhooks
      - WEBHOOK_SECRET=${WEBHOOK_SECRET}
      - LOG_LEVEL=INFO
      - MAX_RETRIES=3
    ports:
      - "8001:8000"
    command: worker run
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

### Multi-Platform Deployment

```yaml
# Run multiple independent instances
services:
  crawler-qpublic:
    # ... config for QPublic
    ports:
      - "8001:8000"

  crawler-beacon:
    # ... config for Beacon
    ports:
      - "8002:8000"

  crawler-florida:
    # ... config for FloridaTax
    ports:
      - "8003:8000"
```

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `PLATFORM` | Platform name | - | Yes |
| `WEBHOOK_URL` | Webhook callback URL | - | No |
| `WEBHOOK_SECRET` | HMAC signing secret | - | No |
| `CONFIG_DIR` | Config directory | `/config` | No |
| `DATA_DIR` | Data directory | `/data` | No |
| `DB_PATH` | SQLite database path | `/data/state/crawler.db` | No |
| `LOG_LEVEL` | Logging level | `INFO` | No |
| `MAX_RETRIES` | Max retry attempts | `3` | No |
| `CHECKPOINT_INTERVAL` | Checkpoint frequency | `10` | No |

### Volume Mounts

| Mount | Purpose | Read/Write |
|-------|---------|------------|
| `/config` | Platform configurations | Read-only |
| `/data/results` | Parsed JSON results | Read-Write |
| `/data/raw` | Raw HTML, screenshots | Read-Write |
| `/data/state` | SQLite DB, checkpoints | Read-Write |

---

## Webhook Integration

### Payload Format

**Task Completed:**
```json
{
  "event": "task.completed",
  "task_id": "uuid",
  "platform": "qpublic",
  "timestamp": "2026-02-26T10:00:00Z",
  "result": {
    "parcel_id": "123-456",
    "owner": "John Doe",
    "data": {...}
  },
  "raw_paths": {
    "html": "/data/raw/qpublic/abc123.html",
    "images": ["/data/raw/qpublic/abc123_img1.jpg"]
  },
  "signature": "sha256:abc123..."
}
```

**Task Failed:**
```json
{
  "event": "task.failed",
  "task_id": "uuid",
  "platform": "qpublic",
  "timestamp": "2026-02-26T10:00:00Z",
  "error": "Timeout fetching URL"
}
```

**Bulk Completed:**
```json
{
  "event": "bulk.completed",
  "job_id": "job-uuid",
  "platform": "qpublic",
  "timestamp": "2026-02-26T10:00:00Z",
  "stats": {
    "total_rows": 10000,
    "processed_rows": 9988,
    "error_rows": 12
  }
}
```

### Signature Verification

```python
import hmac
import hashlib
import json

def verify_webhook(payload: dict, signature: str, secret: str) -> bool:
    """Verify HMAC-SHA256 signature."""
    payload_json = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    expected = hmac.new(
        secret.encode("utf-8"),
        payload_json.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    
    signature_value = signature.replace("sha256=", "")
    return hmac.compare_digest(expected, signature_value)
```

### Gateway Integration

```python
# Example: Receive tasks from gateway
POST /webhooks/receive
Content-Type: application/json
X-Webhook-Signature: sha256:...

{
  "event": "task.create",
  "url": "https://example.com/parcel/123",
  "platform": "qpublic",
  "priority": 5
}
```

---

## Platform Configuration

### Configuration Structure

```
config/platforms/{platform}/
├── selectors.json      # CSS/XPath selectors
├── mapping.json        # Field mappings & transforms
├── discovery.json      # Link discovery rules
├── business_rules.json # Validation rules
├── schedule.json       # Optional cron schedule
└── manifest.json       # Platform metadata
```

### selectors.json

```json
{
  "platform": "qpublic",
  "version": "1.0",
  "selectors": {
    "parcel_id": {
      "selector": "#_lblParcelID",
      "type": "css"
    },
    "owner": {
      "selector": "#ctlBodyPane_ctl01_ctl00_lblName",
      "type": "css"
    },
    "site_address": {
      "selector": "#InfoPane2_lnkWebsite",
      "type": "css",
      "attr": "href"
    },
    "tax_amount": {
      "selector": ".value-column",
      "type": "css",
      "index": 2
    }
  },
  "discovery": {
    "county_links": {
      "selector": ".county-option",
      "type": "css",
      "attr": "href"
    },
    "parcel_links": {
      "selector": "[id*='_lnkParcelID']",
      "type": "css",
      "attr": "href"
    }
  }
}
```

### mapping.json

```json
{
  "platform": "qpublic",
  "fields": {
    "parcel_id": {
      "source": "parcel_id",
      "transform": "clean_parcel_id"
    },
    "owner_name": {
      "source": "owner",
      "transform": "normalize_name"
    },
    "tax_amount": {
      "source": "tax_amount",
      "transform": "to_decimal"
    },
    "county": {
      "const": "Columbia"
    },
    "state": {
      "const": "FL"
    }
  },
  "required": ["parcel_id", "county", "state"]
}
```

### Built-in Transforms

| Transform | Description |
|-----------|-------------|
| `clean_parcel_id` | Remove special chars, standardize |
| `normalize_name` | Format owner name (title case) |
| `to_decimal` | Convert to float |
| `to_integer` | Convert to int |
| `to_date` | Parse date string |
| `uppercase` / `lowercase` | Case conversion |
| `trim` | Remove whitespace |
| `regex_extract` | Extract with regex |

---

## Bulk Ingestion

### Supported Formats

| Format | Extension | Reader |
|--------|-----------|--------|
| CSV | `.csv` | CSVReader |
| Excel | `.xlsx`, `.xls` | ExcelReader |
| GeoJSON | `.geojson`, `.json` | JSONReader |
| Shapefile | `.shp` | GISReader (geopandas) |
| JSON/JSONL | `.json`, `.jsonl` | JSONReader |

### Mapping Profiles

```python
# Example: Define mapping profile
profile = {
    "profile_name": "default",
    "source_format": "csv",
    "mappings": {
        "PARCEL_ID": "parcel_id",
        "OWNER_NAME": "owner_name",
        "SITE_ADDR": "site_address"
    },
    "transformations": {
        "parcel_id": "clean_parcel_id",
        "owner_name": "normalize_name"
    },
    "required_fields": ["parcel_id"],
    "idempotent_key": ["parcel_id", "county", "state"]
}
```

### Resumable Ingestion

```bash
# Start ingestion
curl -X POST http://localhost:8000/bulk/ingest \
  -H "Content-Type: application/json" \
  -d '{"file_path": "/data/parcels.csv", "profile": "default", "platform": "qpublic"}'

# Check progress
curl http://localhost:8000/bulk/{job_id}

# State is automatically saved for resume
```

---

## Integration Examples

### Python Client

```python
import httpx
from typing import Optional, Dict, Any

class CrawlerClient:
    def __init__(self, base_url: str, api_key: Optional[str] = None):
        self.base_url = base_url
        self.api_key = api_key
    
    async def scrape(self, url: str, platform: str) -> Dict[str, Any]:
        """Scrape and parse a single URL."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/scrape",
                json={"url": url, "platform": platform},
                headers={"Authorization": f"Bearer {self.api_key}"} if self.api_key else {},
            )
            response.raise_for_status()
            return response.json()
    
    async def submit_task(self, url: str, platform: str, priority: int = 0) -> str:
        """Submit task to queue."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/tasks",
                json={"url": url, "platform": platform, "priority": priority},
            )
            response.raise_for_status()
            data = response.json()
            return data["id"]
    
    async def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """Get task status."""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.base_url}/tasks/{task_id}")
            response.raise_for_status()
            return response.json()
    
    async def wait_for_task(self, task_id: str, timeout: int = 300) -> Dict[str, Any]:
        """Wait for task completion."""
        import asyncio
        start = asyncio.get_event_loop().time()
        
        while True:
            status = await self.get_task_status(task_id)
            if status["status"] in ["completed", "failed"]:
                return status
            
            if asyncio.get_event_loop().time() - start > timeout:
                raise TimeoutError(f"Task {task_id} did not complete in {timeout}s")
            
            await asyncio.sleep(2)

# Usage
async def main():
    client = CrawlerClient("http://localhost:8001")
    
    # Synchronous scrape
    result = await client.scrape(
        "https://qpublic9.qpublic.net/qpublic_display.cgi?parcel_id=123",
        "qpublic"
    )
    print(f"Parcel: {result['parcel_id']}, Owner: {result['data']['owner_name']}")
    
    # Asynchronous task
    task_id = await client.submit_task("https://...", "qpublic", priority=5)
    result = await client.wait_for_task(task_id)
    print(f"Task completed: {result['status']}")
```

### Node.js Client

```javascript
const axios = require('axios');

class CrawlerClient {
  constructor(baseUrl, apiKey = null) {
    this.base_url = baseUrl;
    this.api_key = apiKey;
  }

  async scrape(url, platform) {
    const response = await axios.post(
      `${this.base_url}/scrape`,
      { url, platform },
      { headers: this.api_key ? { Authorization: `Bearer ${this.api_key}` } : {} }
    );
    return response.data;
  }

  async submitTask(url, platform, priority = 0) {
    const response = await axios.post(
      `${this.base_url}/tasks`,
      { url, platform, priority }
    );
    return response.data.id;
  }

  async getTaskStatus(taskId) {
    const response = await axios.get(`${this.base_url}/tasks/${taskId}`);
    return response.data;
  }

  async waitForTask(taskId, timeout = 300) {
    const start = Date.now();
    
    while (true) {
      const status = await this.getTaskStatus(taskId);
      if (['completed', 'failed'].includes(status.status)) {
        return status;
      }
      
      if (Date.now() - start > timeout * 1000) {
        throw new Error(`Task ${taskId} did not complete in ${timeout}s`);
      }
      
      await new Promise(resolve => setTimeout(resolve, 2000));
    }
  }
}

// Usage
async function main() {
  const client = new CrawlerClient('http://localhost:8001');
  
  const result = await client.scrape(
    'https://qpublic9.qpublic.net/qpublic_display.cgi?parcel_id=123',
    'qpublic'
  );
  console.log(`Parcel: ${result.parcel_id}, Owner: ${result.data.owner_name}`);
}
```

### Webhook Receiver (FastAPI)

```python
from fastapi import FastAPI, Request, HTTPException
import hmac
import hashlib
import json

app = FastAPI()

WEBHOOK_SECRET = "your-secret-key"

def verify_signature(payload: dict, signature: str) -> bool:
    payload_json = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    expected = hmac.new(
        WEBHOOK_SECRET.encode(),
        payload_json.encode(),
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(signature.replace("sha256=", ""), expected)

@app.post("/webhooks")
async def receive_webhook(request: Request):
    # Verify signature
    signature = request.headers.get("X-Webhook-Signature")
    if signature and not verify_signature(await request.json(), signature):
        raise HTTPException(status_code=401, detail="Invalid signature")
    
    # Parse payload
    payload = await request.json()
    event = payload.get("event")
    
    if event == "task.completed":
        task_id = payload["task_id"]
        result = payload["result"]
        print(f"Task {task_id} completed: {result.get('parcel_id')}")
        
    elif event == "task.failed":
        task_id = payload["task_id"]
        error = payload["error"]
        print(f"Task {task_id} failed: {error}")
        
    elif event == "bulk.completed":
        job_id = payload["job_id"]
        stats = payload["stats"]
        print(f"Bulk job {job_id}: {stats['processed_rows']}/{stats['total_rows']}")
    
    return {"status": "received"}
```

---

## Troubleshooting

### Common Issues

**1. Anti-bot Detection**
```
Solution: Enable UC mode in scraper
- Ensure SeleniumBase is installed: pip install seleniumbase
- Check browser logs in /data/raw/{platform}/screenshots/
```

**2. Database Lock**
```
Solution: Enable WAL mode (default)
- PRAGMA journal_mode=WAL (already set in connection.py)
- Ensure single writer access
```

**3. Memory Issues with Large Files**
```
Solution: Use streaming readers
- Bulk readers stream by default (batch_size=100)
- Reduce batch_size in pipeline if needed
```

**4. Webhook Not Received**
```
Solution: Check connectivity and signature
- Verify WEBHOOK_URL is reachable from container
- Check HMAC secret matches on both sides
- Review webhook retry logs
```

### Logs

```bash
# Docker logs
docker logs crawler-qpublic

# With log level
docker logs crawler-qpublic 2>&1 | grep ERROR

# Live tail
docker logs -f crawler-qpublic
```

### Health Checks

```bash
# API health
curl http://localhost:8001/health

# Queue depth
curl http://localhost:8001/tasks | jq '.pending'

# Database integrity
sqlite3 /data/state/crawler.db "PRAGMA integrity_check"
```

---

## License

See [LICENSE](LICENSE) for details.
