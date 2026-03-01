# Status: sdd-crawler-architecture

> **SDD Flow Status Page**
> Note: Originally named "sdd-crawler-architecrure" (with typo)

**Current Phase:** DRAFTED (pending review)
**Last Updated:** 2026-03-01
**Version:** 2.0

---

## Goals

- [x] Document universal single-platform crawler architecture
- [x] Clarify pivot from multi-platform (taxlien-parser) design
- [x] Define external orchestration model
- [x] Document component catalog
- [x] Define deployment options (Docker, K8s)

---

## Progress

- [x] Initial architecture v1.0 (multi-platform, 2026-02-11)
- [x] Architecture v2.0 update (single-platform pivot, 2026-03-01)
- [x] Comparison table: old vs new design
- [x] Deployment examples (docker-compose, kubernetes)

---

## Key Changes in v2.0

### Architectural Pivot

| Aspect | v1.0 (Old) | v2.0 (New) |
|--------|------------|------------|
| Scope | Multi-platform in one codebase | Single-platform per instance |
| Domain | Tax-lien specific | Domain-agnostic |
| Worker | Celery distributed | Async single-process |
| Orchestration | Internal strategy mixer | External (Gateway/Scheduler) |
| Scaling | Celery worker count | Container instances |

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
