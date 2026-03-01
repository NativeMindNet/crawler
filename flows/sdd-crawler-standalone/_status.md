# Status: sdd-crawler-standalone

## Current Phase

REQUIREMENTS

## Phase Status

UPDATED (v1.0 - Celery-based)

## Last Updated

2026-03-01 by Claude

## Blockers

- None

---

## Progress

- [x] Requirements v0.2 drafted (async-based)
- [x] Specifications v0.2 approved (async-based)
- [x] **Rewritten for Celery architecture** (2026-03-01)
- [x] Requirements v1.0 drafted (Celery-based) ← current
- [ ] Requirements approved
- [ ] Specifications drafted
- [ ] Implementation started
- [ ] Implementation complete

---

## Architecture Change

**Before (v0.2):** Async worker loop with SQLite queue

**After (v1.0):** Celery workers with local Redis

| Aspect | v0.2 (Async) | v1.0 (Celery) |
|--------|--------------|---------------|
| Worker | Single process | N workers |
| Queue | SQLite | Redis |
| Monitoring | Logs | **Flower** |
| Retry | Manual | **Automatic** |

---

## Key Scenarios

| Scenario | Description | Celery Support |
|----------|-------------|----------------|
| **A: Emergency** | Gateway down, scrape from CSV | ✅ `bulk import` |
| **B: Benchmark** | Test parser locally | ✅ Isolated stack |
| **C: Debug** | Single URL test | ✅ `celery call` |

---

## Implementation Summary

**Tasks:** 7
**Files:** 7

| Task | Description |
|------|-------------|
| 1 | `docker-compose.standalone.yml` |
| 2 | `STANDALONE` env handling |
| 3 | `bulk import` CLI |
| 4 | LPM state table |
| 5 | `results export` CLI |
| 6 | Single URL CLI |
| 7 | Documentation |

---

## Docker Compose Stack

```yaml
services:
  redis:    # Task broker
  worker:   # Celery workers (STANDALONE=true)
  flower:   # Monitoring UI
```

**No Gateway required.**

---

## CLI Commands

```bash
# Import tasks
python -m crawler bulk import parcels.csv --queue=urgent

# Single URL
python -m crawler scrape http://example.com/parcel/123

# Export results
python -m crawler results export --output results.json
```

---

## Related SDDs

- `sdd-crawler-architecture` - v3.0 Celery-only
- `sdd-crawler-celery` - Celery integration
- `sdd-crawler-bulk` - Bulk ingestion (shared CLI)

---

## Historical Context

v0.2 (async-based) specifications were completed but superseded by v1.0 (Celery-based) after architecture v3.0 pivot.

Original scope (preserved):
- Infrastructure independence
- Local task sources (CSV/JSON)
- LPM for results
- Resume capability

---

## Next Actions

1. Review requirements v1.0
2. Say **"requirements approved"** to proceed
