# Status: sdd-crawler-appsmith

> **SDD Flow Status Page**
> Scope: Crawler management interface (Flower + minimal API)

**Current Phase:** REQUIREMENTS
**Phase Status:** DRAFT (v2.0 rewrite)
**Last Updated:** 2026-03-01 by Claude
**Version:** 2.0

---

## Major Change: AppSmith Replaced with Flower

**v2.0 Decision:** AppSmith is overkill for single-instance management.

| Aspect | v1.x (AppSmith) | v2.0 (Flower) |
|--------|-----------------|---------------|
| RAM | 2GB+ | ~100MB |
| Tasks | 21 | 8 |
| Files | 19 | 6 |
| Task Monitoring | Build custom | Built-in |
| Retry/Revoke | Build custom | Built-in |

**Flower provides:** Task monitoring, retry/revoke, worker stats, Prometheus metrics

**API provides:** Config, logs, restart, enhanced health

---

## Progress

- [x] Requirements v1.0 drafted (AppSmith approach)
- [x] Specifications v1.0 drafted
- [x] Plan v1.0 drafted (21 tasks)
- [x] Plan v1.0 reviewed
- [x] **Decision: Replace AppSmith with Flower** (2026-03-01)
- [x] **Requirements v2.0 rewritten** (2026-03-01) <- current
- [ ] Requirements v2.0 approved
- [ ] Implementation started

---

## Blockers

- None

---

## v2.0 Summary

**Total Tasks:** 8 (down from 21)

| Phase | Tasks | Focus |
|-------|-------|-------|
| 1. API Endpoints | 4 | logs, restart, enhanced health |
| 2. Log Infrastructure | 2 | SQLite logs table, handler |
| 3. Docker Integration | 2 | Flower in docker-compose |

**File Changes:** 6 files (down from 19)

---

## Architecture

```
Crawler Instance
├── Celery Workers (task execution)
├── Celery Beat (scheduling)
├── Redis (broker)
├── Flower (:5555) - Task monitoring, retry, metrics
└── API (:8000) - Config, logs, restart, health
```

---

## Access Points

| Service | Port | Features |
|---------|------|----------|
| Flower | 5555 | Task list, retry, worker stats, /metrics |
| API | 8000 | /config, /logs, /restart, /health |

---

## Related SDDs

- `sdd-crawler-architecture` - Overall crawler architecture (v3.0 Celery-only)
- `sdd-crawler-celery` - Celery distributed queue
- `sdd-crawler-flower` - Flower monitoring (merged into this SDD)

---

## Next Actions

1. Review requirements v2.0
2. Say **"requirements approved"** to proceed

---

## Historical Notes

- v1.0-1.4: AppSmith approach (21 tasks, 19 files)
- v2.0: Pivot to Flower (8 tasks, 6 files) - 60% reduction
