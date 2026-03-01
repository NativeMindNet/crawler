# Status: sdd-crawler-architecture

**Current Phase:** PLAN (drafted, awaiting review)
**Last Updated:** 2026-03-01
**Version:** 3.0

---

## Goals

- [x] Document universal single-platform crawler architecture
- [x] Clarify pivot from multi-platform (taxlien-parser) design
- [x] Define external orchestration model
- [x] Document component catalog
- [x] Define deployment options (Docker, K8s)
- [x] Define platform-agnostic storage architecture
- [x] Define K8s labels for service discovery
- [x] Architecture approved (2026-03-01)
- [x] Specifications drafted
- [x] Added: SOCKS proxy support (plain + tor-socks-proxy-service)
- [x] Added: Rate limiting per domain
- [x] Specifications approved (2026-03-01)
- [x] Plan drafted
- [x] **v3.0: Celery-only architecture (removed async mode)**
- [x] **v3.0: Flower integration for monitoring**
- [ ] Plan approved

---

## Progress

- [x] Initial architecture v1.0 (multi-platform, 2026-02-11)
- [x] Architecture v2.0 update (single-platform pivot, 2026-03-01)
- [x] Comparison table: old vs new design
- [x] Deployment examples (docker-compose, kubernetes)
- [x] v2.1: Platform-agnostic storage design (2026-03-01)
- [x] v2.1: K8s labels convention for discovery (2026-03-01)
- [x] Architecture approved (2026-03-01)
- [x] Specifications drafted (2026-03-01)
- [x] v2.2: Added proxy support + rate limiting (2026-03-01)
- [x] Specifications approved (2026-03-01)
- [x] Plan drafted (2026-03-01)
- [x] **v3.0: Removed async mode, Celery-only (2026-03-01)** ← current
- [ ] Plan approved

---

## Implementation Summary

**5 Phases, 24 Tasks, ~76 Files**

| Phase | Tasks | Complexity |
|-------|-------|------------|
| 1. Foundation | 4 | Low-Medium |
| 2. Core Modules | 5 | Medium-High |
| 3. Interfaces | 2 | Medium |
| 4. Advanced Features | 3 | Medium-High |
| 5. Testing & Deployment | 4 | Medium-High |

---

## Key Changes in v3.0

### Simplification: Celery-Only

| Aspect | v2.x | v3.0 |
|--------|------|------|
| Worker Mode | Dual (Async OR Celery) | **Celery only** |
| Monitoring | Optional Flower | **Flower built-in** |
| Dependencies | Redis optional | Redis required |
| Complexity | Two code paths | Single unified path |

### Why Celery-Only?

1. **Simplicity** - One worker implementation, not two
2. **Flower** - Provides all monitoring needs out-of-box
3. **Production-ready** - Celery is mature, battle-tested
4. **No trade-offs** - Celery handles both low and high volume

### Stack Components

| Component | Purpose |
|-----------|---------|
| Celery Workers | Task execution |
| Redis | Task broker |
| Celery Beat | Scheduling (Gateway sync, periodic crawls) |
| Flower | Monitoring, retry, metrics |
| LPM | Local persistence (SQLite + files) |

---

## Key Changes in v2.0

### Architectural Pivot

| Aspect | v1.0 (Old) | v2.0 (New) |
|--------|------------|------------|
| Scope | Multi-platform in one codebase | Single-platform per instance |
| Domain | Tax-lien specific | Domain-agnostic |
| Worker | Celery distributed | Single-platform focused |
| Orchestration | Internal strategy mixer | External (Gateway/Scheduler) |
| Scaling | Celery worker count | Container instances × Celery workers |

### Why Single-Platform?

1. **Simplicity** - Each instance has one job
2. **Isolation** - Platform issues don't cascade
3. **Scalability** - Scale per-platform independently
4. **Testability** - Test platforms in isolation
5. **Flexibility** - External systems decide what runs where

---

## Historical Analysis (v1.0)

### Existing SDDs Originally Analyzed

| SDD | Type | Status |
|-----|------|--------|
| sdd-taxlien-parser-parcel | Core | Superseded |
| sdd-taxlien-parser-party | Documents | Superseded |
| sdd-taxlien-parser-configs | Config | Migrated to JSON |
| sdd-taxlien-parser-localstorage | Storage | Implemented as LPM |
| sdd-taxlien-parser-strategy | Logic | External orchestration |
| sdd-taxlien-parser-standalone | Mode | Integrated |
| sdd-taxlien-parser-ondemand | Mode | Integrated |
| sdd-taxlien-parser-bulk | Mode | Integrated |

### What Changed

The original architecture described `taxlien-parser` - a multi-platform monolith with:
- Celery workers
- Internal strategy mixing
- Platform-specific Python code

The new Universal Crawler is:
- Single-platform per instance
- JSON config-driven
- Externally orchestrated
- Domain-agnostic

---

## Context

This architecture document was updated to reflect the pivot from the original multi-platform `taxlien-parser` design to the new Universal Crawler approach.

The implementation is complete in `sdd-crawler/` - this document now accurately describes the implemented system.

---

## Document Location

`01-architecture.md` - Full architecture specification

---

## Next Steps

1. Maintain alignment between code and architecture doc
2. Add deployment diagrams as production deployments happen
3. Document external orchestration patterns as they evolve
