# Universal Single-Platform Crawler

A Docker-native, configurable web crawler designed for single-platform instances. Supports scraping, parsing, bulk ingestion, and imagery extraction with local persistence and resume capability.

## Features

- **Single-Platform Design**: Each crawler instance handles ONE platform (configured at runtime)
- **Docker-Native**: Built for containerized deployment with volume mounts
- **Dual Interface**: FastAPI REST API + Typer CLI
- **Local Persistence**: SQLite-based task queue with resume capability
- **Bulk Ingestion**: CSV, Excel, GIS (Shapefile/GeoJSON), JSON/JSONL support
- **Imagery Service**: Photo extraction + external mapping links (Google Maps, Street View, Satellite)
- **Webhook Notifications**: Real-time callbacks for task completion
- **Anti-Bot Support**: SeleniumBase with UC mode for challenging sites

## Quick Start

### Run with Docker

```bash
# Build the image
docker build -t crawler .

# Run a single-platform instance
docker run -d \
  --name crawler-qpublic \
  -v ./platforms/qpublic:/config:ro \
  -v ./data/qpublic/results:/data/results \
  -v ./data/qpublic/raw:/data/raw \
  -v ./data/qpublic/state:/data/state \
  -e PLATFORM=qpublic \
  -e WEBHOOK_URL=http://your-gateway/api/webhooks \
  -e WEBHOOK_SECRET=your-secret-key \
  -p 8001:8000 \
  crawler worker run
```

### Run Locally

```bash
# Install dependencies
pip install -r requirements.txt

# Run a scrape operation
python -m crawler scrape https://example.com/parcel/123 --platform qpublic

# Start the API server
python -m crawler api serve --port 8000

# Start a worker
python -m crawler worker run
```

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│              External Ecosystem                         │
│  CLI  │  HTTP API  │  Webhook Listener                 │
└────────────────────────┬────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│           Crawler Instance (Docker)                     │
│  ┌───────────────────────────────────────────────────┐  │
│  │  API/CLI Layer (FastAPI + Typer)                  │  │
│  └───────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────┐  │
│  │  Core Engine                                      │  │
│  │  Scraper │ Parser │ Bulk Ingestion │ Imagery     │  │
│  └───────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────┐  │
│  │  Local Persistence Manager (SQLite + Filesystem)  │  │
│  └───────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────┐  │
│  │  Platform Configuration (JSON)                    │  │
│  └───────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│           Docker Volume Mounts                          │
│  /data/results  │  /data/raw  │  /data/state           │
└─────────────────────────────────────────────────────────┘
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check and queue depth |
| `/tasks` | POST | Submit single URL task |
| `/tasks/{task_id}` | GET | Get task status |
| `/tasks/{task_id}/result` | GET | Get task result |
| `/scrape` | POST | Scrape + parse single URL |
| `/bulk/ingest` | POST | Start bulk ingestion |
| `/bulk/{job_id}` | GET | Get bulk job status |
| `/webhooks/test` | POST | Test webhook endpoint |

## CLI Commands

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

## Platform Configuration

Each platform has its own configuration directory:

```
config/platforms/{platform}/
├── selectors.json      # CSS/XPath selectors for parsing
├── mapping.json        # Field mapping and transforms
├── discovery.json      # Navigation and link discovery rules
├── business_rules.json # Validation and constraints
├── schedule.json       # Optional cron schedule
└── manifest.json       # Platform metadata
```

### Example: selectors.json

```json
{
  "platform": "qpublic",
  "version": "1.0",
  "selectors": {
    "parcel_id": {"selector": "#_lblParcelID", "type": "css"},
    "owner": {"selector": "#ctlBodyPane_ctl01_ctl00_lblName", "type": "css"},
    "site_address": {"selector": "#InfoPane2_lnkWebsite", "type": "css", "attr": "href"}
  },
  "discovery": {
    "county_links": {"selector": ".county-option", "type": "css", "attr": "href"},
    "parcel_links": {"selector": "[id*='_lnkParcelID']", "type": "css", "attr": "href"}
  }
}
```

## Data Models

### Task

```python
{
  "id": "uuid",
  "url": "https://...",
  "platform": "qpublic",
  "status": "pending|processing|completed|failed",
  "priority": 0,
  "created_at": "2026-02-26T10:00:00Z",
  "result_path": "/data/results/qpublic/abc123.json",
  "raw_paths": {
    "html": "/data/raw/qpublic/abc123.html",
    "images": ["/data/raw/qpublic/abc123_img1.jpg"]
  }
}
```

### Webhook Payload

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

## Development

### Project Structure

```
crawler/
├── __init__.py
├── __main__.py                 # Entry point
├── config_loader.py
├── config_validator.py
├── lpm.py                      # Local Persistence Manager
├── storage.py
├── state.py
├── discovery.py
├── priority.py
├── worker.py
├── worker_loop.py
├── gateway_sync.py
├── models/                     # Data models
├── repositories/               # Data access layer
├── db/                         # Database schema
├── scraper/                    # Scraping module
├── parser/                     # Parsing module
├── parsers/                    # Platform-specific parsers
├── bulk/                       # Bulk ingestion module
├── imagery/                    # Imagery service
├── api/                        # FastAPI layer
├── cli/                        # Typer CLI
└── webhooks/                   # Webhook client

tests/                          # Test suite
config/platforms/               # Platform configurations
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=crawler --cov-report=html

# Run specific test file
pytest tests/test_lpm.py
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `PLATFORM` | Platform name (config directory) | - |
| `WEBHOOK_URL` | Webhook callback URL | - |
| `WEBHOOK_SECRET` | HMAC signing secret | - |
| `DB_PATH` | SQLite database path | `/data/state/crawler.db` |
| `DATA_DIR` | Data directory | `/data` |
| `CONFIG_DIR` | Config directory | `/config` |
| `LOG_LEVEL` | Logging level | `INFO` |

## Supported Platforms

The crawler is compatible with 27 platform configurations from the `sdd-crawler-platform-config` SDD flow:

- QPublic
- Beacon
- FloridaTax
- And 24 more...

Each platform has its own configuration with selectors, mapping, and discovery rules.

## License

See [LICENSE](LICENSE) for details.
