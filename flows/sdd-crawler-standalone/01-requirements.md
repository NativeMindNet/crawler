# Requirements: Standalone Mode (Infrastructure Independence)

**Version:** 0.2
**Status:** REQUIREMENTS PHASE
**Last Updated:** 2026-01-30

---

## 1. Problem Statement
Current workers stop working if the central Gateway API is down, under maintenance, or overloaded. This creates a single point of failure and prevents emergency data collection when infrastructure issues occur.

## 2. Goal
Enable workers to execute scraping tasks provided via local sources (CLI/Files) and store results locally, bypassing the Gateway entirely for both task acquisition and result submission.

## 3. Key Scenarios

### Scenario A: Emergency Collection
The Gateway is down for maintenance, but an auction starts in 1 hour.
- **Action**: Operator provides a CSV with parcel URLs directly to the worker.
- **Outcome**: Worker scrapes data and saves it to local JSON/HTML files.

### Scenario B: Performance Benchmarking
Testing a new parser version without polluting the production database.
- **Action**: Run worker with `--standalone` on a sample set.
- **Outcome**: Results are reviewed locally in `./output`.

## 4. Functional Requirements (Updated)
- **FR-1**: Bypass all Gateway communication when `--standalone` is active.
- **FR-2**: Load tasks from local JSON/CSV.
- **FR-3**: Use `LocalPersistenceManager` for all results.
- **FR-4**: Log progress to local SQLite to support `--resume`.
