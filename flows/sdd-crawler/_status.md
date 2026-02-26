# Status: sdd-crawler

> **SDD Flow Status Page**
> See: [sdd.md](../sdd.md) for flow reference

**Current Phase:** IMPLEMENTATION (in progress)
**Last Updated:** 2026-02-26
**Version:** 1.0

---

## Goals

- [ ] Create universal single-platform crawler architecture
- [ ] Decouple from multi-platform tax-lien specific design
- [ ] Enable external ecosystem to instantiate crawler per platform
- [ ] Support scrap + parse operations for ONE platform per instance
- [ ] Integrate patterns from existing SDD flows (ondemand, standalone, bulk, photos)
- [ ] Docker-ready with API + CLI interface
- [ ] Webhook notifications for task completion
- [ ] Local persistence with resume capability

---

## Progress

- [x] Initialize SDD flow
- [x] Analyze existing SDD flows (ondemand, standalone, bulk, photos)
- [x] Analyze legacy-celery codebase
- [x] Requirements drafted (v1.0) - 8 user stories
- [x] Requirements approved
- [x] Specifications drafted (v1.0) - Architecture, components, data models
- [x] Specifications approved
- [x] Plan drafted (v1.0) - 12 phases, 70+ tasks
- [x] Plan approved
- [x] README.md created
- [ ] Implementation started ← **CURRENT**
- [ ] Implementation complete

---

## Context Notes

### Key Decisions
- **Pivot from multi-platform to single-platform**: All previous SDD flows were designed for multi-platform tax-lien crawling. This new crawler will be universal and handle ONE platform per instance.
- **External ecosystem integration**: The crawler will be called from outside, with separate instances running for different platforms.
- **Universal design**: Not limited to tax-lien data - can support any platform configuration.
- **Docker-first**: Will be deployed in Docker with volume mounts for results (HTML, PDF, images, JSON).
- **API + CLI**: Both interfaces for flexibility.

### Legacy Analysis
- **legacy-celery**: Celery-based distributed crawling with platform-specific tasks (e.g., `qpublic_functions.py`)
- **Existing SDD flows**: All designed for multi-platform tax-lien crawling, need to be re-architected
- **Platform config work**: `sdd-crawler-platform-config` completed 27 platforms with 7 config types each (189 files total)

### Integrated SDD Patterns
- **On-demand**: Gateway task collector, async result delivery, real-time feedback loop
- **Standalone**: Autonomous loop, seed & discovery, local ripple effect, resume capability  
- **Bulk**: Multi-format ingestion (CSV/GIS/JSON), mapping profiles, state management (msgpack/pickle/JSON)
- **Photos**: Unified imagery extraction, external mapping links, YOLOv8 placeholder

### Resumability
New session: Read this file first, then `01-requirements.md` for detailed requirements.

---

## Next Steps

1. Phase 1: Project Structure & Core Infrastructure
2. Phase 2: Local Persistence Manager
3. Phase 3: Scraper Module
4. Continue through all 12 phases
