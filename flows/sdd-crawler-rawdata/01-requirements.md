# Requirements: Tax Lien Parser Raw Data Storage

> Version: 1.0
> Status: DRAFT
> Last Updated: 2026-02-22
> SDD: ./_status.md

## Overview

Document and standardize the raw data storage architecture for scraped files including HTML, JSON, PDF, and images. Ensure data persistence across deployments and provide clear organization for discovered parcel data.

**Motivation:**
- Current storage patterns evolved organically across `storage/`, `orchestrator/storage/`, and `taxlien-storage/`
- Need clear specification for what gets stored where
- PDF and image handling needs explicit design
- CI/CD deployment must preserve downloaded data

---

## User Stories

### US-1: HTML Scraping Persistence

**As a** scraper operator
**I want** all scraped HTML to be persisted to disk
**So that** I can re-parse, debug, and audit scraping results

**Acceptance Criteria:**
- [ ] Every successful scrape saves raw HTML to disk
- [ ] HTML files are organized by platform/state/county/parcel_id
- [ ] File naming is consistent and predictable
- [ ] HTML is saved BEFORE parsing (raw source of truth)
- [ ] Failed scrapes: optional temp debug file for last attempt only (deleted on retry)
- [ ] Old HTML compressed to `.gz` after configurable days (default: 30 days)

---

### US-2: Parsed JSON Data Storage

**As a** data consumer
**I want** parsed results saved as structured JSON
**So that** I can import, query, and process parcel data

**Acceptance Criteria:**
- [ ] Each parsed parcel saves a JSON file alongside its HTML
- [ ] JSON structure follows canonical data model
- [ ] JSON includes metadata (scrape timestamp, platform, version)
- [ ] JSON is validated against schema before saving
- [ ] PDF metadata includes: filename, size, download date, URL, SHA256 hash
- [ ] PDFs stored per-parcel (no global deduplication)

---

### US-3: PDF Document Handling

**As a** researcher
**I want** downloaded PDF documents (tax bills, deeds, notices) stored with their parcel
**So that** I can access official documents for each property

**Acceptance Criteria:**
- [ ] PDFs are downloaded and saved to parcel directory
- [ ] PDF filenames indicate document type (tax_bill, deed, notice, etc.)
- [ ] PDF metadata tracked in JSON (filename, size, download date, URL, SHA256 hash)
- [ ] PDFs stored per-parcel (no global deduplication)
- [ ] Large PDFs handled efficiently (streaming download, not loading fully in memory)

---

### US-4: Image Asset Handling

**As a** analyst
**I want** property images and aerial photos downloaded and stored
**So that** I can visually assess properties without visiting county websites

**Acceptance Criteria:**
- [ ] Images extracted from HTML (img tags with property photos)
- [ ] Images downloaded and saved to parcel directory
- [ ] Image metadata tracked (URL, type, dimensions if available, SHA256 hash)
- [ ] Images stored per-parcel (no global deduplication)
- [ ] Image types supported: JPG, PNG, GIF, WEBP
- [ ] Aerial/satellite imagery handled separately from property photos

---

### US-5: CI/CD Data Persistence

**As a** DevOps engineer
**I want** raw data to persist across Docker deployments
**So that** scraping progress is not lost during updates

**Acceptance Criteria:**
- [ ] Data stored on host filesystem (Docker bind mount)
- [ ] `docker-compose down` does not affect data
- [ ] New containers see existing data immediately
- [ ] Backup strategy documented for host data directory
- [ ] Migration path for moving data between servers

---

### US-6: Storage Organization

**As a** developer
**I want** consistent directory structure across environments
**So that** I can find files and write tooling that works everywhere

**Acceptance Criteria:**
- [ ] Standard path template: `{root}/{platform}/{state}/{county}/{parcel_id}/*`
- [ ] Pending vs completed separation for in-progress work
- [ ] Year-based archival for old data
- [ ] Clear separation between raw HTML and parsed JSON

---

### US-7: Queue/State Management

**As a** system operator
**I want** a queue/state database to track what's been scraped
**So that** I don't re-scrape the same parcels and can resume after failures

**Acceptance Criteria:**
- [ ] SQLite database tracks task queue (pending/processing/completed/failed)
- [ ] Each task linked to its file paths on disk
- [ ] Sync status tracked (local vs synced to gateway)
- [ ] Discovery source tracked (direct, ripple effect, manual)
- [ ] Priority system for task ordering

---

## Constraints

### Technical Constraints

- **C-1:** Must work with existing Docker Compose deployment
- **C-2:** Data directory must be external volume (not Docker volume)
- **C-3:** Support both Linux and macOS runners
- **C-4:** Backward compatible with existing `storage/` and `orchestrator/storage/`
- **C-5:** Handle large files (100MB+ PDFs) efficiently

### Non-Goals

- **NG-1:** Not building a full document management system
- **NG-2:** Not implementing real-time sync (batch sync to gateway is OK)
- **NG-3:** Not storing binary data in database (files on disk only)
- **NG-4:** Not implementing versioning for scraped files (current snapshot only)

---

## Resolved Questions

| Question | Decision |
|----------|----------|
| Q1: PDF/image deduplication | **Per-parcel** — each parcel keeps its own copy, no global dedup |
| Q2: Failed scrape HTML | **Don't keep** — optional temporary debug file for last attempt only |
| Q3: HTML compression | **Yes** — compress old HTML to `.gz` after N days to save space |
| Q4: County subdirectories | TBD during specifications |
| Q5: Imagery download timing | **Out of scope** for this spec |

---

## Current State Analysis

### Existing Storage Locations

| Location | Purpose | Content |
|----------|---------|---------|
| `orchestrator/storage/` | CI/CD worker storage | Custom GIS HTML/JSON |
| `storage/scraped/` | Historical scraped data | Platform/state/county structure |
| `storage/parsed/` | Parsed results | JSON files |
| `storage/cache/` | Caching | Various cache files |
| `storage/jobs/` | Job state | Ingestion state tracking |
| `taxlien-storage/` | External sample repository | 920+ HTML samples for validation |

### Current File Patterns

**HTML:**
- Path: `{platform}/{state}/{county}/{parcel_id}.html` or `{parcel_id}_{timestamp}.html`
- Saved in: `orchestrator/storage/`, `storage/scraped/`

**JSON:**
- Path: `{platform}/{state}/{county}/{parcel_id}.json`
- Saved in: `storage/data/`, `storage/parsed/`

**PDF/Images:**
- Currently: Extracted URLs stored in JSON `image_urls` array
- Download: Implemented in `parsers/imagery_service.py` but not consistently used
- Storage: `storage/test_downloads/` for tests

### Database Schema (worker_state.db)

```sql
-- Task queue
tasks(id, entity_type, platform, state, county, parcel_id, target_json, priority, status, discovery_source, updated_at)

-- Results metadata
results(task_id, parcel_id, platform, state, county, json_path, html_path, scraped_at, sync_status)

-- Discovered links (Ripple Effect)
task_links(parent_id, child_id, relation_type, delta)
```

---

## Approval

- [ ] Requirements reviewed by user
- [ ] Open questions resolved
- [ ] Scope clearly bounded
- [ ] **User explicitly approves: "requirements approved"**
