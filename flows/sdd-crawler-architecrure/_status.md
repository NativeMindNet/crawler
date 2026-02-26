# Status: sdd-taxlien-parser-architecture

**Current Phase:** ARCHITECTURE
**Last Updated:** 2026-02-11

## Progress

- [x] Analyze existing SDD flows (17 flows analyzed)
- [x] Identify parser components and relationships
- [x] Create architecture document

## Key Findings from Analysis

### Existing SDDs Analyzed

| SDD | Type | Status | Key Insights |
|-----|------|--------|--------------|
| sdd-taxlien-parser-parcel | Core | Active | Stateless worker model, Gateway-centric |
| sdd-taxlien-parser-party | Documents | Active | Party documents, probate, deeds |
| sdd-taxlien-parser-configs | Config | In Progress | Platform configuration standardization |
| sdd-taxlien-parser-localstorage | Storage | Draft | LPM, SQLite buffering |
| sdd-taxlien-parser-strategy | Logic | Draft | Task selection strategies |
| sdd-taxlien-parser-priority | Logic | Draft | Delinquency-based prioritization |
| sdd-taxlien-parser-standalone | Mode | Draft | Infrastructure-independent |
| sdd-taxlien-parser-ondemand | Mode | Draft | Gateway-connected mode |
| sdd-taxlien-parser-bulk | Mode | Draft | File imports |
| sdd-auction-scraper | Feature | Draft | Auction metadata |
| sdd-taxlien-enrichment | Feature | Draft | External data sources |
| sdd-platforms-finder | Discovery | Complete | Platform identification |
| sdd-platforms-sample-collector | Discovery | Complete | Sample collection |
| sdd-platforms-sample-collector-v2 | Discovery | Complete | Enhanced collection |
| sdd-platforms-summary | Report | Complete | Coverage matrix |
| sdd-miw-gift | Priority | Active | Arizona Feb 2026 focus |
| sdd-auction-dates | Feature | Draft | Auction date tracking |

### Architecture Highlights

1. **Gateway-Centric Model**: Workers have ZERO direct DB/Redis access
2. **Proxy Independence**: Workers manage tor-socks-proxy directly (Gateway has no proxy knowledge)
3. **Local-First Storage**: LPM buffers results for resilience
4. **Tiered Scraping**: 4 tiers from simple HTTP to heavy Selenium
5. **Strategy-Driven**: Pluggable task selection (Chronos, Hotspot, Targeted, etc.)

### Identified Gaps

1. No unified implementation of LPM yet
2. Strategy Mixer not implemented
3. Platform configs not fully standardized
4. Bulk importer needs state management

## Recommendations

1. **Prioritize LPM**: Foundation for all execution modes
2. **Consolidate Parser SDDs**: Merge overlapping parcel/party concerns
3. **Implement Strategy Mixer**: With starvation protection
4. **Standardize Configs**: Complete JSON-based platform configs
5. **Arizona Focus**: Align all work with Feb 2026 deadline

## Document Location

`/taxlien-parser/flows/sdd-taxlien-parser-architecture/01-architecture.md`

---

**Next Action:** Review architecture with stakeholders, begin LPM implementation
