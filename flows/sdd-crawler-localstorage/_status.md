# Status: sdd-crawler-localstorage

## DEPRECATED - MERGED

**Merged Into:** `sdd-crawler-architecture` (LPM component)
**Merge Date:** 2026-03-01
**Reason:** Local storage is core LPM functionality in architecture doc

---

## What Happened

1. LocalPersistenceManager (LPM) is a core component of crawler architecture
2. SQLite + files persistence is documented in `sdd-crawler-architecture/01-architecture.md`
3. This SDD's requirements are incorporated into architecture Section 7 (Storage Architecture)

---

## Key Concepts (Now in Architecture)

**LPM Components:**
- `lpm.db` - SQLite database for task state, results metadata, logs
- `/data/pending/` - Results ready for consumption (JSON)
- `/data/raw/` - HTML archive (optional, compressed)
- `/data/images/` - Downloaded images

**Features:**
- Offline resilience (local-first)
- Background sync to Gateway
- Resume capability after crash/restart
- Ripple Effect (graph-based task discovery)

---

## Historical Context

See `01-requirements.md` in this directory for original local storage requirements.

Original scope:
- SQLite persistence with aiosqlite
- Offline buffer when Gateway unavailable
- Background synchronization
- Exponential backoff for retries

---

## See Also

- `sdd-crawler-architecture/01-architecture.md` Section 7 - Storage Architecture
- `SDD-CONSOLIDATION.md` - Consolidation plan
