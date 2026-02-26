# Architecture: Tax Lien Parser Module

**Version:** 1.0
**Status:** ARCHITECTURE DOCUMENT
**Last Updated:** 2026-02-11
**Scope:** Comprehensive architecture of the `taxlien-parser` module based on analysis of all existing SDD flows.

---

## 1. Executive Summary

The **taxlien-parser** module is a distributed, stateless data collection system designed to scrape, parse, and deliver tax lien/deed data from 3,000+ county websites across the United States. The architecture follows a **Gateway-centric** model where workers have minimal dependencies and communicate exclusively through a central API Gateway.

### Key Architectural Principles

| Principle | Description |
|-----------|-------------|
| **Stateless Workers** | Workers can run anywhere (local, AWS, DigitalOcean) with zero local state |
| **Gateway-Centric** | All storage, queue management, and coordination via API Gateway |
| **Platform Abstraction** | Each county platform (Beacon, QPublic, etc.) is isolated with its own scraper/parser |
| **Tiered Scraping** | Different HTTP clients for different anti-bot challenges |
| **Local-First Storage** | Results buffered locally before Gateway sync (resilience) |
| **Strategy-Driven** | Task selection via pluggable strategies (Freshness, Hotspot, Targeted) |

---

## 2. High-Level Architecture

```
+====================================================================================+
|                              TAXLIEN-PARSER ECOSYSTEM                               |
+====================================================================================+

                                  EXTERNAL SYSTEMS
    +------------------+     +------------------+     +------------------+
    |  County Websites |     |  Auction Sites   |     |  Enrichment APIs |
    |  (3000+ counties)|     | (Bid4Assets,etc) |     | (Legacy, Courts) |
    +--------+---------+     +--------+---------+     +--------+---------+
             |                        |                        |
             +------------------------+------------------------+
                                      |
                              [Internet / Tor Proxy]
                                      |
+=====================================================================================+
|                                 WORKER LAYER                                         |
|  (Distributed, Stateless, Horizontal Scaling)                                        |
+=====================================================================================+
|                                                                                      |
|   +--------------------------+    +--------------------------+                       |
|   |      WORKER INSTANCE     |    |      WORKER INSTANCE     |    ...N workers      |
|   |      (Docker Container)  |    |      (Cloud VM)          |                       |
|   +--------------------------+    +--------------------------+                       |
|   |                          |    |                          |                       |
|   | +----------------------+ |    | +----------------------+ |                       |
|   | |   EXECUTION MODES    | |    | |   EXECUTION MODES    | |                       |
|   | | - On-Demand (Gateway)| |    | | - On-Demand (Gateway)| |                       |
|   | | - Standalone (Local) | |    | | - Bulk Ingestion     | |                       |
|   | +----------------------+ |    | +----------------------+ |                       |
|   |                          |    |                          |                       |
|   | +----------------------+ |    | +----------------------+ |                       |
|   | |   SCRAPER ENGINE     | |    | |   SCRAPER ENGINE     | |                       |
|   | | Tier 1: aiohttp      | |    | | Tier 2: curl_cffi    | |                       |
|   | | Tier 2: curl_cffi    | |    | | Tier 3: Playwright   | |                       |
|   | | Tier 3: Playwright   | |    | | Tier 4: Selenium     | |                       |
|   | | Tier 4: Selenium     | |    | +----------------------+ |                       |
|   | +----------------------+ |    |                          |                       |
|   |                          |    | +----------------------+ |                       |
|   | +----------------------+ |    | |   PARSER ENGINE      | |                       |
|   | |   PARSER ENGINE      | |    | | - BeaconParser       | |                       |
|   | | - BeaconParser       | |    | | - QPublicParser      | |                       |
|   | | - QPublicParser      | |    | | - FloridaTaxParser   | |                       |
|   | | - FloridaTaxParser   | |    | | - AuctionParser      | |                       |
|   | | - PartyParser        | |    | +----------------------+ |                       |
|   | +----------------------+ |    |                          |                       |
|   |                          |    | +----------------------+ |                       |
|   | +----------------------+ |    | | LOCAL PERSISTENCE    | |                       |
|   | | LOCAL PERSISTENCE    | |    | | (SQLite + Files)     | |                       |
|   | | (SQLite + Files)     | |    | +----------------------+ |                       |
|   | +----------------------+ |    +--------------------------+                       |
|   +--------------------------+                                                       |
|             |                                                                        |
|             | Gateway API (HTTPS)                         Tor SOCKS5 (Direct)        |
|             |                                                    |                   |
+=====================================================================================+
              |                                                    |
              v                                                    v
+=====================================================================================+
|                              INFRASTRUCTURE LAYER                                    |
+=====================================================================================+
|                                                                                      |
|   +----------------------------------+        +----------------------------------+   |
|   |         API GATEWAY              |        |       TOR-SOCKS-PROXY           |   |
|   |     (api.taxlien.online)         |        |    (tor.taxlien.online)         |   |
|   +----------------------------------+        +----------------------------------+   |
|   |                                  |        |                                  |   |
|   |  INTERNAL API (Workers):         |        |  - Multiple Tor circuits         |   |
|   |  - GET  /internal/work           |        |  - IP rotation                   |   |
|   |  - POST /internal/results        |        |  - Ban management                |   |
|   |  - POST /internal/raw-files      |        |  - Geo-targeting (US)            |   |
|   |  - POST /internal/tasks/{id}/*   |        |                                  |   |
|   |  - POST /internal/heartbeat      |        |  NOTE: Gateway has NO knowledge  |   |
|   |                                  |        |  of proxy - workers connect      |   |
|   |  EXTERNAL API (Consumers):       |        |  directly to tor-socks-proxy     |   |
|   |  - GET  /v1/properties/*         |        |                                  |   |
|   |  - GET  /v1/search/*             |        +----------------------------------+   |
|   |  - POST /v1/predictions/*        |                                               |
|   |  - GET  /v1/top-lists/*          |                                               |
|   |  - GET  /v1/auctions/*           |                                               |
|   +----------------------------------+                                               |
|              |                                                                       |
|              v                                                                       |
|   +----------------------------------+        +----------------------------------+   |
|   |         POSTGRESQL               |        |           REDIS                  |   |
|   |        (Data Store)              |        |       (Queue + Cache)            |   |
|   +----------------------------------+        +----------------------------------+   |
|   |  - parcels                       |        |  - Task queues (by priority)     |   |
|   |  - tax_history                   |        |  - API response cache            |   |
|   |  - party_documents               |        |  - Rate limit counters           |   |
|   |  - owner_enrichment              |        |  - Worker heartbeat tracking     |   |
|   |  - auctions                      |        |                                  |   |
|   |  - auction_history               |        +----------------------------------+   |
|   +----------------------------------+                                               |
|                                                                                      |
|   +----------------------------------+                                               |
|   |       RAW FILE STORAGE           |                                               |
|   |   (/data/raw/ or S3/MinIO)       |                                               |
|   +----------------------------------+                                               |
|   |  - Individual HTML files (90d)   |                                               |
|   |  - Bulk archives (5 years)       |                                               |
|   |  - Manifest index (SQLite)       |                                               |
|   +----------------------------------+                                               |
|                                                                                      |
+=====================================================================================+
              |
              v
+=====================================================================================+
|                               CONSUMER LAYER                                         |
+=====================================================================================+
|                                                                                      |
|   +------------------+   +------------------+   +------------------+                 |
|   | taxlien-flutter  |   |  taxlien-ssr     |   |   taxlien-ml     |                 |
|   |   (Mobile App)   |   |   (Web Site)     |   |  (Predictions)   |                 |
|   +------------------+   +------------------+   +------------------+                 |
|          |                      |                      |                             |
|          +----------------------+----------------------+                             |
|                                 |                                                    |
|                          Gateway /v1/* API                                           |
|                                                                                      |
+=====================================================================================+
```

---

## 3. Component Catalog

### 3.1 Execution Modes

Based on analysis of:
- `sdd-taxlien-parser-parcel`
- `sdd-taxlien-parser-standalone`
- `sdd-taxlien-parser-ondemand`
- `sdd-taxlien-parser-bulk`

| Mode | Description | Task Source | Result Destination | Use Case |
|------|-------------|-------------|-------------------|----------|
| **On-Demand** | Real-time Gateway integration | Gateway `/internal/work` | Gateway `/internal/results` | Production scraping |
| **Standalone** | Infrastructure-independent | Local JSON/CSV files | Local filesystem | Emergency, benchmarking |
| **Bulk Ingestion** | Import static datasets | CSV/Shapefile/JSON files | Local + Gateway sync | GIS imports, Tax Rolls |

### 3.2 Scraper Tiers

From `sdd-taxlien-parser-parcel/02-specifications.md`:

| Tier | Technology | Anti-Bot Capability | Platforms | Concurrency |
|------|------------|---------------------|-----------|-------------|
| **Tier 1** | aiohttp | None (plain HTTP) | floridatax, actdata, county-taxes | 20+ threads |
| **Tier 2** | curl_cffi | TLS fingerprint impersonation | Beacon, QPublic | 5-10 threads |
| **Tier 3** | Playwright | Stealth browser, JS execution | Blocked Beacon sites | 2-5 threads |
| **Tier 4** | Selenium | Heavy Cloudflare bypass | Custom sites with WAF | 1-2 threads |

### 3.3 Parser Types

Based on existing flows:

| Parser Type | SDD Source | Data Domain | Output Schema |
|-------------|------------|-------------|---------------|
| **Parcel Parser** | `sdd-taxlien-parser-parcel` | Property data, tax amounts | `parcels` table |
| **Party Parser** | `sdd-taxlien-parser-party` | Owners, deeds, probate | `party_documents` table |
| **Auction Parser** | `sdd-auction-scraper` | Auction dates, registration | `auctions` table |
| **Enrichment Parser** | `sdd-taxlien-enrichment` | Obituaries, photos, family | `owner_enrichment` table |

### 3.4 Strategy Types

From `sdd-taxlien-parser-strategy`:

| Strategy | Logic | Purpose |
|----------|-------|---------|
| **Chronos** | `ORDER BY last_scraped_at ASC` | Freshness maintenance |
| **Hotspot** | Prioritize user-viewed regions | Reactive to demand |
| **Targeted** | Filter by `auction_date` proximity | Business deadlines |
| **Ripple** | Follow graph relations (neighbors, owners) | Context discovery |
| **Sweeper** | Sequential iteration (`ID > max_id`) | Blind discovery |
| **Seeded** | Search by keywords/names | Dictionary-based |

### 3.5 Platform Configurations

From `sdd-taxlien-parser-configs`:

```
platforms/{platform_name}/
├── scraper.py          # Network logic
├── parser.py           # Extraction logic
├── manifest.json       # Rate limits, Cloudflare, Proxy
├── counties.json       # County-to-Platform mapping
├── selectors.json      # DOM Selectors (CSS/XPath)
├── mapping.json        # Field mapping to Standard Schema
├── business_rules.json # Normalization, date formats
├── schedule.json       # Update frequency
└── discovery.json      # URL patterns, ID validation
```

---

## 4. Data Flow Diagrams

### 4.1 On-Demand Mode Flow

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│                           ON-DEMAND MODE DATA FLOW                                │
└──────────────────────────────────────────────────────────────────────────────────┘

    ┌─────────┐         ┌─────────────┐         ┌─────────────┐
    │ Gateway │         │   Worker    │         │ Tor Proxy   │
    │  (API)  │         │ (Stateless) │         │  (SOCKS5)   │
    └────┬────┘         └──────┬──────┘         └──────┬──────┘
         │                     │                       │
         │  1. GET /internal/work                      │
         │<────────────────────│                       │
         │                     │                       │
         │  2. Return tasks[]  │                       │
         │─────────────────────>                       │
         │  (parcel_ids, urls, │                       │
         │   platform, tier)   │                       │
         │                     │                       │
         │                     │  3. SOCKS5 request    │
         │                     │──────────────────────>│
         │                     │                       │
         │                     │                       │ 4. Forward to
         │                     │                       │    county site
         │                     │                       │──────────>
         │                     │                       │
         │                     │  5. HTML response     │
         │                     │<──────────────────────│
         │                     │                       │
         │                     │  6. Parse HTML        │
         │                     │  (platform-specific)  │
         │                     │                       │
         │                     │  7. Save to Local     │
         │                     │     SQLite (buffer)   │
         │                     │                       │
         │  8. POST /internal/results                  │
         │<────────────────────│                       │
         │    (batch of parsed │                       │
         │     parcel data)    │                       │
         │                     │                       │
         │  9. POST /internal/raw-files                │
         │<────────────────────│                       │
         │    (compressed HTML)│                       │
         │                     │                       │
         │  10. POST /internal/tasks/{id}/complete     │
         │<────────────────────│                       │
         │                     │                       │
    ┌────┴────┐         ┌──────┴──────┐         ┌──────┴──────┐
    │ Gateway │         │   Worker    │         │ Tor Proxy   │
    └─────────┘         └─────────────┘         └─────────────┘
```

### 4.2 Local Persistence Manager (LPM) Flow

From `sdd-taxlien-parser-localstorage`:

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│                      LOCAL PERSISTENCE MANAGER (LPM)                              │
└──────────────────────────────────────────────────────────────────────────────────┘

    ┌─────────────┐      ┌─────────────┐      ┌─────────────┐      ┌─────────────┐
    │   Gateway   │      │  Collector  │      │   Worker    │      │ Sync Service│
    │    (API)    │      │  (Puller)   │      │  (Scraper)  │      │ (Background)│
    └──────┬──────┘      └──────┬──────┘      └──────┬──────┘      └──────┬──────┘
           │                    │                    │                    │
           │  Every N seconds   │                    │                    │
           │<───────────────────│                    │                    │
           │ GET /internal/work │                    │                    │
           │───────────────────>│                    │                    │
           │     tasks[]        │                    │                    │
           │                    │                    │                    │
           │                    │  persist_tasks()   │                    │
           │                    │  status=PENDING    │                    │
           │                    │───────────────────>│                    │
           │                    │      SQLite        │                    │
           │                    │                    │                    │
           │                    │                    │ get_next_pending() │
           │                    │                    │<───────────────────│
           │                    │                    │                    │
           │                    │                    │ scrape()           │
           │                    │                    │──────┐             │
           │                    │                    │      │             │
           │                    │                    │<─────┘             │
           │                    │                    │                    │
           │                    │                    │ save_result()      │
           │                    │                    │ status=COMPLETED   │
           │                    │                    │ synced=false       │
           │                    │                    │───────────────────>│
           │                    │                    │                    │
           │                    │                    │                    │ Every M sec
           │                    │                    │                    │ get_unsynced()
           │                    │                    │<───────────────────│
           │                    │                    │                    │
           │ POST /internal/results                  │                    │
           │<────────────────────────────────────────┼────────────────────│
           │                    │                    │                    │
           │                    │                    │ mark_synced()      │
           │                    │                    │<───────────────────│
           │                    │                    │                    │
    ┌──────┴──────┐      ┌──────┴──────┐      ┌──────┴──────┐      ┌──────┴──────┐
    │   Gateway   │      │  Collector  │      │   Worker    │      │ Sync Service│
    └─────────────┘      └─────────────┘      └─────────────┘      └─────────────┘
```

---

## 5. Module Dependencies

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│                           MODULE DEPENDENCY GRAPH                                 │
└──────────────────────────────────────────────────────────────────────────────────┘

                              ┌─────────────────────┐
                              │  sdd-taxlien-gateway│
                              │  (External Service) │
                              └──────────┬──────────┘
                                         │
                                         │ HTTPS API
                                         │
          ┌──────────────────────────────┼──────────────────────────────┐
          │                              │                              │
          ▼                              ▼                              ▼
┌─────────────────────┐      ┌─────────────────────┐      ┌─────────────────────┐
│ sdd-parser-parcel   │      │ sdd-parser-party    │      │ sdd-auction-scraper │
│ (Core Parcel Data)  │      │ (Documents/History) │      │ (Auction Metadata)  │
└──────────┬──────────┘      └──────────┬──────────┘      └──────────┬──────────┘
           │                            │                            │
           └────────────────────────────┼────────────────────────────┘
                                        │
                                        ▼
                         ┌──────────────────────────┐
                         │  SHARED INFRASTRUCTURE   │
                         └──────────────────────────┘
                                        │
          ┌─────────────────────────────┼─────────────────────────────┐
          │                             │                             │
          ▼                             ▼                             ▼
┌─────────────────────┐     ┌─────────────────────┐     ┌─────────────────────┐
│ sdd-parser-configs  │     │ sdd-parser-strategy │     │ sdd-parser-storage  │
│ (Platform JSONs)    │     │ (Task Selection)    │     │ (LPM + Raw Files)   │
└─────────────────────┘     └─────────────────────┘     └─────────────────────┘
           │                            │                            │
           │                            │                            │
           ▼                            ▼                            ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                               EXECUTION MODES                                    │
├─────────────────────┬─────────────────────┬─────────────────────────────────────┤
│ sdd-parser-ondemand │ sdd-parser-standalone│       sdd-parser-bulk             │
│ (Gateway-connected) │ (Infrastructure-free)│       (File imports)              │
└─────────────────────┴─────────────────────┴─────────────────────────────────────┘
                                        │
                                        ▼
                         ┌──────────────────────────┐
                         │   sdd-parser-priority    │
                         │ (Delinquency-based)      │
                         └──────────────────────────┘
                                        │
                                        ▼
                         ┌──────────────────────────┐
                         │  sdd-taxlien-enrichment  │
                         │ (External Data Sources)  │
                         └──────────────────────────┘
```

---

## 6. Directory Structure

```
taxlien-parser/
├── flows/                              # SDD specifications
│   ├── sdd-taxlien-parser-architecture/  # THIS DOCUMENT
│   ├── sdd-taxlien-parser-parcel/        # Core parcel scraping
│   ├── sdd-taxlien-parser-party/         # Document/owner parsing
│   ├── sdd-taxlien-parser-configs/       # Platform configurations
│   ├── sdd-taxlien-parser-localstorage/  # LPM specifications
│   ├── sdd-taxlien-parser-strategy/      # Task selection strategies
│   ├── sdd-taxlien-parser-priority/      # Delinquency prioritization
│   ├── sdd-taxlien-parser-standalone/    # Offline mode
│   ├── sdd-taxlien-parser-ondemand/      # Gateway-connected mode
│   ├── sdd-taxlien-parser-bulk/          # Bulk file ingestion
│   ├── sdd-auction-scraper/              # Auction metadata
│   ├── sdd-taxlien-enrichment/           # External enrichment
│   ├── sdd-platforms-finder/             # Platform discovery
│   ├── sdd-platforms-sample-collector/   # Sample collection
│   └── sdd-miw-gift/                     # Arizona auction priority
│
├── worker/                             # Worker entry point
│   ├── __init__.py
│   ├── main.py                         # python -m worker.main
│   ├── runner.py                       # Execution loop
│   ├── config.py                       # WorkerConfig
│   └── metrics.py                      # Prometheus metrics
│
├── client/                             # Gateway communication
│   ├── __init__.py
│   ├── gateway.py                      # GatewayClient
│   └── models.py                       # Task, Result, etc.
│
├── scrapers/                           # HTTP clients by tier
│   ├── __init__.py
│   ├── base.py                         # BaseScraper
│   ├── factory.py                      # ScraperFactory
│   ├── tier1/
│   │   ├── http_scraper.py             # aiohttp
│   │   ├── floridatax.py
│   │   └── countytaxes.py
│   ├── tier2/
│   │   ├── curl_scraper.py             # curl_cffi
│   │   ├── beacon.py
│   │   └── qpublic.py
│   ├── tier3/
│   │   └── playwright_scraper.py
│   └── tier4/
│       └── selenium_scraper.py
│
├── parsers/                            # HTML extraction
│   ├── __init__.py
│   ├── base.py                         # BaseParser
│   ├── registry.py                     # ParserRegistry
│   └── platforms/
│       ├── beacon_parser.py
│       ├── qpublic_parser.py
│       ├── floridatax_parser.py
│       └── ...
│
├── platforms/                          # Platform configurations
│   ├── beacon/
│   │   ├── manifest.json
│   │   ├── counties.json
│   │   ├── selectors.json
│   │   └── ...
│   ├── qpublic/
│   └── ...
│
├── storage/                            # Local persistence
│   ├── __init__.py
│   ├── lpm.py                          # LocalPersistenceManager
│   ├── sync.py                         # Background sync service
│   └── models.py                       # SQLite models
│
├── strategies/                         # Task selection
│   ├── __init__.py
│   ├── base.py                         # BaseStrategy
│   ├── mixer.py                        # Strategy mixer
│   ├── chronos.py                      # Freshness
│   ├── hotspot.py                      # User signals
│   ├── targeted.py                     # Auction dates
│   └── ...
│
├── importers/                          # Bulk ingestion
│   ├── __init__.py
│   ├── csv_importer.py
│   ├── gis_importer.py
│   └── mapping_profiles/
│
├── configs/                            # Additional config
│   └── platforms/
│
├── tests/
│   ├── unit/
│   ├── integration/
│   └── fixtures/
│
├── Dockerfile
├── docker-compose.dev.yml
├── requirements.txt
└── pyproject.toml
```

---

## 7. Platform Coverage Matrix

Based on `sdd-platforms-finder` and `sdd-platforms-sample-collector`:

| Platform | Tier | Counties | Data Types | Priority |
|----------|------|----------|------------|----------|
| **beacon** | 2 | 183 | Assessor, Tax, GIS | HIGH |
| **qpublic** | 2 | 179 | Assessor, GIS | HIGH |
| **floridatax** | 1 | 67 | Tax only | HIGH |
| **county-taxes** | 1 | 30 | Tax only | MEDIUM |
| **actdata** | 1 | 47 | Assessor, Tax | MEDIUM |
| **arcountydata** | 1 | 44 | Assessor, Tax, Recorder | MEDIUM |
| **fidlar** | 1 | 35 | Recorder | LOW |
| **uslandrecords** | 1 | 26 | Recorder | LOW |
| **governmax** | 1 | 5 | Tax | LOW |
| **myfloridacounty** | 1 | 15 | Recorder | LOW |
| **Bid4Assets** | 1 | 1000+ | Auctions | MEDIUM |
| **RealAuction** | 1 | 500+ | Auctions | MEDIUM |

---

## 8. Priority Queues (MMP)

From `sdd-taxlien-parser-parcel`:

| Priority | Name | Max Wait | Use Case |
|----------|------|----------|----------|
| 1 | **Urgent** | <30s | User viewing parcel |
| 2 | **High** | <5m | Graph exploration |
| 3 | **Normal** | <1h | Background refresh |
| 4 | **Low** | <24h | Batch crawling |

---

## 9. Monitoring & Dashboards

### Required Grafana Panels

1. **Platform Health Matrix** - Per-platform success rate, last OK time
2. **Proxy Pool Status** - Available, banned, cooldown counts
3. **Worker Utilization** - Active tasks, throughput, queue depth
4. **Storage Metrics** - Raw files count, bulk archives, dedupe rate
5. **Priority Queue Depth** - By priority level, by platform

### Alert Thresholds

| Metric | Warning | Critical |
|--------|---------|----------|
| Platform success rate | <90% | <70% |
| Proxy available | <5 | <3 |
| Queue depth (urgent) | >100 | >500 |
| Worker utilization | <30% | <10% |
| Gateway latency | >500ms | >2s |

---

## 10. Development Stages

From `sdd-taxlien-parser-parcel`:

| Stage | Goal | Key Deliverables |
|-------|------|------------------|
| **MVP** | Prove scraping works | 3 platforms, 50K parcels, basic monitoring |
| **MMP** | Enable product features | All TIER 1+2, on-demand API, Grafana |
| **MLP** | Delight internal users | Full observability, 2M+ parcels |
| **PF** | Complete system | All platforms, 10M+ parcels, auto-scaling |

---

## 11. Cross-References

| SDD | Purpose | Status |
|-----|---------|--------|
| `sdd-taxlien-gateway` | API Gateway specifications | Active |
| `sdd-taxlien-parser-parcel` | Core parcel scraping | Active |
| `sdd-taxlien-parser-party` | Document/owner parsing | Active |
| `sdd-taxlien-parser-configs` | Platform configurations | In Progress |
| `sdd-taxlien-parser-localstorage` | Local persistence | In Progress |
| `sdd-taxlien-parser-strategy` | Task selection strategies | Draft |
| `sdd-taxlien-parser-priority` | Delinquency prioritization | Draft |
| `sdd-taxlien-parser-standalone` | Offline mode | Draft |
| `sdd-taxlien-parser-ondemand` | Gateway mode | Draft |
| `sdd-taxlien-parser-bulk` | Bulk ingestion | Draft |
| `sdd-auction-scraper` | Auction metadata | Draft |
| `sdd-taxlien-enrichment` | External enrichment | Draft |
| `sdd-miw-gift` | Arizona auction priority | Active |

---

## 12. Next Steps

1. **Consolidate** duplicate SDDs (parcel vs party parsers)
2. **Implement** LPM as foundation for all modes
3. **Standardize** platform configurations
4. **Build** Strategy Mixer with starvation protection
5. **Deploy** MVP for Arizona Feb 2026 auction

---

**Document Status:** ARCHITECTURE v1.0
**Last Updated:** 2026-02-11
**Author:** Claude (synthesized from existing SDDs)
