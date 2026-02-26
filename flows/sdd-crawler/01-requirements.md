# Requirements: Universal Single-Platform Crawler

**Version:** 1.0
**Status:** REQUIREMENTS PHASE
**Last Updated:** 2026-02-26

---

## 1. Problem Statement

All existing SDD flows and the legacy-celery codebase were designed for **multi-platform tax-lien crawling**. This creates:
- Unnecessary complexity for single-platform use cases
- Tight coupling to tax-lien domain logic
- Difficulty integrating into external ecosystems that need platform-specific crawler instances

## 2. Goal

Build a **universal crawler** that:
- Handles **ONE specific platform** per instance (configured at runtime)
- Supports both **scraping** (HTML download) and **parsing** (data extraction) operations
- Can be called from an external ecosystem
- Is **not limited to tax-lien data** - works with any platform configuration

## 3. User Stories

### US-1: External System Integration
**As** an external system orchestrator
**I want** to instantiate a crawler for a specific platform via API or CLI
**So that** I can run multiple independent crawler instances for different platforms in Docker

**Acceptance Criteria:**
- [ ] Crawler exposes HTTP API for task submission and status
- [ ] Crawler supports CLI for one-off operations
- [ ] Crawler accepts platform configuration at startup
- [ ] Each instance operates independently with its own configuration
- [ ] No shared state between crawler instances
- [ ] Docker-ready with volume mounts for results

### US-2: Platform Configuration
**As** a platform operator
**I want** to configure the crawler for my platform's specific structure
**So that** it can scrape and parse data correctly

**Acceptance Criteria:**
- [ ] Configuration defines selectors, mapping, and discovery rules
- [ ] Configuration is loaded from external files (JSON)
- [ ] Compatible with existing 27 platform configs from `sdd-crawler-platform-config`
- [ ] No code changes needed to support a new platform

### US-3: Scraping Operation
**As** a user
**I want** to scrape HTML from platform URLs
**So that** I can store raw data for later processing

**Acceptance Criteria:**
- [ ] Crawler can fetch URLs and save HTML
- [ ] Supports browser automation (SeleniumBase) for dynamic content
- [ ] Handles anti-bot challenges
- [ ] Saves raw files (HTML, PDF, images) to Docker volume

### US-4: Parsing Operation
**As** a user
**I want** to parse scraped HTML into structured data
**So that** I can import it into a database or use it programmatically

**Acceptance Criteria:**
- [ ] Parser uses platform-specific selectors from configuration
- [ ] Output is structured JSON matching the platform's schema
- [ ] Can parse both single pages and batch process
- [ ] Supports discovery of related URLs (Ripple Effect from standalone/ondemand)

### US-5: Bulk Operations
**As** a user (from `sdd-crawler-bulk`)
**I want** to import static datasets (CSV, GIS Shapefiles, Tax Rolls)
**So that** I can populate data without web crawling

**Acceptance Criteria:**
- [ ] Supports CSV, Excel, GIS formats (Shapefile, GeoJSON), JSON/JSONL
- [ ] Mapping profiles for column transformation
- [ ] Streaming for large files (>1GB)
- [ ] Resumable ingestion with state tracking (msgpack/pickle/JSON)
- [ ] Idempotent upsert based on parcel_id + county + state

### US-6: Imagery & Photos
**As** a user (from `sdd-crawler-photos`)
**I want** to extract property photos and generate external mapping links
**So that** I have complete property imagery data

**Acceptance Criteria:**
- [ ] Extract images from HTML using `BaseParser.extract_images()`
- [ ] Generate Google Maps/Street View/Satellite/Bing links
- [ ] Support all platform parsers (Beacon, QPublic, FloridaTax, etc.)
- [ ] Download images to Docker volume
- [ ] Optional: YOLOv8 analysis for property condition (placeholder)

### US-7: Notifications (Webhooks)
**As** an external system
**I want** to receive webhook notifications when scraping completes
**So that** I can react to completed tasks in real-time

**Acceptance Criteria:**
- [ ] Webhook sent per-item (single URL scraped)
- [ ] Webhook sent for bulk completion (batch finished)
- [ ] Configurable webhook endpoints
- [ ] Retry logic for failed webhook delivery
- [ ] Payload includes task ID, status, and result paths

### US-8: Local Persistence & Resume (from standalone/ondemand)
**As** an operator
**I want** tasks and results persisted locally with resume capability
**So that** I don't lose progress on crashes or restarts

**Acceptance Criteria:**
- [ ] Local SQLite for task queue and state tracking
- [ ] Priority-aware task scheduling (from ondemand)
- [ ] Resume from last checkpoint (`--resume`)
- [ ] Local Ripple Effect: discovered links auto-added to queue
- [ ] Optional: Sync to external Gateway when available

## 4. Constraints

- **C-1**: Must work with existing platform configurations (27 platforms from `sdd-crawler-platform-config`)
- **C-2**: Must support SeleniumBase for browser automation (legacy compatibility)
- **C-3**: Must be Docker-ready with volume mounts for results
- **C-4**: Must integrate patterns from existing SDD flows:
  - **On-demand**: Gateway task collector, async result delivery, real-time feedback loop
  - **Standalone**: Autonomous loop, seed & discovery, local ripple effect, resume capability
  - **Bulk**: Multi-format ingestion (CSV/GIS/JSON), mapping profiles, state management (msgpack/pickle/JSON)
  - **Photos**: Unified imagery extraction, external mapping links, YOLOv8 placeholder
- **C-5**: Webhook notifications for task completion (single + bulk)
- **C-6**: Local SQLite persistence for task queue and state tracking

## 5. Non-Goals

- **NG-1**: Multi-platform crawling in a single instance (each instance handles ONE platform)
- **NG-2**: Tax-lien specific logic (keep domain-agnostic, compatible with existing configs)
- **NG-3**: Mandatory Gateway API (standalone operation supported, optional sync)
- **NG-4**: Distributed task queue (no Celery dependency - simplify from legacy-celery)
- **NG-5**: Complex CV analysis (YOLOv8 is placeholder, not initial implementation)

## 6. Open Questions

1. **Q1 - API Design**: REST API with FastAPI? Or Flask? What endpoints are essential vs nice-to-have?
2. **Q2 - Webhook Security**: Should webhooks include signatures/HMAC for verification?
3. **Q3 - Priority Model**: How to handle task priorities (from ondemand SDD)? Config-driven or API-specified?
4. **Q4 - Rate Limiting**: Should rate limiting be config-driven (per-platform) or built-in logic?
5. **Q5 - Bulk vs Real-time**: Should bulk ingestion be a separate CLI command or integrated into the API?

---

## Next Phase

After requirements are approved, move to **SPECIFICATIONS** phase to define:
- Architecture and component design
- Data models and interfaces
- Integration points with external ecosystem
