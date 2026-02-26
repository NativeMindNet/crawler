# Specifications: Local Storage & Synchronization for Tax Lien Parser

## 1. Architecture Overview
The system consists of a `storage` module providing a non-blocking interface to a SQLite database. The `WorkerRunner` uses this for immediate persistence and runs a background loop for synchronization.

## 2. Storage Schema (SQLite)

We use **WAL (Write-Ahead Logging)** mode to allow concurrent reads (by the Sync Service) and writes (by the Scraper Worker).

### Table: `tasks`
Tracks tasks regardless of their source (Gateway or Local File).
- `task_id`: TEXT PRIMARY KEY
- `source`: TEXT ('gateway', 'local_file', 'cli')
- `platform`, `state`, `county`, `parcel_id`: TEXT
- `target_json`: TEXT (Serialized target dict)
- `status`: TEXT ('pending', 'running', 'completed', 'failed')
- `created_at`: DATETIME
- `updated_at`: DATETIME

### Table: `local_results`
Tracks local results and their synchronization status.
- `task_id`: TEXT PRIMARY KEY (Foreign Key to `tasks`)
- `parcel_id`: TEXT
- `platform`: TEXT
- `state`: TEXT
- `county`: TEXT
- `data`: TEXT (JSON serialized result data)
- `json_path`: TEXT (Optional: path to local .json)
- `html_path`: TEXT (Optional: path to local .html.gz)
- `scraped_at`: TEXT (ISO format timestamp)
- `synced`: INTEGER (0=False, 1=True)
- `sync_attempts`: INTEGER
- `last_error`: TEXT

## 3. Directory Structure
```text
storage/
├── __init__.py
├── db.py           # SQLite schema and CRUD (aiosqlite)
├── sync.py         # Sync worker logic
├── worker_state.db  # SQLite database
└── data/           # (Optional) Raw HTML/JSON storage
    ├── {platform}/
    │   └── {state}/
    │       └── {county}/
    │           ├── {parcel_id}.json
    │           └── {parcel_id}.html.gz
```

## 4. Technical Implementation Details

### 4.1 `storage/db.py`
Provides `LocalDatabase` class:
- `async def init()`: Initialize DB and tables.
- `async def register_task(task: Task)`: Persist new task.
- `async def save_result(result: ParcelResult)`: Upsert to `local_results` and update task status.
- `async def get_unsynced_results()`: Fetch pending uploads.
- `async def mark_synced(task_id: str)`: Set `synced=1`.

### 4.2 `storage/sync.py`
Provides `SyncManager` class:
- `async def sync_loop()`: Background loop fetching unsynced rows and attempting upload via `client.submit_results`.
- Implements exponential backoff.

### 4.3 `worker/runner.py` Integration
- Initialize `LocalDatabase` in `__init__`.
- Start `SyncManager.sync_loop()` as a background task in `start()`.
- In `_process_task()`, always `save_result()` locally first, then try immediate upload.

## 5. Error Handling & Retries
- Gateway unavailable: Background sync retries with backoff (30s to 5m).
- Data rejection (400/422): Log error, increment attempts, but avoid infinite loops for unfixable data.