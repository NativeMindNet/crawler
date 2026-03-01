# Status: sdd-crawler-architecture

**Current Phase:** IMPLEMENTATION (in progress)
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
- [x] Plan approved (2026-03-01)
- [ ] Implementation in progress
- [ ] Implementation complete

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
- [x] **v3.0: Removed async mode, Celery-only (2026-03-01)**
- [x] Plan approved (2026-03-01)
- [x] Implementation started (2026-03-01)
- [x] Codebase audit complete (2026-03-01)
- [ ] Proxy support implemented
- [ ] Rate limiting implemented
- [ ] Tests expanded
- [ ] Implementation complete

---

## Implementation Summary

**Audit Complete: 2026-03-01**

| Metric | Status |
|--------|--------|
| Overall Progress | ~85% complete |
| Tasks Complete | 14/19 (74%) |
| Files Implemented | ~68/~80 |

### Phase Status

| Phase | Status | Notes |
|-------|--------|-------|
| 1. Foundation | ✅ 100% | All complete |
| 2. Core Modules | ⚠️ 67% | Missing proxy + rate limiting |
| 3. Interfaces | ✅ 100% | All complete |
| 4. Advanced Features | ✅ 100% | All complete |
| 5. Testing & Deployment | ⚠️ 60% | Partial tests, Docker naming |

### Remaining Work

| Priority | Task | Files | TDD Spec |
|----------|------|-------|----------|
| HIGH | 2.4 Proxy Support | `proxy.py`, `proxy_pool.py` | ✅ `05-tdd-proxy.md` |
| HIGH | 2.5 Rate Limiting | `rate_limiter.py` | ✅ `05-tdd-rate-limiter.md` |
| MEDIUM | 2.6 Flower Config | `flower.conf.py` | ✅ `05-tdd-flower.md` |
| MEDIUM | 5.1 Unit Tests | 9 test files | 📋 See specs |
| LOW | 5.3 Docker Naming | File standardization | 📋 See specs |

---

## TDD/DDD/VDD Specifications

Created comprehensive test-driven development specifications for remaining work:

| Specification | Contents |
|---------------|----------|
| `05-tdd-proxy.md` | VDD (user stories), DDD (aggregates), TDD (20+ tests) |
| `05-tdd-rate-limiter.md` | VDD (rate limit stories), DDD (Token Bucket), TDD (25+ tests) |
| `05-tdd-flower.md` | VDD (monitoring stories), DDD (Flower context), TDD (integration tests) |

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
