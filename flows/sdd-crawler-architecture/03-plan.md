# Implementation Plan: Universal Single-Platform Crawler Architecture

> **Version:** 1.0  
> **Status:** DRAFT  
> **Last Updated:** 2026-03-01  
> **Specifications:** [02-specifications.md](02-specifications.md)

---

## Summary

This plan implements the universal single-platform crawler architecture as specified. The implementation is organized into 5 phases:

1. **Foundation** - Core infrastructure (LPM, config loading, storage)
2. **Core Modules** - Scraper, parser, worker
3. **Interfaces** - API (FastAPI) and CLI (Typer)
4. **Advanced Features** - Bulk ingestion, imagery, webhooks, proxy support
5. **Testing & Deployment** - Tests, Docker, documentation

---

## Task Breakdown

### Phase 1: Foundation

#### Task 1.1: Project Structure Setup
- **Description**: Create crawler module directory structure
- **Files**:
  - `crawler/__init__.py` - Create
  - `crawler/__main__.py` - Create (entry point)
  - `crawler/models/` - Create directory
  - `crawler/repositories/` - Create directory
  - `crawler/db/` - Create directory
  - `crawler/scraper/` - Create directory
  - `crawler/parser/` - Create directory
  - `crawler/bulk/` - Create directory
  - `crawler/imagery/` - Create directory
  - `crawler/api/` - Create directory
  - `crawler/cli/` - Create directory
  - `crawler/webhooks/` - Create directory
  - `crawler/tests/` - Create directory
- **Dependencies**: None
- **Verification**: Directory structure matches spec
- **Complexity**: Low

#### Task 1.2: Data Models
- **Description**: Define core data models using dataclasses
- **Files**:
  - `crawler/models/task.py` - Create (Task, TaskStatus)
  - `crawler/models/scraped_content.py` - Create
  - `crawler/models/parsed_result.py` - Create
  - `crawler/models/bulk_job.py` - Create
  - `crawler/models/external_links.py` - Create
  - `crawler/models/mapping_profile.py` - Create
- **Dependencies**: Task 1.1
- **Verification**: Models importable, type hints correct
- **Complexity**: Low

#### Task 1.3: Local Persistence Manager (LPM)
- **Description**: SQLite-based task queue and result storage
- **Files**:
  - `crawler/lpm.py` - Create
  - `crawler/storage.py` - Create
  - `crawler/state.py` - Create
  - `crawler/db/connection.py` - Create
  - `crawler/db/schema.py` - Create
  - `crawler/repositories/task_repo.py` - Create
- **Dependencies**: Task 1.2
- **Verification**: Can queue tasks, store results, query by status
- **Complexity**: Medium

#### Task 1.4: Config Loader
- **Description**: Load and validate platform JSON configs
- **Files**:
  - `crawler/config_loader.py` - Create
  - `crawler/config_validator.py` - Create
  - `config/platforms/` - Create directory
  - `config/platforms/.gitkeep` - Create
- **Dependencies**: Task 1.2
- **Verification**: Can load manifest, selectors, mapping configs
- **Complexity**: Low

---

### Phase 2: Core Modules

#### Task 2.1: Scraper Module
- **Description**: SeleniumBase wrapper with anti-bot and retry logic
- **Files**:
  - `crawler/scraper/browser.py` - Create
  - `crawler/scraper/anti_bot.py` - Create
  - `crawler/scraper/retry.py` - Create
  - `crawler/scraper/screenshots.py` - Create
  - `crawler/scraper/scraper.py` - Create
- **Dependencies**: Task 1.2, Task 1.4
- **Verification**: Can fetch HTML from test URLs
- **Complexity**: High

#### Task 2.2: Parser Module
- **Description**: HTML parsing with CSS/XPath selectors
- **Files**:
  - `crawler/parser/selector_engine.py` - Create
  - `crawler/parser/transformer.py` - Create
  - `crawler/parser/validator.py` - Create
  - `crawler/parser/parser.py` - Create
  - `crawler/parser/image_extractor.py` - Create
  - `crawler/parser/external_links.py` - Create
- **Dependencies**: Task 1.2, Task 1.4
- **Verification**: Can extract data using selectors.json
- **Complexity**: Medium

#### Task 2.3: Worker (Dual Mode)
- **Description**: Task processing worker (Async and Celery modes)
- **Files**:
  - `crawler/worker.py` - Create
  - `crawler/priority.py` - Create
  - `crawler/discovery.py` - Create
- **Dependencies**: Task 1.3, Task 2.1, Task 2.2
- **Verification**: Worker processes queue in priority order
- **Complexity**: High

#### Task 2.4: Proxy Support
- **Description**: SOCKS5 proxy integration (plain + tor)
- **Files**:
  - `crawler/scraper/proxy.py` - Create
  - `crawler/scraper/proxy_pool.py` - Create
- **Dependencies**: Task 2.1
- **Verification**: Can route requests through SOCKS proxy
- **Complexity**: Medium

#### Task 2.5: Rate Limiting
- **Description**: Per-domain rate limiting
- **Files**:
  - `crawler/scraper/rate_limiter.py` - Create
- **Dependencies**: Task 2.1
- **Verification**: Respects configured rate limits per domain
- **Complexity**: Medium

---

### Phase 3: Interfaces

#### Task 3.1: FastAPI API
- **Description**: HTTP API endpoints
- **Files**:
  - `crawler/api/app.py` - Create
  - `crawler/api/schemas.py` - Create
  - `crawler/api/middleware.py` - Create
  - `crawler/api/routes/health.py` - Create
  - `crawler/api/routes/tasks.py` - Create
  - `crawler/api/routes/scrape.py` - Create
  - `crawler/api/routes/bulk.py` - Create
  - `crawler/api/routes/config.py` - Create
  - `crawler/api/routes/webhooks.py` - Create
- **Dependencies**: Task 1.3, Task 2.3
- **Verification**: API endpoints respond correctly
- **Complexity**: Medium

#### Task 3.2: Typer CLI
- **Description**: Command-line interface
- **Files**:
  - `crawler/cli/__init__.py` - Create
  - `crawler/cli/commands/scrape.py` - Create
  - `crawler/cli/commands/task.py` - Create
  - `crawler/cli/commands/bulk.py` - Create
  - `crawler/cli/commands/worker.py` - Create
  - `crawler/cli/commands/config.py` - Create
- **Dependencies**: Task 1.3, Task 2.3
- **Verification**: CLI commands execute correctly
- **Complexity**: Medium

---

### Phase 4: Advanced Features

#### Task 4.1: Bulk Ingestion Pipeline
- **Description**: CSV/Excel/GIS/JSON bulk import
- **Files**:
  - `crawler/bulk/pipeline.py` - Create
  - `crawler/bulk/transformer.py` - Create
  - `crawler/bulk/state.py` - Create
  - `crawler/bulk/upsert.py` - Create
  - `crawler/bulk/readers/csv_reader.py` - Create
  - `crawler/bulk/readers/excel_reader.py` - Create
  - `crawler/bulk/readers/gis_reader.py` - Create
  - `crawler/bulk/readers/json_reader.py` - Create
  - `crawler/repositories/bulk_job_repo.py` - Create
- **Dependencies**: Task 1.3, Task 2.2
- **Verification**: Can ingest bulk data from CSV
- **Complexity**: High

#### Task 4.2: Imagery Service
- **Description**: Image link generation and download
- **Files**:
  - `crawler/imagery/link_generator.py` - Create
  - `crawler/imagery/downloader.py` - Create
  - `crawler/imagery/service.py` - Create
  - `crawler/imagery/analyzer.py` - Create (YOLOv8 placeholder)
  - `crawler/repositories/link_repo.py` - Create
- **Dependencies**: Task 1.3, Task 2.2
- **Verification**: Can generate and download property images
- **Complexity**: Medium

#### Task 4.3: Webhook Notifications
- **Description**: HMAC-signed webhook delivery
- **Files**:
  - `crawler/webhooks/models.py` - Create
  - `crawler/webhooks/signer.py` - Create
  - `crawler/webhooks/client.py` - Create
  - `crawler/gateway_sync.py` - Create
- **Dependencies**: Task 1.2
- **Verification**: Webhooks delivered with valid signatures
- **Complexity**: Medium

---

### Phase 5: Testing & Deployment

#### Task 5.1: Unit Tests
- **Description**: Test core modules
- **Files**:
  - `crawler/tests/conftest.py` - Create
  - `crawler/tests/test_lpm.py` - Create
  - `crawler/tests/test_config_loader.py` - Create
  - `crawler/tests/test_selector_engine.py` - Create
  - `crawler/tests/test_transformer.py` - Create
  - `crawler/tests/test_priority.py` - Create
  - `crawler/tests/test_webhook_signer.py` - Create
  - `crawler/tests/test_proxy.py` - Create
  - `crawler/tests/test_rate_limiter.py` - Create
- **Dependencies**: All implementation tasks
- **Verification**: All unit tests pass
- **Complexity**: Medium

#### Task 5.2: Integration Tests
- **Description**: End-to-end tests
- **Files**:
  - `crawler/tests/test_worker.py` - Create
  - `crawler/tests/test_discovery.py` - Create
  - `crawler/tests/test_bulk_pipeline.py` - Create
  - `crawler/tests/test_api.py` - Create
  - `crawler/tests/test_gateway_sync.py` - Create
  - `crawler/tests/test_imagery_service.py` - Create
- **Dependencies**: Task 5.1
- **Verification**: Integration tests pass
- **Complexity**: High

#### Task 5.3: Docker Deployment
- **Description**: Docker Compose configurations
- **Files**:
  - `Dockerfile.crawler` - Create (or update existing)
  - `docker-compose.crawler.yml` - Create
  - `docker-compose.crawler.celery.yml` - Create
- **Dependencies**: Task 3.1, Task 3.2
- **Verification**: Can start crawler via docker-compose
- **Complexity**: Medium

#### Task 5.4: Documentation
- **Description**: README and usage docs
- **Files**:
  - `crawler/README.md` - Create
  - `config/platforms/README.md` - Create
- **Dependencies**: All tasks
- **Verification**: Documentation complete
- **Complexity**: Low

---

## Dependency Graph

```
Phase 1: Foundation
├─ 1.1 Structure ─┬─→ 1.2 Models ─┬─→ 1.3 LPM ─┬─→ 2.3 Worker ─┬─→ 3.1 API
│                 │               │             │               └─→ 3.2 CLI
│                 │               │             │
│                 │               ├─→ 1.4 Config ─┬─→ 2.1 Scraper ─┬─→ 2.4 Proxy
│                 │               │               │                ├─→ 2.5 Rate Limit
│                 │               │               │                └─→ 2.2 Parser ─┬─→ 4.1 Bulk
│                 │               │               │                                └─→ 4.2 Imagery
│                 │               │               │
│                 │               │               └─→ 4.3 Webhooks
│                 │               │
└─────────────────┴───────────────┘

Phase 5: Testing & Deployment (depends on all above)
├─ 5.1 Unit Tests
├─ 5.2 Integration Tests
├─ 5.3 Docker
└─ 5.4 Documentation
```

---

## File Change Summary

| Directory | Files to Create | Purpose |
|-----------|-----------------|---------|
| `crawler/` | 6 | Core modules (lpm, storage, state, worker, priority, discovery, gateway_sync, config_loader, config_validator) |
| `crawler/models/` | 6 | Data models |
| `crawler/repositories/` | 4 | Database access layer |
| `crawler/db/` | 2 | SQLite connection and schema |
| `crawler/scraper/` | 7 | Web scraping (browser, anti_bot, retry, screenshots, scraper, proxy, proxy_pool, rate_limiter) |
| `crawler/parser/` | 6 | HTML parsing |
| `crawler/bulk/` | 8 | Bulk ingestion pipeline |
| `crawler/imagery/` | 4 | Image processing |
| `crawler/api/` | 8 | FastAPI routes |
| `crawler/cli/` | 7 | Typer CLI commands |
| `crawler/webhooks/` | 3 | Webhook handling |
| `crawler/tests/` | 15 | Unit and integration tests |
| `config/platforms/` | 1 | Platform config directory |
| Root | 3 | Docker Compose files |

**Total:** ~76 new files

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| SeleniumBase anti-bot detection | Medium | High | Test against real platforms early |
| Proxy rotation complexity | Medium | Medium | Start with single proxy, add pool later |
| Rate limiting edge cases | Low | Medium | Conservative defaults, configurable |
| Bulk ingestion performance | Medium | Low | Stream large files, batch inserts |
| Celery mode setup complexity | Low | Low | Document clearly, provide examples |

---

## Rollback Strategy

If implementation needs to be reverted:

1. Delete `crawler/` directory (new module, no existing code affected)
2. Delete `config/platforms/` directory
3. Remove any docker-compose references
4. Restore `requirements.txt` if new dependencies added

---

## Checkpoints

### After Phase 1
- [ ] Models defined and importable
- [ ] LPM can queue/retrieve tasks
- [ ] Config loader reads JSON configs

### After Phase 2
- [ ] Scraper can fetch HTML
- [ ] Parser extracts data correctly
- [ ] Worker processes queue
- [ ] Proxy support functional
- [ ] Rate limiting enforced

### After Phase 3
- [ ] API endpoints respond
- [ ] CLI commands work

### After Phase 4
- [ ] Bulk ingestion works
- [ ] Imagery service functional
- [ ] Webhooks delivered

### After Phase 5
- [ ] All tests pass
- [ ] Docker deployment works
- [ ] Documentation complete

---

## Open Implementation Questions

- [ ] Should we support HTTP proxy in addition to SOCKS5?
- [ ] Should bulk ingestion support database sources (PostgreSQL, MySQL)?
- [ ] What's the default rate limit for unknown domains?

---

## Approval

- [ ] Reviewed by: [name]
- [ ] Approved on: [date]
- [ ] Notes: [any conditions or clarifications]
