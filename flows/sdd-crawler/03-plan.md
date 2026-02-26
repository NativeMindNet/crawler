# Implementation Plan: Universal Single-Platform Crawler

**Version:** 1.0
**Status:** PLAN PHASE
**Last Updated:** 2026-02-26

**Specifications:** [02-specifications.md](02-specifications.md)

---

## 1. Task Breakdown

### Phase 1: Project Structure & Core Infrastructure (Tasks 1-8)

| Task | Description | Files | Complexity |
|------|-------------|-------|------------|
| 1.1 | Create project directory structure | `crawler/`, `tests/`, `config/` | Low |
| 1.2 | Create requirements.txt | `requirements.txt` | Low |
| 1.3 | Create Dockerfile | `Dockerfile` | Low |
| 1.4 | Create docker-compose.yml | `docker-compose.yml` | Low |
| 1.5 | Create .env.example | `.env.example` | Low |
| 1.6 | Create main entry point | `crawler/__main__.py` | Low |
| 1.7 | Create configuration loader | `crawler/config_loader.py` | Medium |
| 1.8 | Create platform config validator | `crawler/config_validator.py` | Medium |

### Phase 2: Local Persistence Manager (Tasks 2-10)

| Task | Description | Files | Complexity |
|------|-------------|-------|------------|
| 2.1 | Create SQLite database schema | `crawler/db/schema.sql` | Medium |
| 2.2 | Create database connection manager | `crawler/db/connection.py` | Medium |
| 2.3 | Create Task model and repository | `crawler/models/task.py`, `crawler/repositories/task_repo.py` | Medium |
| 2.4 | Create BulkJob model and repository | `crawler/models/bulk_job.py`, `crawler/repositories/bulk_job_repo.py` | Medium |
| 2.5 | Create DiscoveredLink model and repository | `crawler/models/discovered_link.py`, `crawler/repositories/link_repo.py` | Medium |
| 2.6 | Create LocalPersistenceManager class | `crawler/lpm.py` | High |
| 2.7 | Create file storage utilities | `crawler/storage.py` | Medium |
| 2.8 | Create state serialization (msgpack/pickle/JSON) | `crawler/state.py` | Medium |
| 2.9 | Write LPM unit tests | `tests/test_lpm.py` | High |
| 2.10 | Write repository tests | `tests/test_repositories.py` | Medium |

### Phase 3: Scraper Module (Tasks 3-16)

| Task | Description | Files | Complexity |
|------|-------------|-------|------------|
| 3.1 | Create ScrapedContent model | `crawler/models/scraped_content.py` | Low |
| 3.2 | Create SeleniumBase wrapper | `crawler/scraper/browser.py` | High |
| 3.3 | Create anti-bot challenge handler | `crawler/scraper/anti_bot.py` | High |
| 3.4 | Create screenshot capture on error | `crawler/scraper/screenshots.py` | Medium |
| 3.5 | Create retry logic with backoff | `crawler/scraper/retry.py` | Medium |
| 3.6 | Create main Scraper class | `crawler/scraper/scraper.py` | High |
| 3.7 | Create discovery extractor | `crawler/scraper/discovery.py` | Medium |
| 3.8 | Write scraper unit tests | `tests/test_scraper.py` | High |
| 3.9 | Write integration tests (mock server) | `tests/test_scraper_integration.py` | High |

### Phase 4: Parser Module (Tasks 4-14)

| Task | Description | Files | Complexity |
|------|-------------|-------|------------|
| 4.1 | Create ParsedResult model | `crawler/models/parsed_result.py` | Low |
| 4.2 | Create selector engine (CSS/XPath) | `crawler/parser/selector_engine.py` | Medium |
| 4.3 | Create mapping transformer | `crawler/parser/transformer.py` | Medium |
| 4.4 | Create data validator | `crawler/parser/validator.py` | Medium |
| 4.5 | Create main Parser class | `crawler/parser/parser.py` | High |
| 4.6 | Integrate image extraction (from sdd-photos) | `crawler/parser/image_extractor.py` | Medium |
| 4.7 | Create external link generator | `crawler/parser/external_links.py` | Medium |
| 4.8 | Create platform-specific parsers (QPublic example) | `crawler/parsers/qpublic.py` | Medium |
| 4.9 | Write parser unit tests | `tests/test_parser.py` | High |
| 4.10 | Write transformer tests | `tests/test_transformer.py` | Medium |
| 4.11 | Write image extractor tests | `tests/test_image_extractor.py` | Medium |

### Phase 5: Bulk Ingestion Module (Tasks 5-17)

| Task | Description | Files | Complexity |
|------|-------------|-------|------------|
| 5.1 | Create IngestionJob model | `crawler/models/ingestion_job.py` | Low |
| 5.2 | Create MappingProfile model | `crawler/models/mapping_profile.py` | Low |
| 5.3 | Create SourceReader interface | `crawler/bulk/readers/base.py` | Medium |
| 5.4 | Create CSV reader | `crawler/bulk/readers/csv_reader.py` | Medium |
| 5.5 | Create Excel reader | `crawler/bulk/readers/excel_reader.py` | Medium |
| 5.6 | Create GIS reader (Shapefile/GeoJSON) | `crawler/bulk/readers/gis_reader.py` | High |
| 5.7 | Create JSON/JSONL reader | `crawler/bulk/readers/json_reader.py` | Medium |
| 5.8 | Create Transformer pipeline | `crawler/bulk/transformer.py` | High |
| 5.9 | Create IngestionState manager | `crawler/bulk/state.py` | High |
| 5.10 | Create BulkIngestionPipeline | `crawler/bulk/pipeline.py` | High |
| 5.11 | Create idempotent upsert logic | `crawler/bulk/upsert.py` | Medium |
| 5.12 | Write bulk reader tests | `tests/test_bulk_readers.py` | High |
| 5.13 | Write pipeline tests | `tests/test_bulk_pipeline.py` | High |
| 5.14 | Write state management tests | `tests/test_bulk_state.py` | Medium |

### Phase 6: Imagery Service (Tasks 6-10)

| Task | Description | Files | Complexity |
|------|-------------|-------|------------|
| 6.1 | Create ExternalLinks model | `crawler/models/external_links.py` | Low |
| 6.2 | Create link generator (Google Maps, etc.) | `crawler/imagery/link_generator.py` | Medium |
| 6.3 | Create image downloader | `crawler/imagery/downloader.py` | Medium |
| 6.4 | Create ImageryService | `crawler/imagery/service.py` | Medium |
| 6.5 | Create YOLOv8 placeholder | `crawler/imagery/analyzer.py` | Low |
| 6.6 | Write imagery service tests | `tests/test_imagery_service.py` | Medium |

### Phase 7: API Layer (FastAPI) (Tasks 7-14)

| Task | Description | Files | Complexity |
|------|-------------|-------|------------|
| 7.1 | Create FastAPI app | `crawler/api/app.py` | Low |
| 7.2 | Create health endpoint | `crawler/api/routes/health.py` | Low |
| 7.3 | Create task endpoints | `crawler/api/routes/tasks.py` | High |
| 7.4 | Create scrape endpoint | `crawler/api/routes/scrape.py` | Medium |
| 7.5 | Create bulk endpoints | `crawler/api/routes/bulk.py` | High |
| 7.6 | Create config endpoints | `crawler/api/routes/config.py` | Medium |
| 7.7 | Create webhook test endpoint | `crawler/api/routes/webhooks.py` | Low |
| 7.8 | Create API schemas (Pydantic) | `crawler/api/schemas.py` | Medium |
| 7.9 | Create API middleware (logging, error handling) | `crawler/api/middleware.py` | Medium |
| 7.10 | Write API integration tests | `tests/test_api.py` | High |
| 7.11 | Write endpoint tests | `tests/test_api_routes.py` | High |

### Phase 8: CLI Layer (Typer) (Tasks 8-9)

| Task | Description | Files | Complexity |
|------|-------------|-------|------------|
| 8.1 | Create Typer CLI app | `crawler/cli.py` | Medium |
| 8.2 | Implement all CLI commands | `crawler/cli/commands/*.py` | High |
| 8.3 | Write CLI tests | `tests/test_cli.py` | Medium |

### Phase 9: Webhook Client (Tasks 9-4)

| Task | Description | Files | Complexity |
|------|-------------|-------|------------|
| 9.1 | Create WebhookPayload model | `crawler/webhooks/models.py` | Low |
| 9.2 | Create HMAC signer | `crawler/webhooks/signer.py` | Medium |
| 9.3 | Create WebhookClient | `crawler/webhooks/client.py` | High |
| 9.4 | Write webhook tests | `tests/test_webhooks.py` | Medium |

### Phase 10: Worker & Discovery Engine (Tasks 10-7)

| Task | Description | Files | Complexity |
|------|-------------|-------|------------|
| 10.1 | Create DiscoveryEngine | `crawler/discovery.py` | High |
| 10.2 | Create priority calculator | `crawler/priority.py` | Medium |
| 10.3 | Create Worker class | `crawler/worker.py` | High |
| 10.4 | Create worker loop (from standalone) | `crawler/worker_loop.py` | High |
| 10.5 | Create Gateway sync (optional) | `crawler/gateway_sync.py` | Medium |
| 10.6 | Write worker tests | `tests/test_worker.py` | High |
| 10.7 | Write discovery tests | `tests/test_discovery.py` | Medium |

### Phase 11: Platform Configurations (Tasks 11-3)

| Task | Description | Files | Complexity |
|------|-------------|-------|------------|
| 11.1 | Copy existing platform configs | `config/platforms/*/` | Low |
| 11.2 | Validate all 27 platform configs | `scripts/validate_configs.py` | Medium |
| 11.3 | Create config documentation | `config/README.md` | Low |

### Phase 12: Testing & Documentation (Tasks 12-6)

| Task | Description | Files | Complexity |
|------|-------------|-------|------------|
| 12.1 | Create pytest configuration | `pytest.ini`, `tests/conftest.py` | Low |
| 12.2 | Create test fixtures | `tests/fixtures/*.py` | Medium |
| 12.3 | Create end-to-end tests | `tests/test_e2e.py` | High |
| 12.4 | Create README.md | `README.md` | Medium |
| 12.5 | Create API documentation | `docs/api.md` | Medium |
| 12.6 | Create deployment guide | `docs/deployment.md` | Medium |

---

## 2. File Structure

```
crawler/
├── __init__.py
├── __main__.py                 # Entry point
├── config_loader.py
├── config_validator.py
├── lpm.py                      # Local Persistence Manager
├── storage.py
├── state.py
├── discovery.py
├── priority.py
├── worker.py
├── worker_loop.py
├── gateway_sync.py
│
├── models/
│   ├── __init__.py
│   ├── task.py
│   ├── bulk_job.py
│   ├── discovered_link.py
│   ├── scraped_content.py
│   ├── parsed_result.py
│   ├── ingestion_job.py
│   ├── mapping_profile.py
│   └── external_links.py
│
├── repositories/
│   ├── __init__.py
│   ├── task_repo.py
│   ├── bulk_job_repo.py
│   └── link_repo.py
│
├── db/
│   ├── __init__.py
│   ├── connection.py
│   └── schema.sql
│
├── scraper/
│   ├── __init__.py
│   ├── browser.py
│   ├── anti_bot.py
│   ├── screenshots.py
│   ├── retry.py
│   ├── scraper.py
│   └── discovery.py
│
├── parser/
│   ├── __init__.py
│   ├── selector_engine.py
│   ├── transformer.py
│   ├── validator.py
│   ├── parser.py
│   ├── image_extractor.py
│   └── external_links.py
│
├── parsers/
│   ├── __init__.py
│   ├── base.py
│   └── qpublic.py              # Example platform parser
│
├── bulk/
│   ├── __init__.py
│   ├── pipeline.py
│   ├── transformer.py
│   ├── state.py
│   ├── upsert.py
│   └── readers/
│       ├── __init__.py
│       ├── base.py
│       ├── csv_reader.py
│       ├── excel_reader.py
│       ├── gis_reader.py
│       └── json_reader.py
│
├── imagery/
│   ├── __init__.py
│   ├── link_generator.py
│   ├── downloader.py
│   ├── service.py
│   └── analyzer.py             # YOLOv8 placeholder
│
├── api/
│   ├── __init__.py
│   ├── app.py
│   ├── schemas.py
│   ├── middleware.py
│   └── routes/
│       ├── __init__.py
│       ├── health.py
│       ├── tasks.py
│       ├── scrape.py
│       ├── bulk.py
│       ├── config.py
│       └── webhooks.py
│
├── cli/
│   ├── __init__.py
│   └── commands/
│       ├── __init__.py
│       ├── scrape.py
│       ├── task.py
│       ├── bulk.py
│       ├── worker.py
│       └── config.py
│
├── webhooks/
│   ├── __init__.py
│   ├── models.py
│   ├── signer.py
│   └── client.py
│
└── tests/
    ├── __init__.py
    ├── conftest.py
    ├── test_lpm.py
    ├── test_repositories.py
    ├── test_scraper.py
    ├── test_scraper_integration.py
    ├── test_parser.py
    ├── test_transformer.py
    ├── test_image_extractor.py
    ├── test_bulk_readers.py
    ├── test_bulk_pipeline.py
    ├── test_bulk_state.py
    ├── test_imagery_service.py
    ├── test_api.py
    ├── test_api_routes.py
    ├── test_cli.py
    ├── test_webhooks.py
    ├── test_worker.py
    ├── test_discovery.py
    └── test_e2e.py

config/
└── platforms/
    ├── qpublic/
    │   ├── selectors.json
    │   ├── mapping.json
    │   ├── discovery.json
    │   ├── business_rules.json
    │   ├── schedule.json
    │   └── manifest.json
    ├── beacon/
    └── ... (27 platforms total)

tests/
└── fixtures/
    ├── __init__.py
    ├── html_samples.py
    ├── platform_configs.py
    └── mock_data.py

docs/
├── api.md
└── deployment.md

Dockerfile
docker-compose.yml
requirements.txt
README.md
.env.example
pytest.ini
```

---

## 3. Dependencies

### Python Packages (requirements.txt)

```
# Core
fastapi==0.109.0
uvicorn[standard]==0.27.0
typer==0.9.0
pydantic==2.5.3
pydantic-settings==2.1.0

# Scraping
seleniumbase==4.22.0
beautifulsoup4==4.12.3
lxml==5.1.0

# Bulk ingestion
pandas==2.2.0
openpyxl==3.1.2
geopandas==0.14.3
shapely==2.0.2
ijson==3.2.3

# State serialization
msgpack==1.0.7

# Database
aiosqlite==0.19.0

# HTTP client
httpx==0.26.0

# Images
Pillow==10.2.0

# Security (webhooks)
cryptography==42.0.0

# Testing
pytest==8.0.0
pytest-asyncio==0.23.4
pytest-cov==4.1.0
httpx==0.26.0  # For test client

# Utilities
python-dotenv==1.0.0
structlog==24.1.0
```

---

## 4. Testing Strategy

### Unit Tests (70%)
- Test individual components in isolation
- Mock external dependencies (browser, HTTP, filesystem)
- Focus on business logic

### Integration Tests (20%)
- Test component interactions
- Use test database (SQLite in-memory)
- Mock HTTP endpoints with httpx

### End-to-End Tests (10%)
- Full workflow tests with real browser
- Use test HTML samples
- Validate output files

### Test Execution Order
```bash
# Run all tests
pytest

# Run specific phase tests
pytest tests/test_lpm.py
pytest tests/test_scraper.py
pytest tests/test_parser.py

# Run with coverage
pytest --cov=crawler --cov-report=html
```

---

## 5. Implementation Order

### Sprint 1: Foundation (Tasks 1-2)
- Project structure
- LPM with SQLite
- Basic models and repositories

### Sprint 2: Scraping & Parsing (Tasks 3-4)
- Scraper with SeleniumBase
- Parser with config-driven selectors
- Image extraction

### Sprint 3: Bulk Ingestion (Tasks 5-6)
- All source readers
- Pipeline with state management
- Imagery service

### Sprint 4: API & CLI (Tasks 7-9)
- FastAPI endpoints
- Typer CLI commands
- Webhook client

### Sprint 5: Worker & Discovery (Tasks 10-12)
- Worker loop
- Discovery engine
- Platform configs
- Documentation

---

## 6. Risk Mitigation

| Risk | Mitigation |
|------|------------|
| SeleniumBase compatibility issues | Test early with target platforms |
| Anti-bot measures | Implement robust retry logic, use UC mode |
| Large file handling (bulk) | Stream processing, memory limits |
| SQLite concurrency | Use WAL mode, connection pooling |
| Webhook reliability | Retry logic, dead letter queue |

---

## 7. Definition of Done

Each task is complete when:
- [ ] Code implemented
- [ ] Unit tests written and passing
- [ ] Type hints added
- [ ] Docstrings for public APIs
- [ ] Logged with structlog
- [ ] Error handling implemented

---

## Next Step

After plan approval, begin **IMPLEMENTATION** phase starting with Task 1.1.
