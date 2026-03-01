# Requirements: Bulk Ingestion Module (Celery-based)

**Version:** 1.0
**Status:** DRAFT
**Last Updated:** 2026-03-01

---

## 1. Goal

Create a dedicated pipeline for ingesting large datasets (Tax Rolls, GIS Shapefiles, FTP dumps) using **Celery groups** for parallel processing, feeding directly into LPM storage.

---

## 2. Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      BULK INGESTION PIPELINE                             │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                        CLI / API                                 │   │
│  │  python -m crawler bulk import data.csv --parallel              │   │
│  └──────────────────────────────┬──────────────────────────────────┘   │
│                                 │                                       │
│                                 ▼                                       │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                      File Reader                                 │   │
│  │  CSV | Excel | Shapefile | GeoJSON | JSON | JSONL               │   │
│  └──────────────────────────────┬──────────────────────────────────┘   │
│                                 │                                       │
│                                 ▼                                       │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                    Mapping Engine                                │   │
│  │  Profile → Transform → Validate → Normalize                     │   │
│  └──────────────────────────────┬──────────────────────────────────┘   │
│                                 │                                       │
│                                 ▼                                       │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                    Celery Group                                  │   │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐               │   │
│  │  │ Batch 1 │ │ Batch 2 │ │ Batch 3 │ │ Batch N │  (parallel)   │   │
│  │  └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘               │   │
│  └───────┼──────────┼──────────┼──────────┼────────────────────────┘   │
│          │          │          │          │                            │
│          └──────────┴─────┬────┴──────────┘                            │
│                           │                                             │
│                           ▼                                             │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                      LPM (Storage)                               │   │
│  │  bulk_jobs | bulk_records | properties | discovered_urls        │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Supported Formats

| Format | Extension | Library | Streaming |
|--------|-----------|---------|-----------|
| CSV | `.csv` | pandas/csv | Yes |
| Excel | `.xlsx`, `.xls` | openpyxl | No |
| Shapefile | `.shp` | geopandas | No |
| GeoJSON | `.geojson` | geopandas | Yes |
| JSON | `.json` | json | No |
| JSONL | `.jsonl` | json | Yes |

---

## 4. User Stories

### US-1: GIS Import
**As a** data engineer
**I want** to import a GIS Shapefile with 50,000 parcels
**So that** I populate the DB with geometries without crawling

```bash
python -m crawler bulk import county_parcels.shp \
  --profile=gis_default \
  --parallel \
  --batch-size=1000
```

---

### US-2: Tax Roll CSV
**As a** researcher
**I want** to import a Tax Roll CSV from county clerk
**So that** I bulk-update tax statuses

```bash
python -m crawler bulk import tax_roll_2026.csv \
  --profile=realauction_fl \
  --queue=default
```

---

### US-3: Auction List Import
**As a** operator
**I want** to import auction parcel URLs for scraping
**So that** I queue them for immediate processing

```bash
python -m crawler bulk import auction_list.csv \
  --mode=scrape \
  --queue=urgent
```

---

## 5. Mapping Profiles

```json
// profiles/realauction_fl.json
{
  "name": "realauction_fl",
  "description": "RealAuction Florida export format",
  "source_format": "csv",
  "mappings": {
    "parcel_id": {"source": "Certificate Number", "transform": "clean_parcel_id"},
    "address": {"source": "Property Address"},
    "owner_name": {"source": "Owner Name"},
    "assessed_value": {"source": "Assessed Value", "transform": "to_decimal"},
    "tax_amount": {"source": "Face Amount", "transform": "to_decimal"},
    "auction_date": {"source": "Sale Date", "transform": "to_date"},
    "state": {"constant": "FL"},
    "county": {"source": "County"}
  },
  "required_fields": ["parcel_id", "county", "state"],
  "transforms": {
    "clean_parcel_id": "lambda x: x.strip().upper().replace('-', '')",
    "to_decimal": "lambda x: Decimal(str(x).replace(',', '').replace('$', ''))",
    "to_date": "lambda x: datetime.strptime(x, '%m/%d/%Y').date()"
  }
}
```

---

## 6. Celery Tasks

### Bulk Import Job

```python
from celery import group, chord

@app.task(bind=True)
def start_bulk_import(self, file_path: str, profile: str, options: dict):
    """Start bulk import job."""

    # Create job record
    job_id = lpm.create_bulk_job(
        file_path=file_path,
        profile=profile,
        status='starting'
    )

    # Load profile
    profile_config = load_profile(profile)

    # Read file and create batches
    reader = get_reader(file_path, profile_config)
    batches = list(reader.iter_batches(options.get('batch_size', 100)))

    # Update job with total count
    lpm.update_bulk_job(job_id, total_records=sum(len(b) for b in batches))

    # Create parallel tasks
    if options.get('parallel', True):
        # Celery group for parallel processing
        job = group(
            process_batch.s(job_id, batch, profile_config)
            for batch in batches
        )

        # Chord: parallel batches, then finalize
        chord(job)(finalize_bulk_job.s(job_id))
    else:
        # Sequential processing
        for batch in batches:
            process_batch.delay(job_id, batch, profile_config)
        finalize_bulk_job.delay(job_id)

    return {'job_id': job_id, 'batches': len(batches)}
```

### Batch Processing

```python
@app.task(bind=True)
def process_batch(self, job_id: str, records: list, profile: dict):
    """Process a batch of records."""

    results = {'success': 0, 'failed': 0, 'errors': []}

    for record in records:
        try:
            # Apply mapping
            mapped = apply_mapping(record, profile['mappings'])

            # Validate
            validate_record(mapped, profile['required_fields'])

            # Upsert to LPM
            lpm.upsert_property(mapped)

            results['success'] += 1

        except Exception as e:
            results['failed'] += 1
            results['errors'].append({
                'record': record,
                'error': str(e)
            })

    # Update job progress
    lpm.increment_bulk_job_progress(job_id, results['success'], results['failed'])

    return results
```

### Finalization

```python
@app.task
def finalize_bulk_job(batch_results: list, job_id: str):
    """Finalize bulk import job."""

    # Aggregate results
    total_success = sum(r['success'] for r in batch_results)
    total_failed = sum(r['failed'] for r in batch_results)

    # Update job status
    lpm.update_bulk_job(
        job_id,
        status='completed',
        success_count=total_success,
        failed_count=total_failed,
        completed_at=datetime.now()
    )

    return {
        'job_id': job_id,
        'success': total_success,
        'failed': total_failed
    }
```

---

## 7. Import Modes

| Mode | Description | Output |
|------|-------------|--------|
| `data` | Import as property data | LPM properties table |
| `scrape` | Import URLs for scraping | Celery scrape tasks |
| `urls` | Import as discovered URLs | LPM discovered_urls table |

```bash
# Mode: data (default) - import property records
python -m crawler bulk import tax_roll.csv --mode=data

# Mode: scrape - submit URLs as scrape tasks
python -m crawler bulk import url_list.csv --mode=scrape --queue=high

# Mode: urls - queue for later scraping
python -m crawler bulk import parcel_ids.csv --mode=urls
```

---

## 8. CLI Interface

```bash
python -m crawler bulk import <file> [options]

Arguments:
  file                  Input file path

Options:
  --profile TEXT        Mapping profile name [default: auto-detect]
  --mode TEXT           Import mode: data|scrape|urls [default: data]
  --parallel / --sequential
                        Use parallel processing [default: parallel]
  --batch-size INT      Records per batch [default: 100]
  --queue TEXT          Target queue for scrape mode [default: default]
  --dry-run             Preview without importing
  --validate-only       Validate file without importing
  --resume JOB_ID       Resume interrupted job

Examples:
  # Import CSV with auto-detected profile
  python -m crawler bulk import data.csv

  # Import GIS with specific profile
  python -m crawler bulk import parcels.shp --profile=gis_maricopa

  # Import URLs for urgent scraping
  python -m crawler bulk import auction.csv --mode=scrape --queue=urgent

  # Dry run to preview
  python -m crawler bulk import data.csv --dry-run
```

---

## 9. Job Management

```bash
# List jobs
python -m crawler bulk jobs
# ID        STATUS      PROGRESS    FILE
# job-001   completed   1000/1000   tax_roll.csv
# job-002   running     450/2000    parcels.shp
# job-003   failed      0/500       bad_data.csv

# Job details
python -m crawler bulk status job-002
# Job ID: job-002
# Status: running
# Progress: 450/2000 (22%)
# Success: 445
# Failed: 5
# Errors: [...]

# Resume failed job
python -m crawler bulk resume job-003

# Cancel running job
python -m crawler bulk cancel job-002
```

---

## 10. LPM Schema

```sql
-- Bulk import jobs
CREATE TABLE bulk_jobs (
    job_id TEXT PRIMARY KEY,
    file_path TEXT,
    profile TEXT,
    mode TEXT,
    status TEXT,           -- starting, running, completed, failed, cancelled
    total_records INTEGER,
    processed_records INTEGER DEFAULT 0,
    success_count INTEGER DEFAULT 0,
    failed_count INTEGER DEFAULT 0,
    created_at TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    error TEXT
);

-- Individual record tracking (for resume)
CREATE TABLE bulk_records (
    job_id TEXT,
    record_index INTEGER,
    status TEXT,           -- pending, success, failed
    error TEXT,
    PRIMARY KEY (job_id, record_index)
);

-- Discovered URLs for later scraping
CREATE TABLE discovered_urls (
    id INTEGER PRIMARY KEY,
    url TEXT UNIQUE,
    source TEXT,           -- bulk_import, ripple, sweeper
    source_job_id TEXT,
    priority INTEGER,
    status TEXT,           -- pending, queued, completed
    created_at TIMESTAMP
);
```

---

## 11. Platform-Specific Profiles

### RealAuction (FL, AZ)

```json
{
  "name": "realauction_fl",
  "platforms": ["realauction"],
  "states": ["FL"],
  "coverage": "~15 counties",
  "source_format": "csv",
  "encoding": "utf-8"
}
```

### Beacon (Schneider Corp)

```json
{
  "name": "beacon_export",
  "platforms": ["beacon"],
  "coverage": "90 counties",
  "source_format": "csv"
}
```

### qPublic (Schneider Corp)

```json
{
  "name": "qpublic_export",
  "platforms": ["qpublic"],
  "coverage": "229 counties",
  "source_format": "csv"
}
```

---

## 12. Monitoring

### Flower Integration

- View bulk import tasks in Flower
- Track batch progress
- Retry failed batches

### Prometheus Metrics

```python
bulk_import_total = Counter('bulk_import_total', 'Total bulk imports', ['status'])
bulk_import_records = Counter('bulk_import_records', 'Records processed', ['status'])
bulk_import_duration = Histogram('bulk_import_duration', 'Import duration')
```

---

## 13. Implementation Tasks

| Task | Description | Complexity |
|------|-------------|------------|
| 1 | Implement file readers (CSV, Excel, GIS, JSON) | Medium |
| 2 | Implement mapping engine | Medium |
| 3 | Implement profile loader | Low |
| 4 | Implement `start_bulk_import` task | Medium |
| 5 | Implement `process_batch` task | Medium |
| 6 | Implement `finalize_bulk_job` task | Low |
| 7 | Add LPM tables (bulk_jobs, bulk_records) | Low |
| 8 | Implement CLI commands | Medium |
| 9 | Create default profiles | Low |
| 10 | Add job resume capability | Medium |

**Total: 10 tasks**

---

## 14. Constraints

- **C-1:** Must use LPM for storage (same as scraped data)
- **C-2:** Must handle large files (>1GB) via streaming
- **C-3:** Must support resume after interruption
- **C-4:** Must be idempotent (upsert, no duplicates)

---

## Approval

- [ ] Reviewed by: [name]
- [ ] Approved on: [date]
