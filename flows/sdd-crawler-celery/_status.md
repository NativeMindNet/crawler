# Status: sdd-crawler-celery

## Current Phase

REQUIREMENTS

## Phase Status

UPDATED (v3.0 architecture alignment)

## Last Updated

2026-03-01 by Claude

## Blockers

- None

## Progress

- [x] Requirements drafted (initial analysis complete)
- [x] **Architecture v3.0: Celery is now ONLY mode** (2026-03-01)
- [ ] Requirements approved
- [ ] Specifications drafted
- [ ] Specifications approved
- [ ] Plan drafted
- [ ] Plan approved
- [ ] Implementation started
- [ ] Implementation complete

---

## Architecture Change (v3.0)

**Before:** Celery was optional mode alongside SQLite async mode

**After:** Celery is the **ONLY** worker mode (async removed)

| Aspect | v2.x | v3.0 |
|--------|------|------|
| Async Mode | Available | **Removed** |
| Celery Mode | Optional | **Required** |
| Redis | Optional | **Required** |
| Flower | Optional | **Included** |

---

## Context Notes

Key decisions and context for resuming:

- **Purpose**: Core Celery distributed task queue requirements
- **Status**: **FOUNDATIONAL** - this is now the only worker mode
- **Broker**: Redis (required)
- **Monitoring**: Flower dashboard (built-in)
- **Task Chains**: scrape → save → parse

### Components:

| Component | Purpose |
|-----------|---------|
| Celery Workers | Task execution |
| Redis Broker | Task queue |
| Celery Beat | Scheduling |
| Flower | Monitoring |

### Task Patterns:

```python
# Single task
@app.task(queue='default', rate_limit='5/m')
def scrape_url(url): ...

# Chain
chain(scrape_url.s(url), parse_html.s(), save_result.s())()

# Group (parallel)
group(scrape_url.s(url) for url in urls)()
```

### Priority Queues:

| Queue | Priority | Use Case |
|-------|----------|----------|
| urgent | 1 | Auction-imminent |
| high | 2 | Delinquent properties |
| default | 3 | Normal crawling |
| low | 4 | Maintenance |

---

## Open Questions (To Resolve)

| Question | Options | Decision |
|----------|---------|----------|
| Q1 - Broker Config | ENV / config file | TBD |
| Q2 - Serialization | JSON / msgpack | JSON (default) |
| Q3 - Error Handling | Auto-retry count | TBD |
| Q4 - Result Backend | Redis / SQLite | Redis |
| Q5 - Periodic Config | JSON file / DB | JSON file |
| Q6 - Worker Config | Concurrency, pool | TBD |
| Q7 - Deployment | docker-compose | Yes |

---

## Next Actions

1. **User reviews requirements** - Confirm updated scope
2. **Resolve open questions** - Q1, Q3, Q6 need answers
3. **Move to SPECIFICATIONS phase** - Design Celery architecture

---

## Related SDDs

- `sdd-crawler-architecture` - v3.0 Celery-only architecture
- `sdd-crawler-appsmith` - v2.0 Flower + API
- `sdd-crawler-flower` - MERGED into sdd-crawler-appsmith

---

## Fork History

- v1.0: Original Celery requirements (optional mode)
- v3.0: Updated for Celery-only architecture (2026-03-01)
