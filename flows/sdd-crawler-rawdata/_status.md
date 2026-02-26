# Status: sdd-taxlien-parser-rawdata

## Current Phase

SPECIFICATIONS

## Phase Status

REVIEW (awaiting approval)

## Last Updated

2026-02-23 by Qwen

## Blockers

- None

## Progress

- [x] Requirements drafted
- [x] Requirements approved (2026-02-23)
- [x] Specifications drafted
- [ ] Specifications approved  ← current
- [ ] Plan drafted
- [ ] Plan approved
- [ ] Implementation started
- [ ] Implementation complete

## Context Notes

Key decisions and context for resuming:

- **Scope:** Raw data storage for scraped files (HTML, JSON, PDF, images)
- **Sources:** Current `orchestrator/storage/`, `storage/`, and `taxlien-storage/` patterns
- **Deployment:** Docker volumes (external bind mounts) for persistence
- **CI/CD:** Data preserved across deploys via host volumes

**Resolved decisions:**
- PDF/image deduplication: **per-parcel** (no global dedup)
- Failed scrape HTML: **don't keep** (temp debug for last attempt only)
- HTML compression: **yes**, compress to `.gz` after N days
- Imagery download timing: **out of scope** for this spec

## Fork History

- New SDD flow (not forked)
- Reason: Document and improve raw data storage architecture

## Next Actions

1. User reviews and approves requirements
2. Advance to SPECIFICATIONS phase
