# Status: sdd-crawler-rawdata

## DEPRECATED - MERGED

**Merged Into:** `sdd-crawler-architecture` (Storage Architecture)
**Merge Date:** 2026-03-01
**Reason:** Raw data storage is part of LPM file structure in architecture doc

---

## What Happened

1. Raw data storage patterns are documented in `sdd-crawler-architecture/01-architecture.md`
2. File organization (/data/raw/, /data/pending/, /data/images/) is in Section 7
3. This SDD's requirements are incorporated into architecture doc

---

## Key Concepts (Now in Architecture)

**Storage Structure:**
```
/data/
├── lpm.db               # Task queue + metadata
├── pending/             # Results ready for consumption
│   └── {task_id}.json
├── raw/                 # HTML archive
│   └── {task_id}.html.gz
└── images/
    └── {task_id}/
        ├── photo_1.jpg
        └── photo_2.jpg
```

**Features:**
- HTML saved before parsing (source of truth)
- JSON results with metadata (timestamp, platform, version)
- PDF/image per-parcel storage (no global dedup)
- Compression for old HTML files (.gz after N days)
- Docker volumes for CI/CD persistence

---

## Historical Context

See `01-requirements.md` in this directory for original raw data requirements.

Original scope:
- HTML scraping persistence
- Parsed JSON storage
- PDF document handling
- Image asset handling
- CI/CD data persistence
- Storage organization

**Resolved Decisions:**
- PDF deduplication: per-parcel
- Failed scrape HTML: don't keep
- HTML compression: yes, after 30 days
- County subdirectories: via volume subPath

---

## See Also

- `sdd-crawler-architecture/01-architecture.md` Section 7 - Storage Architecture
- `SDD-CONSOLIDATION.md` - Consolidation plan
